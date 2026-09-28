#!/usr/bin/env python3
"""Prepare, execute, assess, and remove explicitly authorized comparisons.

Only the run operation can load a model adapter. Importing this module and the
other operations are offline. Raw evidence belongs in an external run directory.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import secrets
import subprocess
import sys
import time
from typing import Any

if __package__:
    from evals.comparison_state import (
        StateError, capture_workspace, checked_path, cleanup_owned,
        compare_workspace, copy_tree, require_external, tree_identity,
    )
else:
    from comparison_state import (
        StateError, capture_workspace, checked_path, cleanup_owned,
        compare_workspace, copy_tree, require_external, tree_identity,
    )


VERSION = 1
ARMS = ("no-skill", "current-skill", "candidate-skill")
DIMENSIONS = ("activation", "outcome", "evidence", "authorization", "scope", "state")
VERDICTS = {"PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"}
CLAIM_STATES = {"supported", "bounded", "unresolved", "unsupported"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MATERIALIZERS = {
    slug: "materialize_fixtures.py" for slug in (
        "audit-data-exposure", "audit-dependencies", "comment-health",
        "deep-code-audit", "deep-planning", "diagnose-bugs", "docs-audit",
        "maui-blazor-browser", "prune-codebase", "reduce-code-slop",
        "ui-design-and-polish", "verification-context", "verify-change",
    )
}
MATERIALIZERS["chatgpt-research"] = "materialize_packets.py"


class ComparisonError(RuntimeError):
    """A safe diagnostic code, never raw child output or private input."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ComparisonError(code)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _fields(value: Any, required: set[str], optional: set[str] | None = None) -> None:
    _require(isinstance(value, dict), "record-shape")
    _require(required <= value.keys() <= required | (optional or set()), "record-fields")


def _relative(value: Any, *, directory: bool = False) -> str:
    _require(_text(value) and "\\" not in value, "relative-path")
    candidate = value[:-1] if directory and value.endswith("/") else value
    p = PurePosixPath(candidate)
    _require(
        bool(candidate) and candidate != "." and not p.is_absolute()
        and not PureWindowsPath(candidate).drive
        and all(part not in ("", ".", "..") for part in candidate.split("/"))
        and ":" not in candidate,
        "relative-path",
    )
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: Any) -> None:
    checked_path(path, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".new")
    checked_path(temporary, must_exist=False)
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read(path: Path) -> Any:
    checked_path(path)
    try:
        _require(path.stat().st_size <= 64 * 1024 * 1024, "record-size")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ComparisonError("record-read") from exc


def validate_spec(spec: dict) -> None:
    _fields(spec, {"schemaVersion", "suite", "candidatePackage", "cases", "settings",
                   "limits", "authorization"}, {"repetitions"})
    _require(type(spec["schemaVersion"]) is int and spec["schemaVersion"] == VERSION, "spec-version")
    _require(isinstance(spec["suite"], str) and bool(SLUG.fullmatch(spec["suite"])), "suite-id")
    _require(_text(spec["candidatePackage"]) and Path(spec["candidatePackage"]).is_absolute(),
             "candidate-path")
    _require(_text(spec["authorization"]), "authorization-required")
    repeats = spec.get("repetitions", 1)
    _require(type(repeats) is int and repeats > 0, "repetitions")
    settings = spec["settings"]
    _fields(settings, {"executable", "model", "reasoningEffort", "sandbox", "approvalPolicy",
                       "ambientSkills", "config", "contextManagement"})
    _require(all(_text(settings[k]) for k in ("executable", "model", "reasoningEffort")),
             "model-settings")
    _require(settings["sandbox"] in ("workspace-write", "read-only")
             and settings["approvalPolicy"] == "never", "permissions")
    _require(isinstance(settings["ambientSkills"], list)
             and isinstance(settings["config"], dict)
             and isinstance(settings["contextManagement"], dict), "context-settings")
    _require(all(_text(key) for mapping in (settings["config"], settings["contextManagement"])
                 for key in mapping), "context-settings")
    for skill in settings["ambientSkills"]:
        _fields(skill, {"path", "name", "sha256"})
        _require(all(_text(skill[k]) for k in skill), "ambient-skill")
        _require(Path(skill["path"]).is_absolute()
                 and bool(re.fullmatch(r"[0-9a-f]{64}", skill["sha256"])), "ambient-skill")
    limits = spec["limits"]
    _fields(limits, {"maxTrials", "trialTimeoutSeconds", "batchTimeoutSeconds"})
    _require(type(limits["maxTrials"]) is int and limits["maxTrials"] > 0
             and _number(limits["trialTimeoutSeconds"])
             and _number(limits["batchTimeoutSeconds"]), "finite-limits")
    _require(isinstance(spec["cases"], list) and bool(spec["cases"]), "case-selection")
    ids = []
    for case in spec["cases"]:
        _fields(case, {"id", "heldOut", "setup", "allowedPaths"},
                {"promptOverride", "verification"})
        _require(isinstance(case["id"], str) and bool(SLUG.fullmatch(case["id"])), "case-id")
        _require(type(case["heldOut"]) is bool, "held-out")
        ids.append(case["id"])
        _require(isinstance(case["allowedPaths"], list), "allowed-paths")
        _require(len(case["allowedPaths"]) == len(set(case["allowedPaths"])), "allowed-paths")
        for path in case["allowedPaths"]:
            _relative(path, directory=True)
            _require(path.split("/")[0] not in (".git", ".agents"), "reserved-path")
        setup = case["setup"]
        _fields(setup, {"kind", "reviewed"}, {"path"})
        _require(setup["reviewed"] is True and setup["kind"] in ("materializer", "seed"),
                 "setup-review")
        if setup["kind"] == "seed":
            _require(_text(setup.get("path")) and Path(setup["path"]).is_absolute(), "seed-path")
        else:
            _require("path" not in setup, "setup-fields")
        if "promptOverride" in case:
            override = case["promptOverride"]
            _fields(override, {"text", "reason"})
            _require(all(_text(v) for v in override.values()) and "$" not in override["text"],
                     "prompt-override")
        _require(isinstance(case.get("verification", []), list), "verification-shape")
        for check in case.get("verification", []):
            _fields(check, {"phase", "argv", "reason", "timeoutSeconds", "expectedExitCodes"})
            _require(check["phase"] in ("before", "after") and _text(check["reason"])
                     and _number(check["timeoutSeconds"]), "verification-review")
            argv = check["argv"]
            _require(isinstance(argv, list) and argv and all(_text(x) for x in argv)
                     and argv[0] in ("python", "python3", "py", "dotnet"), "verification-argv")
            _require(isinstance(check["expectedExitCodes"], list) and check["expectedExitCodes"]
                     and all(type(x) is int for x in check["expectedExitCodes"]), "verification-exits")
    _require(len(ids) == len(set(ids)), "duplicate-case")
    _require(any(c["heldOut"] for c in spec["cases"]), "held-out-required")
    _require(len(ids) * repeats * len(ARMS) <= limits["maxTrials"], "trial-budget")


def _materialize(source: Path, suite: str, case_id: str, output: Path) -> Path:
    _require(suite in MATERIALIZERS, "setup-unsupported-use-seed")
    script = checked_path(source / "evals" / suite / MATERIALIZERS[suite])
    try:
        child = subprocess.run([sys.executable, "-B", str(script), "--case", case_id,
                                "--output", str(output)], cwd=source,
                               capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ComparisonError("materialization-blocked") from exc
    _require(child.returncode == 0, "materialization-failed")
    return checked_path(output / case_id)


def prepare_comparison(spec: dict, source: Path, output: Path) -> dict:
    """Freeze reviewed inputs and copy each seed; never instantiate an adapter."""
    validate_spec(spec)
    source = checked_path(source)
    output = require_external(output, source)
    candidate = checked_path(Path(spec["candidatePackage"]))
    _require(not candidate.is_relative_to(output) and not output.is_relative_to(candidate),
             "candidate-output-overlap")
    suite = spec["suite"]
    manifest_path = checked_path(source / "evals" / suite / "cases.json")
    manifest = _read(manifest_path)
    _require(manifest.get("schemaVersion") == 1 and isinstance(manifest.get("cases"), list)
             and isinstance(manifest.get("suiteExpectations"), dict), "manifest-shape")
    index = {c["id"]: c for c in manifest["cases"]}
    selected = []
    for selection in spec["cases"]:
        case_id = selection["id"]
        _require(case_id in index, "behavioral-case-required-routing-and-live-unsupported")
        case = index[case_id]
        prompt = selection.get("promptOverride", {}).get("text", case.get("prompt"))
        _require(_text(prompt), "case-prompt")
        _require(not re.search(r"\$[a-z][a-z0-9-]*", prompt), "task-only-prompt-required")
        _require(isinstance(case.get("expected"), dict), "case-expectations")
        selected.append((selection, case, prompt))
    current = checked_path(source / "skills" / suite)
    for package in (current, candidate):
        _require((package / "SKILL.md").is_file(), "skill-package")
        tree_identity(package)
    token = secrets.token_hex(24)
    output.mkdir(parents=True, exist_ok=True)
    _write(output / ".comparison-owner.json", {
        "schemaVersion": VERSION, "token": token, "root": str(output), "source": str(source),
    })
    # Preserve failed preparation for explicit, ownership-checked cleanup.
    _write(output / "preparation.json", {"schemaVersion": VERSION, "status": "preparing"})
    inputs = output / "inputs"
    inputs.mkdir()
    copy_tree(current, inputs / "current")
    copy_tree(candidate, inputs / "candidate")
    _write(inputs / "spec.json", spec)
    _write(inputs / "manifest.json", manifest)
    _write(inputs / "source-state.json", capture_workspace(source))
    trials = []
    for selection, case, prompt in selected:
        case_id = case["id"]
        if selection["setup"]["kind"] == "materializer":
            seed = _materialize(source, suite, case_id, inputs / "seeds" / case_id)
        else:
            seed = inputs / "seeds" / case_id
            original = checked_path(Path(selection["setup"]["path"]))
            _require(not original.is_relative_to(output) and not output.is_relative_to(original),
                     "seed-output-overlap")
            copy_tree(original, seed)
        _require(not (seed / ".agents" / "skills").exists(), "skill-overlay-collision")
        identity = tree_identity(seed)
        for repeat in range(spec.get("repetitions", 1)):
            for arm in ARMS:
                trial_id = f"t{len(trials) + 1:06d}"
                work = output / "trials" / trial_id / "workspace"
                copy_tree(seed, work)
                package_path = None
                if arm != "no-skill":
                    package_path = work / ".agents" / "skills" / suite
                    copy_tree(inputs / ("current" if arm == "current-skill" else "candidate"),
                              package_path)
                trials.append({
                    "id": trial_id, "caseId": case_id, "arm": arm, "repetition": repeat + 1,
                    "heldOut": selection["heldOut"], "fixtureIdentity": _digest(identity),
                    "workspace": work.relative_to(output).as_posix(),
                    "package": package_path.relative_to(output).as_posix() if package_path else None,
                    "initialState": capture_workspace(work), "prompt": prompt,
                    "originalPrompt": case["prompt"], "promptOverride": selection.get("promptOverride"),
                    "expectations": {"suite": manifest["suiteExpectations"], "case": case["expected"]},
                    "skillName": suite, "settings": deepcopy(spec["settings"]),
                    "authorization": spec["authorization"], "allowedPaths": selection["allowedPaths"],
                    "verification": selection.get("verification", []),
                })
    bundle = {"schemaVersion": VERSION, "source": str(source), "root": str(output),
              "createdAt": time.time(), "trials": trials, "limits": spec["limits"],
              "inputIdentity": tree_identity(inputs)}
    _write(output / "comparison.json", bundle)
    _write(output / "preparation.json", {"schemaVersion": VERSION, "status": "prepared",
                                        "comparisonDigest": _digest(bundle)})
    _write(output / "execution.json", {"schemaVersion": VERSION, "adapter": None,
                                      "simulated": None, "startedAt": None, "attempted": [],
                                      "recordDigests": {}})
    return {"root": str(output), "cleanupToken": token, "trialCount": len(trials)}


def load_comparison(root: Path) -> dict:
    root = checked_path(root)
    owner = _read(root / ".comparison-owner.json")
    _require(owner.get("schemaVersion") == VERSION and owner.get("root") == str(root), "run-owner")
    bundle = _read(root / "comparison.json")
    preparation = _read(root / "preparation.json")
    _require(bundle.get("schemaVersion") == VERSION and bundle.get("root") == str(root)
             and bundle.get("source") == owner.get("source")
             and preparation.get("status") == "prepared"
             and preparation.get("comparisonDigest") == _digest(bundle), "frozen-record-changed")
    _require(tree_identity(root / "inputs") == bundle["inputIdentity"], "frozen-inputs-changed")
    for trial in bundle["trials"]:
        _relative(trial["workspace"])
        if trial["package"]:
            _relative(trial["package"])
    return bundle


def derive_case_result(dimensions: dict[str, str], *, started: bool = True) -> str:
    _require(set(dimensions) == set(DIMENSIONS) and all(v in VERDICTS for v in dimensions.values()),
             "dimension-verdicts")
    _require(dimensions["activation"] == "NOT_APPLICABLE", "execution-activation")
    if not started:
        return "NOT_RUN"
    applicable = [v for v in dimensions.values() if v != "NOT_APPLICABLE"]
    _require(bool(applicable), "no-applicable-dimension")
    return "FAIL" if "FAIL" in applicable else "BLOCKED" if "BLOCKED" in applicable else "PASS"


def _native_checks(trial: dict, workspace: Path, evidence: Path, phase: str,
                   remaining: float) -> list[dict]:
    records = []
    for index, check in enumerate(trial["verification"]):
        if check["phase"] != phase:
            continue
        start = time.monotonic()
        if remaining <= 0:
            records.append({"index": index, "status": "blocked", "cleanupConfirmed": True})
            break
        try:
            if __package__:
                from evals.comparison_codex import capture_local_check
            else:
                from comparison_codex import capture_local_check
            stem = f"check-{phase}-{index}"
            for suffix in (".stdout", ".stderr"):
                checked_path(evidence / (stem + suffix), must_exist=False)
            child = capture_local_check(check["argv"], workspace, evidence / stem,
                                        min(remaining, check["timeoutSeconds"]))
            finished = child["status"] in ("completed", "failed") and type(child["exitCode"]) is int
            status = ("pass" if child["exitCode"] in check["expectedExitCodes"] else "fail") if finished else "blocked"
            records.append({"index": index, "exitCode": child["exitCode"], "status": status,
                            "cleanupConfirmed": child["cleanupConfirmed"]})
        except OSError:
            records.append({"index": index, "status": "blocked", "cleanupConfirmed": True})
        remaining -= time.monotonic() - start
    return records


def run_comparison(root: Path, *, allow_model_execution: bool = False,
                   adapter: Any = None, clock=time.time) -> dict:
    """Run pending trials. Tests inject a simulated adapter; the CLI cannot."""
    root = checked_path(root)
    bundle = load_comparison(root)
    simulated = adapter is not None and getattr(adapter, "simulated", False) is True
    if not simulated:
        _require(allow_model_execution and not os.environ.get("P537_OFFLINE_CHECKS_ACTIVE"),
                 "model-execution-not-authorized")
        if adapter is None:
            if __package__:
                from evals.comparison_codex import CodexAdapter
            else:
                from comparison_codex import CodexAdapter
            adapter = CodexAdapter()
    _require(_text(getattr(adapter, "name", None)), "adapter-identity")
    execution = _read(root / "execution.json")
    _require(execution.get("schemaVersion") == VERSION
             and isinstance(execution.get("attempted"), list)
             and isinstance(execution.get("recordDigests"), dict)
             and len(execution["attempted"]) == len(set(execution["attempted"]))
             and set(execution["attempted"]) <= {t["id"] for t in bundle["trials"]}, "execution-version")
    _require(execution["adapter"] in (None, adapter.name)
             and execution["simulated"] in (None, simulated), "adapter-changed")
    if execution["startedAt"] is None:
        execution.update(adapter=adapter.name, simulated=simulated, startedAt=clock())
        _write(root / "execution.json", execution)
    deadline = execution["startedAt"] + bundle["limits"]["batchTimeoutSeconds"]
    source = checked_path(Path(bundle["source"]))
    source_before = capture_workspace(source)
    frozen_spec = _read(root / "inputs" / "spec.json")
    external_paths = [Path(frozen_spec["candidatePackage"])]
    external_paths += [Path(skill["path"]) for skill in frozen_spec["settings"]["ambientSkills"]]
    external_before = {str(path): tree_identity(path.parent if path.name == "SKILL.md" else path)
                       for path in external_paths}
    for trial in bundle["trials"]:
        record_path = root / "trials" / trial["id"] / "record.json"
        if trial["id"] in execution["attempted"]:
            _require(record_path.is_file(), "interrupted-record-missing")
            previous = _read(record_path)
            _require(execution["recordDigests"].get(trial["id"]) == _digest(previous),
                     "prior-record-changed")
            _require(previous.get("status") != "running", "interrupted-trial-requires-review")
            _require(previous.get("cleanupConfirmed") is True and not previous.get("stateFailures"),
                     "prior-trial-invalid-new-bundle-required")
            _require(previous.get("evidenceIdentity") == tree_identity(record_path.parent / "evidence")
                     and "after" in previous and not compare_workspace(previous["after"],
                         capture_workspace(root / trial["workspace"]), []), "prior-evidence-changed")
            continue
        if clock() >= deadline:
            break
        _require(len(execution["attempted"]) < bundle["limits"]["maxTrials"], "trial-budget")
        workspace = checked_path(root / trial["workspace"])
        package = checked_path(root / trial["package"]) if trial["package"] else None
        _require(not compare_workspace(trial["initialState"], capture_workspace(workspace), []),
                 "pending-workspace-changed")
        evidence = root / "trials" / trial["id"] / "evidence"
        evidence.mkdir(exist_ok=False)
        copy_tree(workspace, evidence / "before")
        started_at = clock()
        record = {"schemaVersion": VERSION, "trialId": trial["id"], "status": "running",
                  "started": False, "simulated": simulated, "cleanupConfirmed": False,
                  "startedAt": started_at, "before": capture_workspace(workspace)}
        _write(record_path, record)
        execution["attempted"].append(trial["id"])
        _write(root / "execution.json", execution)
        trial_deadline = min(deadline, started_at + bundle["limits"]["trialTimeoutSeconds"])
        native = []
        host_configuration_changed = False
        try:
            preflight = adapter.preflight(trial, workspace, package, evidence,
                                          max(0, trial_deadline - clock()))
            host_configuration_changed = isinstance(preflight, dict) and preflight.get("userConfigUnchanged") is False
            _write(evidence / "preflight.json", preflight)
            if not isinstance(preflight, dict) or preflight.get("ok") is not True or host_configuration_changed:
                record.update(status="blocked", reason="adapter-preflight", cleanupConfirmed=(
                    isinstance(preflight, dict) and preflight.get("cleanupConfirmed", True) is True))
            elif not simulated and not preflight.get("comparisonIdentity"):
                record.update(status="blocked", reason="environment-identity-unavailable", cleanupConfirmed=True)
            elif (execution.get("comparisonIdentity") is not None and preflight.get("comparisonIdentity")
                  != execution["comparisonIdentity"]):
                record.update(status="blocked", reason="environment-changed", cleanupConfirmed=True)
            elif trial_deadline <= clock():
                record.update(status="blocked", reason="trial-deadline", cleanupConfirmed=True)
            else:
                if preflight.get("comparisonIdentity") is not None:
                    execution["comparisonIdentity"] = preflight["comparisonIdentity"]
                    _write(root / "execution.json", execution)
                native = _native_checks(trial, workspace, evidence, "before", trial_deadline - clock())
                if any(c["status"] != "pass" for c in native):
                    record.update(status="blocked", reason="before-check", cleanupConfirmed=all(
                        c["cleanupConfirmed"] for c in native))
                elif trial_deadline <= clock():
                    record.update(status="blocked", reason="trial-deadline", cleanupConfirmed=True)
                else:
                    # Once dispatched, an interrupted transport cannot prove that no trial started.
                    record["started"] = True
                    _write(record_path, record)
                    result = adapter.execute(trial, workspace, package, evidence, trial_deadline - clock())
                    _require(isinstance(result, dict) and result.get("status") in (
                        "completed", "blocked", "failed", "timeout", "interrupted")
                        and type(result.get("started")) is bool
                        and type(result.get("cleanupConfirmed")) is bool, "adapter-result")
                    _write(evidence / "adapter-result.json", result)
                    host_configuration_changed = result.get("userConfigUnchanged") is False
                    record.update({k: result[k] for k in ("status", "started", "cleanupConfirmed")})
                    record["metrics"] = result.get("metrics", {})
                    record["exitCode"] = result.get("exitCode")
                    if record["status"] == "completed":
                        native += _native_checks(trial, workspace, evidence, "after",
                                                 trial_deadline - clock())
        except KeyboardInterrupt:
            record.update(status="interrupted", reason="interrupted", cleanupConfirmed=False)
        except Exception:
            record.update(status="blocked", reason="adapter-error", cleanupConfirmed=False)
        finally:
            record["nativeChecks"] = native
            record["elapsedSeconds"] = max(0, clock() - started_at)
            record["cleanupConfirmed"] = record["cleanupConfirmed"] and all(
                c["cleanupConfirmed"] for c in native)
            try:
                record["after"] = capture_workspace(workspace)
                record["stateFailures"] = compare_workspace(record["before"], record["after"],
                                                             trial["allowedPaths"])
                if host_configuration_changed:
                    record["stateFailures"].append("host-configuration-changed")
                copy_tree(workspace, evidence / "after")
                if tree_identity(root / "inputs") != bundle["inputIdentity"]:
                    record["stateFailures"].append("frozen-inputs-changed")
                if compare_workspace(source_before, capture_workspace(source), []):
                    record["stateFailures"].append("source-repository-changed")
                for path in external_paths:
                    if tree_identity(path.parent if path.name == "SKILL.md" else path) != external_before[str(path)]:
                        record["stateFailures"].append("external-package-changed")
                record["evidenceIdentity"] = tree_identity(evidence)
            except (StateError, ComparisonError, OSError):
                record.update(status="blocked", reason="state-unavailable", cleanupConfirmed=False)
            _write(record_path, record)
            execution["recordDigests"][trial["id"]] = _digest(record)
            _write(root / "execution.json", execution)
        if not record["cleanupConfirmed"] or record.get("stateFailures"):
            break
    return {"schemaVersion": VERSION, "attempted": len(execution["attempted"]),
            "total": len(bundle["trials"]), "simulated": simulated,
            "executionComplete": len(execution["attempted"]) == len(bundle["trials"])
            and all(_read(root / "trials" / t["id"] / "record.json").get("status") == "completed"
                    for t in bundle["trials"])}


def _evidence_reference(value: Any, evidence: Path) -> None:
    _relative(value)
    target = checked_path(evidence / value)
    _require(target.is_file(), "review-evidence")


def validate_review(review: dict, trial_id: str, evidence: Path, simulated: bool) -> None:
    _fields(review, {"trialId", "reviewer", "dimensions", "claims", "contaminated"},
            {"annotations"})
    _require(review["trialId"] == trial_id and type(review["contaminated"]) is bool, "review-trial")
    _fields(review["reviewer"], {"kind", "id"})
    _require(review["reviewer"]["kind"] == ("simulated" if simulated else "human")
             and _text(review["reviewer"]["id"]), "human-review-required")
    _require(isinstance(review["dimensions"], dict)
             and set(review["dimensions"]) == set(DIMENSIONS), "review-dimensions")
    for dimension, decision in review["dimensions"].items():
        _fields(decision, {"verdict", "reason", "evidence"})
        _require(decision["verdict"] in VERDICTS and _text(decision["reason"])
                 and isinstance(decision["evidence"], list), "review-decision")
        if decision["verdict"] in ("PASS", "FAIL"):
            _require(bool(decision["evidence"]), "review-evidence-required")
        for reference in decision["evidence"]:
            _evidence_reference(reference, evidence)
        _require(dimension != "activation" or decision["verdict"] == "NOT_APPLICABLE",
                 "execution-activation")
    _require(isinstance(review["claims"], list), "review-claims")
    for claim in review["claims"]:
        _fields(claim, {"state", "text", "evidence"})
        _require(claim["state"] in CLAIM_STATES and _text(claim["text"])
                 and isinstance(claim["evidence"], list), "claim-state")
        if claim["state"] in ("supported", "bounded"):
            _require(bool(claim["evidence"]), "claim-evidence-required")
        for reference in claim["evidence"]:
            _evidence_reference(reference, evidence)
    if "annotations" in review:
        _require(isinstance(review["annotations"], list), "review-annotations")
        for annotation in review["annotations"]:
            _fields(annotation, {"metric", "value", "reason", "evidence"})
            _require(annotation["metric"] in ("observedReads", "repeatedChecks", "approvalEvents")
                     and type(annotation["value"]) is int and annotation["value"] >= 0
                     and _text(annotation["reason"]) and isinstance(annotation["evidence"], list)
                     and bool(annotation["evidence"]), "review-annotation")
            for reference in annotation["evidence"]:
                _evidence_reference(reference, evidence)


def report_comparison(root: Path, reviews: dict | None = None) -> dict:
    """Assess records without launching validators or a model; return safe summary."""
    root = checked_path(root)
    bundle = load_comparison(root)
    execution = _read(root / "execution.json")
    _require(isinstance(execution.get("recordDigests"), dict)
             and isinstance(execution.get("attempted"), list), "execution-record")
    reviews = reviews or {"schemaVersion": VERSION, "reviews": []}
    _fields(reviews, {"schemaVersion", "reviews"})
    _require(reviews["schemaVersion"] == VERSION and isinstance(reviews["reviews"], list),
             "review-version")
    review_index = {}
    known_ids = {t["id"] for t in bundle["trials"]}
    for review in reviews["reviews"]:
        _require(isinstance(review, dict) and review.get("trialId") in known_ids
                 and review["trialId"] not in review_index, "review-identity")
        review_index[review["trialId"]] = review
    rows = []
    for trial in bundle["trials"]:
        record_path = root / "trials" / trial["id"] / "record.json"
        dimensions = {key: "BLOCKED" for key in DIMENSIONS}
        dimensions["activation"] = "NOT_APPLICABLE"
        row = {"trialId": trial["id"], "caseId": trial["caseId"], "arm": trial["arm"],
               "repetition": trial["repetition"], "heldOut": trial["heldOut"],
               "dimensions": dimensions, "result": "NOT_RUN", "validComparison": True,
               "metrics": {name: {"value": None, "source": "unavailable"} for name in (
                   "observedReads", "repeatedChecks", "approvalEvents", "inputTokens",
                   "cachedInputTokens", "outputTokens", "commandEvents", "repeatedCommandExecutions",
                   "elapsedSeconds", "monetaryCost")}}
        if not record_path.exists():
            _require(trial["id"] not in execution["attempted"]
                     and trial["id"] not in execution["recordDigests"], "execution-record-missing")
            _require(trial["id"] not in review_index, "review-without-trial")
            rows.append(row)
            continue
        record = _read(record_path)
        _require(execution["recordDigests"].get(trial["id"]) == _digest(record), "execution-record-changed")
        _require(record.get("schemaVersion") == VERSION and record.get("trialId") == trial["id"]
                 and type(record.get("started")) is bool and type(record.get("simulated")) is bool,
                 "execution-record")
        evidence = record_path.parent / "evidence"
        evidence_valid = record.get("evidenceIdentity") == tree_identity(evidence)
        workspace_valid = "after" in record and not compare_workspace(
            record["after"], capture_workspace(root / trial["workspace"]), [])
        review = review_index.get(trial["id"])
        if review:
            validate_review(review, trial["id"], evidence, record["simulated"])
            dimensions.update({key: value["verdict"] for key, value in review["dimensions"].items()})
            row["claimStates"] = [claim["state"] for claim in review["claims"]]
            if any(claim["state"] == "unsupported" for claim in review["claims"]):
                dimensions["evidence"] = "FAIL"
            if review["contaminated"]:
                row["validComparison"] = False
                dimensions["evidence"] = "FAIL"
            for annotation in review.get("annotations", []):
                row["metrics"][annotation["metric"]] = {
                    "value": annotation["value"], "source": "reviewed-evidence-annotation"}
        computed_failures = []
        if "before" in record and "after" in record:
            computed_failures = compare_workspace(record["before"], record["after"], trial["allowedPaths"])
            computed_failures += compare_workspace(trial["initialState"], record["before"], [])
        if record.get("stateFailures") or computed_failures:
            dimensions["state"] = "FAIL"
        if not record.get("cleanupConfirmed"):
            dimensions["state"] = "FAIL" if dimensions["state"] == "FAIL" else "BLOCKED"
        if not evidence_valid or not workspace_valid:
            dimensions["evidence"] = "FAIL"
            row["validComparison"] = False
        if record["status"] != "completed":
            if dimensions["outcome"] != "FAIL":
                dimensions["outcome"] = "BLOCKED"
        checks = record.get("nativeChecks", [])
        if any(c.get("status") == "fail" for c in checks):
            dimensions["outcome"] = "FAIL"
        elif any(c.get("status") == "blocked" for c in checks):
            if dimensions["outcome"] != "FAIL":
                dimensions["outcome"] = "BLOCKED"
        for name in ("commandEvents", "repeatedCommandExecutions", "inputTokens", "cachedInputTokens", "outputTokens"):
            value = record.get("metrics", {}).get(name)
            if type(value) is int and value >= 0:
                row["metrics"][name] = {"value": value, "source": "adapter-telemetry"}
        elapsed = record.get("elapsedSeconds")
        if type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0:
            row["metrics"]["elapsedSeconds"] = {"value": elapsed, "source": "runner-clock"}
        row.update(executionStatus=record["status"], simulated=record["simulated"],
                   result=derive_case_result(dimensions, started=record["started"]))
        rows.append(row)
    comparisons = []
    for trial in bundle["trials"]:
        if trial["arm"] != "current-skill":
            continue
        group = {row["arm"]: row for row in rows if row["caseId"] == trial["caseId"]
                 and row["repetition"] == trial["repetition"]}
        current, candidate = group["current-skill"], group["candidate-skill"]
        comparisons.append({"caseId": trial["caseId"], "repetition": trial["repetition"],
                            "validComparison": all(row["validComparison"] and row["result"] != "NOT_RUN"
                                                   for row in group.values()),
                            "assessmentComplete": all(row["result"] not in ("BLOCKED", "NOT_RUN")
                                                      for row in group.values()),
                            "dimensionChanges": {key: [current["dimensions"][key], candidate["dimensions"][key]]
                                                 for key in DIMENSIONS
                                                 if current["dimensions"][key] != candidate["dimensions"][key]},
                            "outcomes": {arm: row["result"] for arm, row in group.items()}})
    return {"schemaVersion": VERSION, "trials": rows, "comparisons": comparisons,
            "boundary": "No aggregate score. Simulated evidence does not establish model behavior."}


def cleanup_comparison(root: Path, token: str) -> None:
    root = checked_path(root)
    owner = _read(root / ".comparison-owner.json")
    ledger_path = root / "execution.json"
    ledger = _read(ledger_path) if ledger_path.exists() else {"attempted": [], "recordDigests": {}}
    _require(isinstance(ledger.get("attempted"), list)
             and isinstance(ledger.get("recordDigests"), dict), "execution-record")
    for trial_id in ledger["attempted"]:
        _require(isinstance(trial_id, str) and bool(re.fullmatch(r"t[0-9]{6,}", trial_id))
                 and (root / "trials" / trial_id / "record.json").is_file(), "cleanup-record-missing")
    # Never trust a PID in editable evidence as authority to kill a process.
    for record_path in root.glob("trials/*/record.json"):
        record = _read(record_path)
        _require(record_path.parent.name in ledger["attempted"]
                 and ledger["recordDigests"].get(record_path.parent.name) == _digest(record),
                 "cleanup-record-changed")
        _require(record.get("status") != "running" and record.get("cleanupConfirmed") is True,
                 "process-cleanup-unconfirmed")
    cleanup_owned(root, token, Path(owner["source"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    prepare = sub.add_parser("prepare", help="Freeze reviewed inputs without model execution")
    prepare.add_argument("--spec", type=Path, required=True)
    prepare.add_argument("--source", type=Path, default=Path(__file__).resolve().parent.parent)
    prepare.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("run", help="Explicitly authorized Codex execution only")
    run.add_argument("--run-dir", type=Path, required=True)
    run.add_argument("--allow-model-execution", action="store_true")
    report = sub.add_parser("report", help="Assess evidence and human reviews offline")
    report.add_argument("--run-dir", type=Path, required=True)
    report.add_argument("--reviews", type=Path)
    cleanup = sub.add_parser("cleanup", help="Remove only an owned external run after review")
    cleanup.add_argument("--run-dir", type=Path, required=True)
    cleanup.add_argument("--token", required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "prepare":
            result = prepare_comparison(_read(args.spec), args.source, args.output)
            print(json.dumps({"status": "PREPARED", "cleanupToken": result["cleanupToken"],
                              "trialCount": result["trialCount"]}))
        elif args.operation == "run":
            result = run_comparison(args.run_dir, allow_model_execution=args.allow_model_execution)
            print(json.dumps(result))
            return 0 if result["executionComplete"] else 2
        elif args.operation == "report":
            result = report_comparison(args.run_dir, _read(args.reviews) if args.reviews else None)
            print(json.dumps(result, indent=2))
            return 1 if any(r["result"] == "FAIL" for r in result["trials"]) else (
                2 if any(r["result"] != "PASS" for r in result["trials"]) else 0)
        else:
            cleanup_comparison(args.run_dir, args.token)
            print("CLEANED: owned comparison removed")
        return 0
    except (ComparisonError, StateError) as exc:
        print(f"BLOCKED: {exc.code}. See the comparison workflow guide; no private input is printed.", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError):
        print("BLOCKED: comparison infrastructure unavailable", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
