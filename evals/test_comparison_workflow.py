"""Offline integration tests; simulated adapters never launch a model.

All workspaces, evidence, and comparison records live under owned temporary
directories. The docs smoke exercises infrastructure, not skill effectiveness.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals import run_comparisons as workflow
from evals.comparison_state import StateError, capture_workspace, tree_identity


REPOSITORY = Path(__file__).resolve().parent.parent


class SimulatedAdapter:
    """A test double with observable callbacks and no subprocess capability."""

    name = "simulated-offline"
    simulated = True

    def __init__(self, action=None, *, preflight=None, result=None):
        self.action = action
        self.preflight_action = preflight
        self.result = result
        self.preflights = []
        self.executions = []

    def preflight(self, trial, workspace, package, evidence, remaining):
        self.preflights.append(trial["id"])
        if self.preflight_action:
            return self.preflight_action(trial, workspace, package, evidence, remaining)
        return {"ok": True, "simulated": True}

    def execute(self, trial, workspace, package, evidence, remaining):
        self.executions.append(trial["id"])
        if self.action:
            self.action(trial, workspace, package, evidence)
        (evidence / "response.txt").write_text(
            "Simulated task result; no model ran.\n", encoding="utf-8"
        )
        if self.result is not None:
            return deepcopy(self.result)
        return {
            "started": True,
            "status": "completed",
            "cleanupConfirmed": True,
            "exitCode": 0,
            "metrics": {"inputTokens": 11, "outputTokens": 7, "commandEvents": 2},
        }


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def settings():
    return {
        "executable": "forbidden-model-launch-canary",
        "model": "simulated-model",
        "reasoningEffort": "simulated",
        "sandbox": "workspace-write",
        "approvalPolicy": "never",
        "ambientSkills": [],
        "config": {},
        "contextManagement": {"mode": "fresh-context"},
    }


def reviews_for(bundle):
    return {
        "schemaVersion": 1,
        "reviews": [
            {
                "trialId": trial["id"],
                "reviewer": {"kind": "simulated", "id": "offline-test-reviewer"},
                "dimensions": {
                    dimension: {
                        "verdict": "NOT_APPLICABLE" if dimension == "activation" else "PASS",
                        "reason": "Simulated control expectation.",
                        "evidence": [] if dimension == "activation" else ["response.txt"],
                    }
                    for dimension in workflow.DIMENSIONS
                },
                "claims": [
                    {
                        "state": "bounded",
                        "text": "The simulated adapter completed the fixture operation.",
                        "evidence": ["response.txt"],
                    }
                ],
                "contaminated": False,
            }
            for trial in bundle["trials"]
        ],
    }


class ComparisonWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p537 comparison workflow ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source checkout"
        self.source.mkdir()
        self.current = self.source / "skills" / "alpha"
        self.current.mkdir(parents=True)
        (self.current / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: Synthetic bounded test.\n---\n\nCurrent instructions.\n",
            encoding="utf-8",
        )
        self.candidate = self.root / "candidate package"
        shutil.copytree(self.current, self.candidate)
        self.seed = self.root / "seed with spaces"
        self.seed.mkdir()
        (self.seed / "README.md").write_text("Original task content.\n", encoding="utf-8")
        (self.seed / "unrelated.txt").write_text("User work.\n", encoding="utf-8")
        (self.seed / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        (self.seed / "ignored").mkdir()
        (self.seed / "ignored" / "data.txt").write_text("Preserved ignored work.\n", encoding="utf-8")
        self.manifest = {
            "schemaVersion": 1,
            "suite": "alpha",
            "suiteExpectations": {"requiredSignals": ["evidence"], "prohibitedSignals": [],
                                  "repositoryState": "preserved"},
            "cases": [{"id": "controlled-case", "prompt": "Use $alpha to inspect this document.",
                       "expected": {"requiredSignals": ["bounded outcome"], "prohibitedSignals": [],
                                    "repositoryState": "unchanged"}}],
            "triggerCases": [{"id": "routing-only", "prompt": "Review the document."}],
            "liveCases": [{"id": "live-only", "prompt": "Contact a service."}],
        }
        write_json(self.source / "evals" / "alpha" / "cases.json", self.manifest)
        self.spec = {
            "schemaVersion": 1,
            "suite": "alpha",
            "candidatePackage": str(self.candidate),
            "cases": [{
                "id": "controlled-case", "heldOut": True,
                "setup": {"kind": "seed", "path": str(self.seed), "reviewed": True},
                "allowedPaths": [],
                "promptOverride": {"text": "Inspect this document and report your findings.",
                                   "reason": "Same task without an evaluated-skill invocation."},
            }],
            "settings": settings(),
            "limits": {"maxTrials": 3, "trialTimeoutSeconds": 30, "batchTimeoutSeconds": 90},
            "authorization": "Offline simulated infrastructure test only.",
        }
        self.output = self.root / "private run bundle"

    def prepare(self):
        self.prepared = workflow.prepare_comparison(self.spec, self.source, self.output)
        return workflow.load_comparison(self.output)

    def run_simulated(self, adapter=None):
        adapter = adapter or SimulatedAdapter()
        workflow.run_comparison(self.output, adapter=adapter)
        return adapter

    def assert_code(self, expected, callable_, *args, **kwargs):
        with self.assertRaises(workflow.ComparisonError) as error:
            callable_(*args, **kwargs)
        self.assertEqual(error.exception.code, expected)

    def test_preparation_freezes_equal_seeds_and_distinct_packages_without_execution(self):
        (self.candidate / "SKILL.md").write_text("Candidate-only instructions.\n", encoding="utf-8")
        original_source = tree_identity(self.source)
        original_seed = tree_identity(self.seed)
        model_module = types.ModuleType("evals.comparison_codex")
        model_module.CodexAdapter = mock.Mock(side_effect=AssertionError("model launch canary"))
        with mock.patch.dict(sys.modules, {"evals.comparison_codex": model_module}):
            bundle = self.prepare()
            report = workflow.report_comparison(self.output)
            self.assert_code("model-execution-not-authorized", workflow.run_comparison, self.output)
        model_module.CodexAdapter.assert_not_called()
        self.assertEqual(tree_identity(self.source), original_source)
        self.assertEqual(tree_identity(self.seed), original_seed)
        self.assertEqual({row["result"] for row in report["trials"]}, {"NOT_RUN"})
        self.assertEqual(len({trial["fixtureIdentity"] for trial in bundle["trials"]}), 1)
        self.assertEqual({trial["prompt"] for trial in bundle["trials"]},
                         {self.spec["cases"][0]["promptOverride"]["text"]})
        for trial in bundle["trials"]:
            work = self.output / trial["workspace"]
            self.assertEqual((work / "README.md").read_bytes(), (self.seed / "README.md").read_bytes())
            self.assertEqual((work / "ignored" / "data.txt").read_bytes(),
                             (self.seed / "ignored" / "data.txt").read_bytes())
            self.assertNotIn("expectations", " ".join(p.name for p in work.iterdir()))
            self.assertNotIn(trial["arm"], str(work))
            self.assertTrue(trial["heldOut"])
            self.assertIn("$alpha", trial["originalPrompt"])
            if trial["arm"] == "no-skill":
                self.assertFalse((work / ".agents" / "skills").exists())
            else:
                expected = self.current if trial["arm"] == "current-skill" else self.candidate
                self.assertEqual(tree_identity(self.output / trial["package"]), tree_identity(expected))
        workflow.cleanup_comparison(self.output, self.prepared["cleanupToken"])
        self.assertFalse(self.output.exists())

    def test_completed_process_requires_review_and_resume_skips_completed_trials(self):
        bundle = self.prepare()
        adapter = self.run_simulated()
        before = tree_identity(self.output)
        missing = workflow.report_comparison(self.output)
        self.assertEqual({row["result"] for row in missing["trials"]}, {"BLOCKED"})
        report = workflow.report_comparison(self.output, reviews_for(bundle))
        self.assertEqual({row["result"] for row in report["trials"]}, {"PASS"})
        self.assertTrue(all(row["simulated"] for row in report["trials"]))
        self.assertEqual(tree_identity(self.output), before)
        workflow.run_comparison(self.output, adapter=adapter)
        self.assertEqual(len(adapter.executions), 3)
        self.assertEqual(tree_identity(self.output), before)

    def test_duplicate_cases_and_nonfinite_or_insufficient_budgets_are_rejected(self):
        for field, value, code in (("maxTrials", 2, "trial-budget"),
                                   ("maxTrials", True, "finite-limits"),
                                   ("trialTimeoutSeconds", float("inf"), "finite-limits"),
                                   ("batchTimeoutSeconds", 0, "finite-limits")):
            with self.subTest(field=field, value=value):
                spec = deepcopy(self.spec)
                spec["limits"][field] = value
                self.assert_code(code, workflow.validate_spec, spec)
        duplicate = deepcopy(self.spec)
        duplicate["cases"].append(deepcopy(duplicate["cases"][0]))
        self.assert_code("duplicate-case", workflow.validate_spec, duplicate)

    def test_routing_live_missing_overrides_and_unreviewed_setup_are_rejected(self):
        for case_id in ("routing-only", "live-only"):
            self.spec["cases"][0]["id"] = case_id
            self.assert_code("behavioral-case-required-routing-and-live-unsupported",
                             workflow.prepare_comparison, self.spec, self.source, self.output)
        self.spec["cases"][0]["id"] = "controlled-case"
        override = self.spec["cases"][0].pop("promptOverride")
        self.assert_code("task-only-prompt-required", workflow.prepare_comparison,
                         self.spec, self.source, self.output)
        self.spec["cases"][0]["promptOverride"] = override
        self.spec["cases"][0]["setup"]["reviewed"] = False
        self.assert_code("setup-review", workflow.validate_spec, self.spec)
        self.assertFalse(self.output.exists())

    def test_held_out_selection_and_scope_are_validated_before_preparation(self):
        self.spec["cases"][0]["heldOut"] = False
        self.assert_code("held-out-required", workflow.validate_spec, self.spec)
        self.spec["cases"][0]["heldOut"] = True
        for unsafe in ("../outside", "/absolute", "C:/absolute", ".git/config", ".agents/skills"):
            with self.subTest(path=unsafe):
                self.spec["cases"][0]["allowedPaths"] = [unsafe]
                with self.assertRaises(workflow.ComparisonError):
                    workflow.validate_spec(self.spec)

    def test_duplicate_unknown_and_malformed_reviews_are_rejected(self):
        bundle = self.prepare()
        self.run_simulated()
        review = reviews_for(bundle)
        variants = []
        duplicate = deepcopy(review)
        duplicate["reviews"].append(deepcopy(duplicate["reviews"][0]))
        variants.append((duplicate, "review-identity"))
        unknown = deepcopy(review)
        unknown["reviews"][0]["trialId"] = "unknown"
        variants.append((unknown, "review-identity"))
        malformed = deepcopy(review)
        malformed["reviews"][0]["dimensions"].pop("scope")
        variants.append((malformed, "review-dimensions"))
        unavailable = deepcopy(review)
        unavailable["reviews"][0]["dimensions"]["outcome"]["evidence"] = []
        variants.append((unavailable, "review-evidence-required"))
        mislabeled = deepcopy(review)
        mislabeled["reviews"][0]["reviewer"]["kind"] = "human"
        variants.append((mislabeled, "human-review-required"))
        for value, code in variants:
            with self.subTest(code=code):
                self.assert_code(code, workflow.report_comparison, self.output, value)

    def test_semantic_failure_unsupported_claim_and_contamination_override_success(self):
        bundle = self.prepare()
        self.run_simulated()
        review = reviews_for(bundle)
        review["reviews"][0]["dimensions"]["outcome"]["verdict"] = "FAIL"
        review["reviews"][1]["claims"][0]["state"] = "unsupported"
        review["reviews"][2]["contaminated"] = True
        report = workflow.report_comparison(self.output, review)
        self.assertEqual([row["result"] for row in report["trials"]], ["FAIL"] * 3)
        self.assertFalse(report["trials"][2]["validComparison"])
        self.assertEqual(report["trials"][1]["dimensions"]["evidence"], "FAIL")
        self.assertEqual(report["comparisons"][0]["dimensionChanges"], {})
        self.assertEqual(report["comparisons"][0]["outcomes"]["current-skill"], "FAIL")

    def test_metrics_keep_telemetry_annotations_and_unavailable_values_distinct(self):
        bundle = self.prepare()
        self.run_simulated()
        review = reviews_for(bundle)
        review["reviews"][0]["annotations"] = [{"metric": "observedReads", "value": 1,
            "reason": "Synthetic evidence explicitly records one read.", "evidence": ["response.txt"]}]
        report = workflow.report_comparison(self.output, review)
        metrics = report["trials"][0]["metrics"]
        self.assertEqual(metrics["inputTokens"], {"value": 11, "source": "adapter-telemetry"})
        self.assertEqual(metrics["observedReads"],
                         {"value": 1, "source": "reviewed-evidence-annotation"})
        for metric in ("cachedInputTokens", "monetaryCost", "repeatedChecks", "approvalEvents"):
            self.assertEqual(metrics[metric], {"value": None, "source": "unavailable"})
        self.assertEqual(metrics["elapsedSeconds"]["source"], "runner-clock")
        self.assertNotIn("score", report)

    def test_unauthorized_and_ignored_file_edits_fail_and_stop_remaining_trials(self):
        bundle = self.prepare()
        def mutate(_trial, workspace, _package, _evidence):
            (workspace / "ignored" / "data.txt").write_text("Changed.\n", encoding="utf-8")
        adapter = self.run_simulated(SimulatedAdapter(mutate))
        review = reviews_for(bundle)
        review["reviews"] = review["reviews"][:1]
        rows = workflow.report_comparison(self.output, review)["trials"]
        self.assertEqual(len(adapter.executions), 1)
        self.assertEqual(rows[0]["dimensions"]["state"], "FAIL")
        self.assertEqual([row["result"] for row in rows], ["FAIL", "NOT_RUN", "NOT_RUN"])
        self.assert_code("prior-trial-invalid-new-bundle-required", workflow.run_comparison,
                         self.output, adapter=adapter)
        self.assertEqual(len(adapter.executions), 1)

    def test_staging_changes_fail_despite_authorized_readme_edits(self):
        environment = {key: value for key, value in os.environ.items()
                       if not key.upper().startswith("GIT_")}
        environment.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                            "GIT_AUTHOR_NAME": "Comparison Fixture",
                            "GIT_COMMITTER_NAME": "Comparison Fixture",
                            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                            "GIT_COMMITTER_EMAIL": "fixture@example.invalid"})
        def git(root, *arguments):
            result = subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull,
                                     "-c", "commit.gpgsign=false", *arguments],
                                    cwd=root, env=environment, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, "Synthetic Git setup or staging failed.")
        git(self.seed, "init", "--quiet", "--template=")
        git(self.seed, "add", "--all")
        git(self.seed, "commit", "--quiet", "-m", "Synthetic initial state")
        (self.seed / "README.md").write_text("Pre-existing staged work.\n", encoding="utf-8")
        git(self.seed, "add", "--", "README.md")
        (self.seed / "unrelated.txt").write_text("Pre-existing unstaged work.\n", encoding="utf-8")
        seed_before = capture_workspace(self.seed)
        self.spec["cases"][0]["allowedPaths"] = ["README.md"]
        bundle = self.prepare()
        def stage(_trial, workspace, _package, _evidence):
            (workspace / "README.md").write_text("Authorized content edit.\n", encoding="utf-8")
            git(workspace, "add", "--", "README.md")
        self.run_simulated(SimulatedAdapter(stage))
        record = read_json(self.output / "trials" / bundle["trials"][0]["id"] / "record.json")
        self.assertIn("git-staged-change", record["stateFailures"])
        self.assertEqual(capture_workspace(self.seed), seed_before)
        review = reviews_for(bundle)
        review["reviews"] = review["reviews"][:1]
        self.assertEqual(workflow.report_comparison(self.output, review)["trials"][0]["result"], "FAIL")

    def test_source_mutation_during_execution_is_detected(self):
        bundle = self.prepare()
        def mutate(_trial, _workspace, _package, _evidence):
            (self.current / "SKILL.md").write_text("Unauthorized source change.\n", encoding="utf-8")
        self.run_simulated(SimulatedAdapter(mutate))
        record = read_json(self.output / "trials" / bundle["trials"][0]["id"] / "record.json")
        self.assertIn("source-repository-changed", record["stateFailures"])
        review = reviews_for(bundle)
        review["reviews"] = review["reviews"][:1]
        self.assertEqual(workflow.report_comparison(self.output, review)["trials"][0]["result"], "FAIL")

    def test_package_overlay_mutation_fails_the_preservation_dimension(self):
        bundle = self.prepare()
        def mutate(_trial, _workspace, package, _evidence):
            if package:
                (package / "SKILL.md").write_text("Unauthorized overlay change.\n", encoding="utf-8")
        self.run_simulated(SimulatedAdapter(mutate))
        review = reviews_for(bundle)
        review["reviews"] = review["reviews"][:2]
        rows = workflow.report_comparison(self.output, review)["trials"]
        self.assertEqual([row["result"] for row in rows], ["PASS", "FAIL", "NOT_RUN"])

    def test_original_external_candidate_mutation_fails_and_stops_execution(self):
        bundle = self.prepare()
        frozen_candidate = tree_identity(self.output / "inputs" / "candidate")
        source_before = tree_identity(self.source)
        def mutate(_trial, _workspace, _package, _evidence):
            (self.candidate / "SKILL.md").write_text("External candidate changed.\n", encoding="utf-8")
        adapter = self.run_simulated(SimulatedAdapter(mutate))
        record = read_json(self.output / "trials" / bundle["trials"][0]["id"] / "record.json")
        self.assertIn("external-package-changed", record["stateFailures"])
        self.assertEqual(len(adapter.executions), 1)
        self.assertEqual(tree_identity(self.output / "inputs" / "candidate"), frozen_candidate)
        self.assertEqual(tree_identity(self.source), source_before)
        review = reviews_for(bundle)
        review["reviews"] = review["reviews"][:1]
        rows = workflow.report_comparison(self.output, review)["trials"]
        self.assertEqual([row["result"] for row in rows], ["FAIL", "NOT_RUN", "NOT_RUN"])
        self.assert_code("prior-trial-invalid-new-bundle-required", workflow.run_comparison,
                         self.output, adapter=adapter)
        self.assertEqual(len(adapter.executions), 1)

    def test_ambient_package_mutation_fails_and_stops_execution(self):
        ambient = self.root / "ambient package"
        ambient.mkdir()
        skill = ambient / "SKILL.md"
        skill.write_text("---\nname: beta\ndescription: Synthetic ambient skill.\n---\n", encoding="utf-8")
        self.spec["settings"]["ambientSkills"] = [{"path": str(skill), "name": "beta",
            "sha256": hashlib.sha256(skill.read_bytes()).hexdigest()}]
        bundle = self.prepare()
        def mutate(_trial, _workspace, _package, _evidence):
            (ambient / "reference.md").write_text("Unauthorized reference addition.\n", encoding="utf-8")
        adapter = self.run_simulated(SimulatedAdapter(mutate))
        record = read_json(self.output / "trials" / bundle["trials"][0]["id"] / "record.json")
        self.assertIn("external-package-changed", record["stateFailures"])
        self.assertEqual(len(adapter.executions), 1)
        review = reviews_for(bundle)
        review["reviews"] = review["reviews"][:1]
        self.assertEqual(workflow.report_comparison(self.output, review)["trials"][0]["result"], "FAIL")

    def test_finalized_record_tampering_is_rejected_in_report_and_resume(self):
        bundle = self.prepare()
        def mutate(_trial, workspace, _package, _evidence):
            (workspace / "unrelated.txt").write_text("Unauthorized modification.\n", encoding="utf-8")
        adapter = self.run_simulated(SimulatedAdapter(mutate))
        record_path = self.output / "trials" / bundle["trials"][0]["id"] / "record.json"
        original = read_json(record_path)
        self.assertTrue(original["stateFailures"])
        for field, forged in (("stateFailures", []), ("simulated", False), ("status", "running")):
            with self.subTest(field=field):
                changed = deepcopy(original)
                changed[field] = forged
                write_json(record_path, changed)
                self.assert_code("execution-record-changed", workflow.report_comparison, self.output)
                self.assert_code("prior-record-changed", workflow.run_comparison, self.output,
                                 adapter=adapter)
                self.assertEqual(len(adapter.executions), 1)
        write_json(record_path, original)
        self.assertEqual(workflow.report_comparison(self.output)["trials"][0]["result"], "FAIL")

    def test_missing_finalized_record_is_not_reported_as_not_run(self):
        bundle = self.prepare()
        self.run_simulated()
        record_path = self.output / "trials" / bundle["trials"][0]["id"] / "record.json"
        record_path.unlink()
        self.assert_code("execution-record-missing", workflow.report_comparison, self.output)
        self.assert_code("cleanup-record-missing", workflow.cleanup_comparison,
                         self.output, self.prepared["cleanupToken"])
        self.assertTrue(self.output.exists())

    def test_frozen_input_or_record_drift_blocks_continuation(self):
        self.prepare()
        (self.output / "inputs" / "candidate" / "SKILL.md").write_text("Changed frozen package.\n", encoding="utf-8")
        self.assert_code("frozen-inputs-changed", workflow.run_comparison, self.output,
                         adapter=SimulatedAdapter())
        self.assert_code("frozen-inputs-changed", workflow.report_comparison, self.output)

    def test_pending_workspace_drift_blocks_before_adapter_execution(self):
        bundle = self.prepare()
        (self.output / bundle["trials"][0]["workspace"] / "README.md").write_text("Changed.\n", encoding="utf-8")
        adapter = SimulatedAdapter()
        self.assert_code("pending-workspace-changed", workflow.run_comparison, self.output,
                         adapter=adapter)
        self.assertEqual(adapter.executions, [])

    def test_post_execution_evidence_or_workspace_tampering_invalidates_comparison(self):
        bundle = self.prepare()
        self.run_simulated()
        first, second = bundle["trials"][:2]
        response = self.output / "trials" / first["id"] / "evidence" / "response.txt"
        response.write_text("Forged evidence.\n", encoding="utf-8")
        (self.output / second["workspace"] / "README.md").write_text("After-the-fact edit.\n", encoding="utf-8")
        rows = workflow.report_comparison(self.output, reviews_for(bundle))["trials"]
        self.assertEqual([row["result"] for row in rows], ["FAIL", "FAIL", "PASS"])
        self.assertFalse(rows[0]["validComparison"])
        self.assertFalse(rows[1]["validComparison"])

    def test_missing_capability_preflight_never_calls_execute(self):
        self.prepare()
        adapter = SimulatedAdapter(preflight=lambda *_: {"ok": False, "reason": "missing-capability"})
        self.run_simulated(adapter)
        rows = workflow.report_comparison(self.output)["trials"]
        self.assertEqual(adapter.executions, [])
        self.assertTrue(all(row["executionStatus"] == "blocked" for row in rows))
        self.assertEqual({row["result"] for row in rows}, {"NOT_RUN"})

    def test_host_configuration_mutation_stops_batch_without_erasing_evidence(self):
        bundle = self.prepare()
        adapter = self.run_simulated(SimulatedAdapter(result={
            "started": True, "status": "blocked", "cleanupConfirmed": True,
            "userConfigUnchanged": False,
        }))
        record = read_json(self.output / "trials" / bundle["trials"][0]["id"] / "record.json")
        self.assertIn("host-configuration-changed", record["stateFailures"])
        self.assertEqual(len(adapter.executions), 1)
        rows = workflow.report_comparison(self.output)["trials"]
        self.assertEqual([row["result"] for row in rows], ["FAIL", "NOT_RUN", "NOT_RUN"])

    def test_host_configuration_mutation_in_preflight_blocks_model_dispatch(self):
        bundle = self.prepare()
        adapter = self.run_simulated(SimulatedAdapter(preflight=lambda *_: {
            "ok": True, "cleanupConfirmed": True, "userConfigUnchanged": False,
        }))
        record = read_json(self.output / "trials" / bundle["trials"][0]["id"] / "record.json")
        self.assertIn("host-configuration-changed", record["stateFailures"])
        self.assertEqual(len(adapter.preflights), 1)
        self.assertEqual(adapter.executions, [])

    def test_expired_batch_and_preflight_deadline_do_not_start_model_work(self):
        self.prepare()
        now = [100.0]
        def consume_deadline(*_):
            now[0] += 100.0
            return {"ok": True}
        adapter = SimulatedAdapter(preflight=consume_deadline)
        result = workflow.run_comparison(self.output, adapter=adapter, clock=lambda: now[0])
        self.assertEqual(result["attempted"], 1)
        self.assertEqual(adapter.executions, [])
        workflow.run_comparison(self.output, adapter=adapter, clock=lambda: now[0])
        self.assertEqual(len(adapter.preflights), 1)

    def test_timeout_with_confirmed_cleanup_is_blocked_and_can_be_removed(self):
        bundle = self.prepare()
        result = {"started": True, "status": "timeout", "cleanupConfirmed": True}
        self.run_simulated(SimulatedAdapter(result=result))
        rows = workflow.report_comparison(self.output, reviews_for(bundle))["trials"]
        self.assertEqual({row["result"] for row in rows}, {"BLOCKED"})
        workflow.cleanup_comparison(self.output, self.prepared["cleanupToken"])
        self.assertFalse(self.output.exists())

    def test_interruption_or_malformed_result_keeps_partial_evidence_and_blocks_cleanup(self):
        bundle = self.prepare()
        adapter = SimulatedAdapter(result={"status": "invented"})
        self.run_simulated(adapter)
        record_path = self.output / "trials" / bundle["trials"][0]["id"] / "record.json"
        record = read_json(record_path)
        self.assertEqual(record["status"], "blocked")
        self.assertFalse(record["cleanupConfirmed"])
        self.assertEqual(len(adapter.executions), 1)
        self.assertTrue((record_path.parent / "evidence" / "response.txt").exists())
        self.assert_code("prior-trial-invalid-new-bundle-required", workflow.run_comparison,
                         self.output, adapter=adapter)
        self.assertEqual(len(adapter.executions), 1)
        self.assert_code("process-cleanup-unconfirmed", workflow.cleanup_comparison,
                         self.output, self.prepared["cleanupToken"])
        record["status"] = "running"
        write_json(record_path, record)
        self.assert_code("prior-record-changed", workflow.run_comparison,
                         self.output, adapter=adapter)

    def test_keyboard_interrupt_is_recorded_without_restarting_completed_work(self):
        bundle = self.prepare()
        def interrupt(*_):
            raise KeyboardInterrupt
        self.run_simulated(SimulatedAdapter(interrupt))
        record = read_json(self.output / "trials" / bundle["trials"][0]["id"] / "record.json")
        self.assertEqual(record["status"], "interrupted")
        self.assertFalse(record["cleanupConfirmed"])
        self.assert_code("process-cleanup-unconfirmed", workflow.cleanup_comparison,
                         self.output, self.prepared["cleanupToken"])

    def test_cleanup_requires_ownership_and_preserves_unrelated_work(self):
        self.prepare()
        unrelated = self.root / "keep this.txt"
        unrelated.write_text("User-owned data.\n", encoding="utf-8")
        with self.assertRaises(StateError):
            workflow.cleanup_comparison(self.output, "wrong-token")
        self.assertTrue(self.output.exists())
        workflow.cleanup_comparison(self.output, self.prepared["cleanupToken"])
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "User-owned data.\n")

    def test_cli_diagnostics_do_not_expose_private_spec_values(self):
        canary = "PRIVATE_COMPARISON_CANARY_7b1d"
        spec_path = self.root / "invalid.json"
        spec = deepcopy(self.spec)
        spec[canary] = canary
        write_json(spec_path, spec)
        standard_out, standard_err = io.StringIO(), io.StringIO()
        with redirect_stdout(standard_out), redirect_stderr(standard_err):
            result = workflow.main(["prepare", "--spec", str(spec_path), "--source", str(self.source),
                                    "--output", str(self.output)])
        self.assertEqual(result, 2)
        rendered = standard_out.getvalue() + standard_err.getvalue()
        self.assertNotIn(canary, rendered)
        self.assertNotIn(str(self.root), rendered)
        self.assertIn("BLOCKED", rendered)

    def test_offline_recursion_guard_blocks_opted_in_real_adapter_loading(self):
        self.prepare()
        module = types.ModuleType("evals.comparison_codex")
        module.CodexAdapter = mock.Mock(side_effect=AssertionError("model launch canary"))
        with mock.patch.dict(sys.modules, {"evals.comparison_codex": module}), mock.patch.dict(
            os.environ, {"P537_OFFLINE_CHECKS_ACTIVE": "1"}
        ):
            self.assert_code("model-execution-not-authorized", workflow.run_comparison,
                             self.output, allow_model_execution=True)
        module.CodexAdapter.assert_not_called()


class DocumentationComparisonSmokeTests(unittest.TestCase):
    def test_existing_update_no_op_and_held_out_audit_complete_simulated_workflow(self):
        with tempfile.TemporaryDirectory(prefix="p537 docs comparison ") as directory:
            root = Path(directory)
            source, candidate, output = root / "source checkout", root / "candidate package", root / "run bundle"
            shutil.copytree(REPOSITORY / "evals" / "docs-audit", source / "evals" / "docs-audit")
            shutil.copytree(REPOSITORY / "skills" / "docs-audit", source / "skills" / "docs-audit")
            shutil.copytree(source / "skills" / "docs-audit", candidate)
            cases = (
                ("stale-public-contract", "Update this repository's public documentation to match its implemented service contract.", ["README.md"]),
                ("accurate-no-op", "Refresh this repository's documentation. Make no changes unsupported by implementation evidence.", []),
                ("plain-audit-stale-public-contract", "Audit this repository's documentation against its implemented service contract and report findings without edits.", []),
            )
            spec = {
                "schemaVersion": 1, "suite": "docs-audit", "candidatePackage": str(candidate),
                "cases": [{"id": case, "heldOut": case.startswith("plain-audit"),
                           "setup": {"kind": "materializer", "reviewed": True}, "allowedPaths": allowed,
                           "promptOverride": {"text": prompt, "reason": "Reviewed equivalent task without a named-skill invocation."},
                           "verification": [{"phase": phase, "argv": ["python", "-B", "-m", "unittest", "-v"],
                                             "reason": "Existing disposable fixture unit checks.", "timeoutSeconds": 30,
                                             "expectedExitCodes": [0]} for phase in ("before", "after")]}
                          for case, prompt, allowed in cases],
                "settings": settings(), "authorization": "Offline simulated fixture execution only.",
                "limits": {"maxTrials": 9, "trialTimeoutSeconds": 60, "batchTimeoutSeconds": 600},
            }
            baseline_source = tree_identity(source)
            prepared = workflow.prepare_comparison(spec, source, output)
            bundle = workflow.load_comparison(output)
            self.assertEqual(prepared["trialCount"], 9)
            for case_id, _prompt, _allowed in cases:
                selected = [trial for trial in bundle["trials"] if trial["caseId"] == case_id]
                self.assertEqual(len({trial["fixtureIdentity"] for trial in selected}), 1)
                self.assertEqual(len({trial["initialState"]["git"]["staged"] for trial in selected}), 1)
                for trial in selected:
                    workspace = output / trial["workspace"]
                    self.assertFalse((workspace / "comparison.json").exists())
                    self.assertNotIn(trial["arm"], str(workspace))
                    self.assertEqual(trial["heldOut"], case_id.startswith("plain-audit"))
            def perform(trial, workspace, _package, evidence):
                if trial["caseId"] == "stale-public-contract":
                    readme = workspace / "README.md"
                    text = readme.read_text(encoding="utf-8")
                    readme.write_text(text.replace("8080", "9000").replace("/v1/items", "/v2/items")
                                      .replace("`name`", "`title`"), encoding="utf-8")
            adapter = SimulatedAdapter(perform)
            result = workflow.run_comparison(output, adapter=adapter)
            self.assertEqual(result["attempted"], 9)
            report = workflow.report_comparison(output, reviews_for(bundle))
            self.assertEqual({row["result"] for row in report["trials"]}, {"PASS"})
            self.assertEqual(tree_identity(source), baseline_source)
            for trial in bundle["trials"]:
                record = read_json(output / "trials" / trial["id"] / "record.json")
                self.assertEqual(record["stateFailures"], [])
                self.assertTrue(all(check["status"] == "pass" for check in record["nativeChecks"]))
                self.assertEqual(len(record["nativeChecks"]), 2)
                self.assertEqual(record["before"]["git"]["staged"], record["after"]["git"]["staged"])
                if trial["caseId"] == "stale-public-contract":
                    self.assertNotEqual(record["before"]["files"]["README.md"], record["after"]["files"]["README.md"])
                else:
                    self.assertEqual(record["before"]["files"], record["after"]["files"])
                evidence = output / "trials" / trial["id"] / "evidence"
                self.assertTrue((evidence / "before" / "README.md").is_file())
                self.assertTrue((evidence / "after" / "README.md").is_file())
            workflow.cleanup_comparison(output, prepared["cleanupToken"])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
