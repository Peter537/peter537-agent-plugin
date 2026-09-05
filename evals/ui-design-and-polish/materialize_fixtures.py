#!/usr/bin/env python3
"""Materialize disposable Git repositories for UI design evaluations."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[1]
MANIFEST_PATH = SCRIPT_DIR / "cases.json"
FIXTURES_ROOT = SCRIPT_DIR / "fixtures"
CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
OPERATIONS = {"audit", "polish", "refine", "redesign", "create", "context"}
RENDER_POLICIES = {"required-when-safe", "blocked-by-fixture", "not-applicable"}
GIT_MODES = {"clean", "worktree"}
MAX_FIXTURE_FILE_BYTES = 1_048_576


class FixtureError(RuntimeError):
    """Raised when fixture metadata or materialization is unsafe or invalid."""


def require_text(record: dict[str, Any], field: str, context: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FixtureError(f"{context}.{field} must be a non-empty string.")
    return value


def require_text_list(
    record: dict[str, Any], field: str, context: str, *, allow_empty: bool = False
) -> list[str]:
    values = record.get(field)
    if not isinstance(values, list):
        raise FixtureError(f"{context}.{field} must be an array.")
    if not allow_empty and not values:
        raise FixtureError(f"{context}.{field} must not be empty.")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise FixtureError(f"{context}.{field} must contain non-empty strings.")
    if len(values) != len(set(values)):
        raise FixtureError(f"{context}.{field} must not contain duplicates.")
    return values


def is_link_or_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError as exc:
        raise FixtureError(f"Cannot inspect path {path}: {exc}") from exc
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def safe_relative_path(value: str, context: str) -> Path:
    path = Path(value)
    if not value.strip() or path.drive or path.is_absolute() or ".." in path.parts:
        raise FixtureError(f"{context} must be a safe repository-relative path.")
    if any(part in {"", "."} for part in path.parts):
        raise FixtureError(f"{context} contains an invalid path segment.")
    return path


def validate_tree(root: Path, label: str) -> None:
    if not root.is_dir():
        raise FixtureError(f"{label} directory does not exist: {root}")
    if is_link_or_reparse_point(root):
        raise FixtureError(f"{label} root must not be a link or reparse point: {root}")

    found_file = False
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            children = list(directory.iterdir())
        except OSError as exc:
            raise FixtureError(f"Cannot inspect fixture directory {directory}: {exc}") from exc
        for path in children:
            relative = path.relative_to(root)
            if any(part.casefold() == ".git" for part in relative.parts):
                raise FixtureError(f"{label} must not contain .git entries: {path}")
            if is_link_or_reparse_point(path):
                raise FixtureError(f"{label} must not contain links or reparse points: {path}")
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                found_file = True
                try:
                    size = path.stat().st_size
                except OSError as exc:
                    raise FixtureError(f"Cannot inspect fixture file {path}: {exc}") from exc
                if size > MAX_FIXTURE_FILE_BYTES:
                    raise FixtureError(f"{label} file exceeds the safety limit: {path}")
            else:
                raise FixtureError(f"{label} contains an unsupported filesystem entry: {path}")
    if not found_file:
        raise FixtureError(f"{label} must contain at least one file: {root}")


def load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureError(f"Cannot read fixture manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        raise FixtureError("Fixture manifest must be a schemaVersion 1 object.")

    suite = manifest.get("suiteExpectations")
    if not isinstance(suite, dict):
        raise FixtureError("Fixture manifest must contain suiteExpectations.")
    require_text_list(suite, "requiredSignals", "suiteExpectations")
    require_text_list(suite, "prohibitedSignals", "suiteExpectations")
    require_text(suite, "conditionalOutcomePolicy", "suiteExpectations")
    require_text(suite, "repositoryState", "suiteExpectations")
    require_text_list(suite, "blindReviewRubric", "suiteExpectations")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FixtureError("Fixture manifest must contain a non-empty cases array.")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise FixtureError("Every case must be an object.")
        case_id = require_text(case, "id", "case")
        if CASE_ID_PATTERN.fullmatch(case_id) is None or case_id in seen:
            raise FixtureError(f"Case id must be a unique lowercase slug: {case_id}")
        seen.add(case_id)
        for field in ("description", "prompt"):
            require_text(case, field, f"case {case_id}")
        if case.get("fixture") != case_id:
            raise FixtureError(f"Case {case_id} must use a matching fixture directory.")
        if case.get("operation") not in OPERATIONS:
            raise FixtureError(f"Case {case_id} has an unsupported operation.")
        if case.get("renderedVerification") not in RENDER_POLICIES:
            raise FixtureError(f"Case {case_id} has an unsupported renderedVerification value.")
        if not isinstance(case.get("blindReview"), bool):
            raise FixtureError(f"Case {case_id}.blindReview must be boolean.")
        require_text_list(case, "objectiveAssertions", f"case {case_id}")
        for index, value in enumerate(require_text_list(case, "authorizedPaths", f"case {case_id}", allow_empty=True)):
            safe_relative_path(value, f"case {case_id}.authorizedPaths[{index}]")

        git = case.get("git")
        if not isinstance(git, dict) or git.get("mode") not in GIT_MODES:
            raise FixtureError(f"Case {case_id}.git must declare a supported mode.")
        stage_paths = require_text_list(git, "stagePaths", f"case {case_id}.git", allow_empty=True) if "stagePaths" in git else []
        for index, value in enumerate(stage_paths):
            safe_relative_path(value, f"case {case_id}.git.stagePaths[{index}]")
        expected_status = require_text_list(git, "expectedStatus", f"case {case_id}.git", allow_empty=True)
        if git["mode"] == "clean" and (stage_paths or expected_status):
            raise FixtureError(f"Clean case {case_id} must not declare dirty Git state.")

        expected = case.get("expected")
        if not isinstance(expected, dict):
            raise FixtureError(f"Case {case_id} must contain expected behavior.")
        require_text(expected, "outcome", f"case {case_id}.expected")
        require_text_list(expected, "requiredSignals", f"case {case_id}.expected")
        require_text_list(expected, "prohibitedSignals", f"case {case_id}.expected")
        require_text(expected, "repositoryState", f"case {case_id}.expected")

        base = FIXTURES_ROOT / case_id / "base"
        validate_tree(base, f"Case {case_id} base fixture")
        reviewed = FIXTURES_ROOT / case_id / "reviewed"
        if git["mode"] == "worktree":
            validate_tree(reviewed, f"Case {case_id} reviewed overlay")
            overlay_files = {str(path.relative_to(reviewed)).replace("\\", "/") for path in reviewed.rglob("*") if path.is_file()}
            for value in stage_paths:
                if value.replace("\\", "/") not in overlay_files:
                    raise FixtureError(f"Case {case_id} stages a path missing from its reviewed overlay: {value}")
        elif reviewed.exists():
            raise FixtureError(f"Case {case_id} has an unused reviewed overlay.")

    triggers = manifest.get("triggerCases")
    if not isinstance(triggers, list) or not triggers:
        raise FixtureError("Fixture manifest must contain triggerCases.")
    trigger_ids: set[str] = set()
    for trigger in triggers:
        if not isinstance(trigger, dict):
            raise FixtureError("Every trigger case must be an object.")
        trigger_id = require_text(trigger, "id", "trigger case")
        if CASE_ID_PATTERN.fullmatch(trigger_id) is None or trigger_id in trigger_ids:
            raise FixtureError(f"Trigger id must be a unique lowercase slug: {trigger_id}")
        trigger_ids.add(trigger_id)
        require_text(trigger, "prompt", f"trigger case {trigger_id}")
        if not isinstance(trigger.get("expectActivation"), bool):
            raise FixtureError(f"Trigger case {trigger_id}.expectActivation must be boolean.")
    return manifest


def safe_git_environment() -> dict[str, str]:
    environment = {name: value for name, value in os.environ.items() if not name.upper().startswith("GIT_")}
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_AUTHOR_EMAIL": "ui-eval@example.invalid",
            "GIT_AUTHOR_NAME": "UI Evaluation Fixture",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_EMAIL": "ui-eval@example.invalid",
            "GIT_COMMITTER_NAME": "UI Evaluation Fixture",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CREDENTIAL_INTERACTIVE": "never",
            "GIT_LFS_SKIP_SMUDGE": "1",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def run_git(repository: Path, *arguments: str) -> str:
    command = [
        "git",
        "-c", "commit.gpgSign=false",
        "-c", "tag.gpgSign=false",
        "-c", f"core.hooksPath={os.devnull}",
        "-c", "core.autocrlf=false",
        "-c", "protocol.allow=never",
        "-c", "user.useConfigOnly=true",
        *arguments,
    ]
    result = subprocess.run(
        command,
        cwd=repository,
        check=False,
        env=safe_git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise FixtureError(f"Local Git command failed in {repository}: {detail}")
    return result.stdout


def copy_overlay(source: Path, destination: Path) -> None:
    for item in source.rglob("*"):
        if item.is_file():
            relative = item.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def initialize_repository(destination: Path, source: Path) -> None:
    shutil.copytree(source, destination)
    run_git(destination, "init", "--quiet", "--initial-branch=main", "--template=")
    run_git(destination, "add", "--all")
    run_git(destination, "commit", "--quiet", "-m", "Base fixture")


def status_lines(repository: Path) -> list[str]:
    output = run_git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    return sorted(line for line in output.splitlines() if line)


def materialize_case(case: dict[str, Any], output_root: Path) -> Path:
    case_id = case["id"]
    source = FIXTURES_ROOT / case_id
    destination = output_root / case_id
    if destination.exists():
        raise FixtureError(f"Destination already exists: {destination}")
    initialize_repository(destination, source / "base")
    if case["git"]["mode"] == "worktree":
        copy_overlay(source / "reviewed", destination)
        for value in case["git"].get("stagePaths", []):
            run_git(destination, "add", "--", value)
    actual_status = status_lines(destination)
    expected_status = sorted(case["git"]["expectedStatus"])
    if actual_status != expected_status:
        raise FixtureError(f"Case {case_id} produced an unexpected Git state.")
    return destination


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_output_path(requested: Path) -> Path:
    if ".." in requested.parts:
        raise FixtureError("The output path must not contain parent traversal.")
    absolute = Path(os.path.abspath(requested))
    existing_chain = [absolute, *absolute.parents]
    for component in reversed(existing_chain):
        if component.exists() and is_link_or_reparse_point(component):
            raise FixtureError(f"The output path must not traverse a link or reparse point: {component}")
    output_root = absolute.resolve(strict=False)
    repository_root = REPOSITORY_ROOT.resolve()
    if output_root == repository_root or path_is_within(output_root, repository_root):
        raise FixtureError("The output directory must be outside the source repository.")
    if output_root.exists():
        if not output_root.is_dir():
            raise FixtureError("The output path exists and is not a directory.")
        if any(output_root.iterdir()):
            raise FixtureError("The output directory must be absent or empty.")
    return output_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true", help="List case ids without writing fixtures.")
    selection.add_argument("--case", action="append", dest="case_ids", metavar="ID", help="Materialize one case; repeat to select several.")
    selection.add_argument("--all", action="store_true", help="Materialize every repository fixture.")
    parser.add_argument("--output", type=Path, help="Required empty directory outside this repository when materializing fixtures.")
    return parser.parse_args()


def main() -> int:
    try:
        manifest = load_manifest()
        cases = {case["id"]: case for case in manifest["cases"]}
        args = parse_args()
        if args.list:
            for case_id in sorted(cases):
                print(case_id)
            return 0
        if args.output is None:
            raise FixtureError("--output is required when materializing fixtures.")
        if shutil.which("git") is None:
            raise FixtureError("Git is required to materialize evaluation repositories.")
        selected = sorted(cases) if args.all else list(dict.fromkeys(args.case_ids or []))
        unknown = [case_id for case_id in selected if case_id not in cases]
        if unknown:
            raise FixtureError("Unknown case id(s): " + ", ".join(unknown))
        output_root = validate_output_path(args.output)
        output_root.mkdir(parents=True, exist_ok=True)
        if is_link_or_reparse_point(output_root):
            raise FixtureError("The output directory must not be a link or reparse point.")
        for case_id in selected:
            destination = materialize_case(cases[case_id], output_root)
            print(f"{case_id}\t{destination}")
        return 0
    except FixtureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
