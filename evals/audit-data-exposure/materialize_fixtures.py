#!/usr/bin/env python3
"""Materialize disposable Git repositories for data-exposure evaluations."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
from typing import Any
import zipfile


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[1]
MANIFEST_PATH = SCRIPT_DIR / "cases.json"
FIXTURES_ROOT = SCRIPT_DIR / "fixtures"
CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SCENARIOS = {"clean", "changes", "renamed-history", "path-boundary", "coverage-gaps", "archive"}
SCOPES = {"full", "changes", "path", "history"}
OUTCOMES = {"PASS", "PASS_WITH_WARNINGS", "FAIL", "BLOCKED"}
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
        metadata = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise FixtureError(f"Cannot inspect path {path}: {exc}") from exc
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def safe_relative_path(value: str, context: str) -> Path:
    path = Path(value)
    if (
        not value.strip()
        or "\x00" in value
        or not path.parts
        or path == Path(".")
        or path.anchor
        or path.root
        or path.drive
        or path.is_absolute()
        or ".." in path.parts
        or any(part.casefold() == ".git" for part in path.parts)
        or any(part in {"", "."} for part in path.parts)
        or (os.name == "nt" and any(":" in part for part in path.parts))
    ):
        raise FixtureError(f"{context} must be a safe repository-relative path.")
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
                if path.stat().st_size > MAX_FIXTURE_FILE_BYTES:
                    raise FixtureError(f"{label} file exceeds the safety limit: {path}")
            else:
                raise FixtureError(f"{label} contains an unsupported entry: {path}")
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
    require_text(suite, "repositoryState", "suiteExpectations")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 8:
        raise FixtureError("Fixture manifest must contain at least eight behavioral cases.")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise FixtureError("Every case must be an object.")
        case_id = require_text(case, "id", "case")
        if CASE_ID_PATTERN.fullmatch(case_id) is None or case_id in seen:
            raise FixtureError(f"Case id must be a unique lowercase slug: {case_id}")
        seen.add(case_id)
        require_text(case, "description", f"case {case_id}")
        require_text(case, "prompt", f"case {case_id}")
        if case.get("fixture") != case_id:
            raise FixtureError(f"Case {case_id} must use a matching fixture directory.")
        scenario = require_text(case, "scenario", f"case {case_id}")
        if scenario not in SCENARIOS:
            raise FixtureError(f"Case {case_id} has an unsupported scenario.")
        scope = require_text(case, "scannerScope", f"case {case_id}")
        if scope not in SCOPES:
            raise FixtureError(f"Case {case_id} has an unsupported scanner scope.")
        scanner_paths = require_text_list(
            case, "scannerPaths", f"case {case_id}", allow_empty=True
        ) if "scannerPaths" in case else []
        for index, value in enumerate(scanner_paths):
            safe_relative_path(value, f"case {case_id}.scannerPaths[{index}]")
        if scope == "path" and not scanner_paths:
            raise FixtureError(f"Path case {case_id} must declare scannerPaths.")
        if scope != "path" and scanner_paths:
            raise FixtureError(f"Non-path case {case_id} must not declare scannerPaths.")

        git = case.get("git")
        if not isinstance(git, dict):
            raise FixtureError(f"Case {case_id}.git must be an object.")
        require_text_list(git, "expectedStatus", f"case {case_id}.git", allow_empty=True)
        stage_paths = require_text_list(
            git, "stagePaths", f"case {case_id}.git", allow_empty=True
        ) if "stagePaths" in git else []
        for index, value in enumerate(stage_paths):
            safe_relative_path(value, f"case {case_id}.git.stagePaths[{index}]")
        canary_path = git.get("canaryPath")
        if canary_path is not None:
            safe_relative_path(
                require_text(git, "canaryPath", f"case {case_id}.git"),
                f"case {case_id}.git.canaryPath",
            )
            timing = require_text(git, "canaryTiming", f"case {case_id}.git")
            if timing not in {"before-base", "worktree"}:
                raise FixtureError(f"Case {case_id} has an unsupported canary timing.")

        expected = case.get("expected")
        if not isinstance(expected, dict):
            raise FixtureError(f"Case {case_id} must contain expected behavior.")
        if require_text(expected, "outcome", f"case {case_id}.expected") not in OUTCOMES:
            raise FixtureError(f"Case {case_id} has an unsupported expected outcome.")
        require_text_list(expected, "requiredSignals", f"case {case_id}.expected")
        require_text_list(expected, "prohibitedSignals", f"case {case_id}.expected")
        require_text(expected, "repositoryState", f"case {case_id}.expected")

        fixture = FIXTURES_ROOT / case_id
        validate_tree(fixture / "base", f"Case {case_id} base fixture")
        reviewed = fixture / "reviewed"
        expects_reviewed = scenario in {"changes", "renamed-history", "path-boundary"}
        if expects_reviewed:
            validate_tree(reviewed, f"Case {case_id} reviewed fixture")
        elif os.path.lexists(reviewed):
            raise FixtureError(f"Case {case_id} has an unused reviewed fixture.")

    triggers = manifest.get("triggerCases")
    if not isinstance(triggers, list) or len(triggers) < 8:
        raise FixtureError("Fixture manifest must contain at least eight trigger cases.")
    trigger_ids: set[str] = set()
    activation_count = 0
    near_miss_count = 0
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
        if trigger["expectActivation"]:
            activation_count += 1
        else:
            near_miss_count += 1
        require_text(trigger, "expectedOwner", f"trigger case {trigger_id}")
    if activation_count < 6 or near_miss_count < 4:
        raise FixtureError("Trigger coverage requires at least six activations and four near misses.")
    return manifest


def safe_git_environment() -> dict[str, str]:
    environment = {
        name: value for name, value in os.environ.items() if not name.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_AUTHOR_EMAIL": "fixture@localhost",
            "GIT_AUTHOR_NAME": "Data Exposure Evaluation Fixture",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_EMAIL": "fixture@localhost",
            "GIT_COMMITTER_NAME": "Data Exposure Evaluation Fixture",
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


def run_git(repository: Path, *arguments: str, input_text: str | None = None) -> str:
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
        input=input_text,
        stdin=subprocess.DEVNULL if input_text is None else None,
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
        if not item.is_file():
            continue
        relative = item.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def inject_private_canary(repository: Path, relative_path: str) -> None:
    requested = safe_relative_path(relative_path, "canaryPath")
    destination = repository / requested
    destination.parent.mkdir(parents=True, exist_ok=True)
    token = f"private-{secrets.token_hex(18)}@example.invalid"
    destination.write_text(
        "full_name,email,private_path\n"
        f"Evaluation Person,{token},C:\\Users\\private-eval-owner\\export\n",
        encoding="utf-8",
    )


def initialize_repository(destination: Path) -> None:
    run_git(destination, "init", "--quiet", "--initial-branch=main", "--template=")
    run_git(destination, "add", "--all")
    run_git(destination, "commit", "--quiet", "-m", "Base fixture")


def materialize_archive(destination: Path) -> None:
    member_source = destination / "archive-member.txt"
    member_text = member_source.read_text(encoding="utf-8")
    token = f"archive-{secrets.token_hex(18)}@example.invalid"
    with zipfile.ZipFile(destination / "evidence.docx", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/private-records.txt", member_text + token + "\n")
    member_source.unlink()


def add_gap_surfaces(repository: Path) -> None:
    (repository / "binary.dat").write_bytes(b"\x00\x01\x02evaluation")
    nested = repository / "external-module"
    nested.mkdir()
    run_git(nested, "init", "--quiet", "--initial-branch=main", "--template=")
    (nested / "README.md").write_text("Nested fixture\n", encoding="utf-8")
    run_git(nested, "add", "--all")
    run_git(nested, "commit", "--quiet", "-m", "Nested fixture")
    run_git(repository, "add", "external-module", "binary.dat")
    link_blob = run_git(repository, "hash-object", "-w", "--stdin", input_text="../private-target\n").strip()
    run_git(repository, "update-index", "--add", "--cacheinfo", f"120000,{link_blob},linked.txt")
    run_git(repository, "commit", "--quiet", "-m", "Add unsupported surfaces")
    run_git(repository, "checkout", "--", "linked.txt")


def status_lines(repository: Path) -> list[str]:
    output = run_git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    return sorted(line for line in output.splitlines() if line)


def materialize_case(case: dict[str, Any], output_root: Path) -> Path:
    case_id = case["id"]
    source = FIXTURES_ROOT / case_id
    destination = output_root / case_id
    if destination.exists():
        raise FixtureError(f"Destination already exists: {destination}")
    shutil.copytree(source / "base", destination)
    gitignore_template = destination / "gitignore.template"
    if gitignore_template.exists():
        gitignore_template.replace(destination / ".gitignore")
    git = case["git"]
    scenario = case["scenario"]
    if scenario == "archive":
        materialize_archive(destination)
    if scenario == "coverage-gaps":
        (destination / "binary.dat").write_bytes(b"\x00\x01\x02evaluation")
    if git.get("canaryTiming") == "before-base":
        inject_private_canary(destination, git["canaryPath"])
    initialize_repository(destination)

    if scenario == "changes":
        copy_overlay(source / "reviewed", destination)
        for value in git.get("stagePaths", []):
            run_git(destination, "add", "--", value)
        if git.get("canaryTiming") == "worktree":
            inject_private_canary(destination, git["canaryPath"])
    elif scenario == "renamed-history":
        (destination / "selected").mkdir(exist_ok=True)
        run_git(destination, "mv", "legacy/person@example.invalid.txt", "selected/current.txt")
        copy_overlay(source / "reviewed", destination)
        run_git(destination, "add", "--all")
        run_git(destination, "commit", "--quiet", "-m", "Rename and sanitize fixture")
    elif scenario == "path-boundary":
        copy_overlay(source / "reviewed", destination)
        run_git(destination, "add", "--all")
        run_git(destination, "commit", "--quiet", "-m", "one-off personal migration for unrelated data")
        run_git(destination, "tag", "-a", "metadata-fixture", "-m", "delete after personal backfill")
    elif scenario == "coverage-gaps":
        add_gap_surfaces(destination)

    actual_status = status_lines(destination)
    expected_status = sorted(git["expectedStatus"])
    if actual_status != expected_status:
        raise FixtureError(f"Case {case_id} produced an unexpected Git state: {actual_status}")
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
    for component in reversed([absolute, *absolute.parents]):
        if os.path.lexists(component) and is_link_or_reparse_point(component):
            raise FixtureError(
                f"The output path must not traverse a link or reparse point: {component}"
            )
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
            materialize_case(cases[case_id], output_root)
            print(case_id)
        return 0
    except FixtureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
