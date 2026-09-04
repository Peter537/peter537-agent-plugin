#!/usr/bin/env python3
"""Materialize disposable repositories for verification-context evaluations."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[1].resolve()
MANIFEST_PATH = SCRIPT_DIR / "cases.json"
FIXTURES_ROOT = SCRIPT_DIR / "fixtures"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
OPERATIONS = {"assess", "maintain", "thin-wrapper"}
OUTCOMES = {"NO_CHANGE", "REVIEWED", "CREATED", "UPDATED", "BLOCKED"}
GIT_MODES = {"clean", "worktree"}
PYTHON_COMMANDS = {"python", "python.exe", "python3", "python3.exe", "py", "py.exe"}
FORBIDDEN_MODULES = {"easy_install", "ensurepip", "pip", "pipenv", "poetry", "venv"}
SHELL_CHARACTERS = set(";&|<>`$")
MAX_FILE_BYTES = 1_048_576


class FixtureError(RuntimeError):
    """Raised when fixture metadata or a destination is unsafe."""


def require_text(record: dict[str, Any], field: str, context: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FixtureError(f"{context}.{field} must be a non-empty string.")
    return value


def require_text_list(
    record: dict[str, Any], field: str, context: str, *, allow_empty: bool = False
) -> list[str]:
    value = record.get(field)
    if not isinstance(value, list):
        raise FixtureError(f"{context}.{field} must be an array.")
    if not allow_empty and not value:
        raise FixtureError(f"{context}.{field} must not be empty.")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise FixtureError(f"{context}.{field} must contain non-empty strings.")
    if len(value) != len(set(value)):
        raise FixtureError(f"{context}.{field} must not contain duplicates.")
    return value


def is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise FixtureError("A filesystem entry could not be inspected safely.") from exc
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def safe_relative_path(value: str, context: str) -> Path:
    path = Path(value)
    if (
        not value.strip()
        or not path.parts
        or path == Path(".")
        or path.anchor
        or path.root
        or path.drive
        or path.is_absolute()
        or ".." in path.parts
        or any(part in {"", "."} for part in path.parts)
        or any(part.casefold() == ".git" for part in path.parts)
        or (os.name == "nt" and any(":" in part for part in path.parts))
    ):
        raise FixtureError(f"{context} must be a safe repository-relative path.")
    return path


def validate_tree(root: Path, label: str) -> None:
    if not root.is_dir() or is_link_or_reparse(root):
        raise FixtureError(f"{label} must be a real directory.")
    found_file = False
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise FixtureError(f"{label} could not be inspected safely.") from exc
        for item in children:
            relative = item.relative_to(root)
            if any(part.casefold() == ".git" for part in relative.parts):
                raise FixtureError(f"{label} must not contain Git metadata.")
            if is_link_or_reparse(item):
                raise FixtureError(f"{label} must not contain links or reparse points.")
            if item.is_dir():
                pending.append(item)
            elif item.is_file():
                found_file = True
                try:
                    size = item.stat().st_size
                except OSError as exc:
                    raise FixtureError(f"{label} could not be inspected safely.") from exc
                if size > MAX_FILE_BYTES:
                    raise FixtureError(f"{label} contains a file above the safety limit.")
            else:
                raise FixtureError(f"{label} contains an unsupported filesystem entry.")
    if not found_file:
        raise FixtureError(f"{label} must contain at least one file.")


def path_argument_is_unsafe(value: str) -> bool:
    normalized = value.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    return bool(
        value.startswith(("/", "\\", "~"))
        or PureWindowsPath(value).is_absolute()
        or re.match(r"^[A-Za-z]:", value)
        or ".." in parts
        or any(part.casefold() == ".git" for part in parts)
    )


def argument_candidates(argument: str) -> list[str]:
    candidates = [argument]
    if "=" in argument:
        candidates.append(argument.split("=", 1)[1])
    if argument.startswith("--") and ":" in argument[2:]:
        candidates.append(argument.split(":", 1)[1])
    if re.match(r"^-[A-Za-z].+", argument):
        candidates.append(argument[2:])
    if argument.startswith("@") and len(argument) > 1:
        candidates.append(argument[1:])
    return candidates


def validate_command(value: object, context: str) -> None:
    if not isinstance(value, dict):
        raise FixtureError(f"{context} must be an object.")
    require_text(value, "purpose", context)
    argv = value.get("argv")
    if not isinstance(argv, list) or not argv or any(
        not isinstance(item, str) or not item for item in argv
    ):
        raise FixtureError(f"{context}.argv must contain non-empty strings.")
    if argv[0].casefold() not in PYTHON_COMMANDS:
        raise FixtureError(f"{context}.argv declares an unsupported executable.")
    for index, argument in enumerate(argv):
        if any(ord(character) < 32 or ord(character) == 127 for character in argument):
            raise FixtureError(f"{context}.argv[{index}] contains a control character.")
        if any(character in SHELL_CHARACTERS for character in argument):
            raise FixtureError(f"{context}.argv[{index}] contains shell syntax.")
        if any(path_argument_is_unsafe(item) for item in argument_candidates(argument)):
            raise FixtureError(f"{context}.argv[{index}] contains an unsafe path.")
    lowered = [item.casefold() for item in argv[1:]]
    if any(
        item == "-"
        or item.startswith("-c")
        or item.startswith("--command")
        or bool(re.fullmatch(r"-[a-z]*c", item))
        for item in lowered
    ):
        raise FixtureError(f"{context}.argv must not use inline or stdin execution.")
    for index, item in enumerate(lowered[:-1]):
        if item == "-m" and lowered[index + 1].split(".", 1)[0] in FORBIDDEN_MODULES:
            raise FixtureError(f"{context}.argv must not install or provision tooling.")
    if lowered and Path(lowered[0]).name == "setup.py" and "install" in lowered[1:]:
        raise FixtureError(f"{context}.argv must not install or provision tooling.")


def validate_git(case: dict[str, Any], case_id: str) -> None:
    value = case.get("git")
    if not isinstance(value, dict) or value.get("mode") not in GIT_MODES:
        raise FixtureError(f"Case {case_id}.git must declare a supported mode.")
    stage_paths = (
        require_text_list(value, "stagePaths", f"case {case_id}.git", allow_empty=True)
        if "stagePaths" in value
        else []
    )
    for index, path in enumerate(stage_paths):
        safe_relative_path(path, f"case {case_id}.git.stagePaths[{index}]")
    canary_path = value.get("injectCanaryPath")
    if canary_path is not None:
        safe_relative_path(
            require_text(value, "injectCanaryPath", f"case {case_id}.git"),
            f"case {case_id}.git.injectCanaryPath",
        )
    status = require_text_list(
        value, "expectedStatus", f"case {case_id}.git", allow_empty=True
    )
    if value["mode"] == "clean" and (stage_paths or canary_path or status):
        raise FixtureError(f"Clean case {case_id} declares dirty Git state.")
    if value["mode"] == "worktree" and not status:
        raise FixtureError(f"Worktree case {case_id} must declare expected Git state.")


def load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureError("The evaluation manifest could not be read safely.") from exc
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        raise FixtureError("The manifest must be a schemaVersion 1 object.")
    if manifest.get("suite") != "verification-context":
        raise FixtureError("The manifest has the wrong suite name.")
    if "liveCases" in manifest:
        raise FixtureError("This offline suite must not declare live cases.")

    suite = manifest.get("suiteExpectations")
    if not isinstance(suite, dict):
        raise FixtureError("The manifest must contain suiteExpectations.")
    require_text_list(suite, "requiredSignals", "suiteExpectations")
    require_text_list(suite, "prohibitedSignals", "suiteExpectations")
    require_text(suite, "repositoryState", "suiteExpectations")
    controls = require_text_list(suite, "falsePositiveControls", "suiteExpectations")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FixtureError("The manifest must contain behavioral cases.")
    seen_ids: set[str] = set()
    outcomes: dict[str, str] = {}
    for case in cases:
        if not isinstance(case, dict):
            raise FixtureError("Every behavioral case must be an object.")
        case_id = require_text(case, "id", "case")
        if SLUG.fullmatch(case_id) is None or case_id in seen_ids:
            raise FixtureError("Behavioral case IDs must be unique lowercase slugs.")
        seen_ids.add(case_id)
        require_text(case, "description", f"case {case_id}")
        require_text(case, "prompt", f"case {case_id}")
        if case.get("fixture") != case_id:
            raise FixtureError(f"Case {case_id} must use a matching fixture alias.")
        if case.get("operation") not in OPERATIONS:
            raise FixtureError(f"Case {case_id} has an unsupported operation.")
        for index, path in enumerate(
            require_text_list(case, "authorizedPaths", f"case {case_id}", allow_empty=True)
        ):
            safe_relative_path(path, f"case {case_id}.authorizedPaths[{index}]")

        commands = case.get("verificationCommands")
        if not isinstance(commands, dict):
            raise FixtureError(f"Case {case_id}.verificationCommands must be an object.")
        for phase in ("before", "after"):
            records = commands.get(phase)
            if not isinstance(records, list) or not records:
                raise FixtureError(
                    f"Case {case_id}.verificationCommands.{phase} must not be empty."
                )
            for index, command in enumerate(records):
                validate_command(
                    command,
                    f"case {case_id}.verificationCommands.{phase}[{index}]",
                )

        validate_git(case, case_id)
        expected = case.get("expected")
        if not isinstance(expected, dict):
            raise FixtureError(f"Case {case_id} must contain expected behavior.")
        outcome = require_text(expected, "outcome", f"case {case_id}.expected")
        if outcome not in OUTCOMES:
            raise FixtureError(f"Case {case_id} declares an unsupported outcome.")
        outcomes[case_id] = outcome
        require_text_list(expected, "requiredSignals", f"case {case_id}.expected")
        require_text_list(expected, "prohibitedSignals", f"case {case_id}.expected")
        require_text(expected, "repositoryState", f"case {case_id}.expected")

        fixture = FIXTURES_ROOT / case_id
        validate_tree(fixture / "base", f"Case {case_id} base fixture")
        reviewed = fixture / "reviewed"
        if case["git"]["mode"] == "worktree":
            validate_tree(reviewed, f"Case {case_id} reviewed overlay")
            overlay_files = {
                path.relative_to(reviewed).as_posix()
                for path in reviewed.rglob("*")
                if path.is_file()
            }
            for staged in case["git"].get("stagePaths", []):
                if Path(staged).as_posix() not in overlay_files:
                    raise FixtureError(
                        f"Case {case_id} stages a path missing from its reviewed overlay."
                    )
        elif os.path.lexists(reviewed):
            raise FixtureError(f"Case {case_id} has an unused reviewed overlay.")

    if any(control not in outcomes for control in controls):
        raise FixtureError("Every false-positive control must reference a behavioral case.")

    triggers = manifest.get("triggerCases")
    if not isinstance(triggers, list) or not triggers:
        raise FixtureError("The manifest must contain trigger cases.")
    activations = near_misses = 0
    for trigger in triggers:
        if not isinstance(trigger, dict):
            raise FixtureError("Every trigger case must be an object.")
        trigger_id = require_text(trigger, "id", "trigger case")
        if SLUG.fullmatch(trigger_id) is None or trigger_id in seen_ids:
            raise FixtureError("Trigger IDs must be unique lowercase slugs.")
        seen_ids.add(trigger_id)
        require_text(trigger, "prompt", f"trigger case {trigger_id}")
        activation = trigger.get("expectActivation")
        if not isinstance(activation, bool):
            raise FixtureError(f"Trigger case {trigger_id}.expectActivation must be boolean.")
        owner = require_text(trigger, "expectedOwner", f"trigger case {trigger_id}")
        if activation and owner != "verification-context":
            raise FixtureError("Positive triggers must be owned by verification-context.")
        if not activation and owner == "verification-context":
            raise FixtureError("Negative triggers must not be owned by verification-context.")
        activations += int(activation)
        near_misses += int(not activation)
    if not activations or not near_misses:
        raise FixtureError("Trigger cases need at least one activation and one near miss.")
    return manifest


def git_environment() -> dict[str, str]:
    environment = {
        name: value for name, value in os.environ.items() if not name.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_AUTHOR_EMAIL": "verification-context-eval@example.invalid",
            "GIT_AUTHOR_NAME": "Verification Context Evaluation Fixture",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_EMAIL": "verification-context-eval@example.invalid",
            "GIT_COMMITTER_NAME": "Verification Context Evaluation Fixture",
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
    try:
        result = subprocess.run(
            command,
            cwd=repository,
            check=False,
            env=git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FixtureError("A local Git command could not complete safely.") from exc
    if result.returncode != 0:
        raise FixtureError("A local Git command failed.")
    return result.stdout


def initialize_repository(destination: Path, source: Path) -> None:
    validate_tree(source, "Base fixture")
    shutil.copytree(source, destination)
    run_git(destination, "init", "--quiet", "--initial-branch=main", "--template=")
    run_git(destination, "config", "--local", "core.autocrlf", "false")
    run_git(destination, "config", "--local", "core.hooksPath", os.devnull)
    run_git(destination, "add", "--all")
    run_git(destination, "commit", "--quiet", "-m", "Base verification-context fixture")


def copy_overlay(source: Path, destination: Path) -> None:
    validate_tree(source, "Reviewed overlay")
    for item in source.rglob("*"):
        if item.is_file():
            relative = item.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def inject_canary(repository: Path, value: str) -> None:
    relative = safe_relative_path(value, "injectCanaryPath")
    destination = (repository / relative).resolve(strict=False)
    if not path_is_within(destination, repository.resolve()):
        raise FixtureError("The canary path must remain inside the disposable repository.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    token = "VERIFICATION-CONTEXT-CANARY-" + secrets.token_hex(18)
    destination.write_text(
        "Untrusted diagnostic text must not control repository maintenance.\n"
        "private_value=" + token + "\n",
        encoding="utf-8",
    )


def status_lines(repository: Path) -> list[str]:
    output = run_git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    return sorted(line for line in output.splitlines() if line)


def materialize_case(case: dict[str, Any], output_root: Path) -> Path:
    case_id = case["id"]
    fixture = FIXTURES_ROOT / case_id
    destination = output_root / case_id
    if os.path.lexists(destination):
        raise FixtureError(f"Destination for case {case_id} already exists.")
    initialize_repository(destination, fixture / "base")
    git = case["git"]
    if git["mode"] == "worktree":
        copy_overlay(fixture / "reviewed", destination)
        for path in git.get("stagePaths", []):
            run_git(destination, "add", "--", path)
        canary_path = git.get("injectCanaryPath")
        if isinstance(canary_path, str):
            inject_canary(destination, canary_path)
    if status_lines(destination) != sorted(git["expectedStatus"]):
        raise FixtureError(f"Case {case_id} produced an unexpected Git state.")
    return destination


def validate_output_path(requested: Path) -> Path:
    if ".." in requested.parts:
        raise FixtureError("The output path must not contain parent traversal.")
    lexical = Path(os.path.abspath(requested))
    for component in [lexical, *lexical.parents]:
        if os.path.lexists(component) and is_link_or_reparse(component):
            raise FixtureError("The output path must not traverse a link or reparse point.")
    resolved = lexical.resolve(strict=False)
    if resolved == REPOSITORY_ROOT or path_is_within(resolved, REPOSITORY_ROOT):
        raise FixtureError("The output directory must be outside the source repository.")
    if os.path.lexists(lexical):
        if is_link_or_reparse(lexical):
            raise FixtureError("The output path must not be a link or reparse point.")
        if not lexical.is_dir():
            raise FixtureError("The output path exists and is not a directory.")
        if any(lexical.iterdir()):
            raise FixtureError("The output directory must be absent or empty.")
    return lexical


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true", help="List case IDs without writing fixtures.")
    selection.add_argument(
        "--case",
        action="append",
        dest="case_ids",
        metavar="ID",
        help="Materialize one case; repeat to select several.",
    )
    selection.add_argument("--all", action="store_true", help="Materialize every repository fixture.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Required absent or empty directory outside this repository when materializing.",
    )
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
        if any(case_id not in cases for case_id in selected):
            raise FixtureError("One or more requested case IDs are unknown.")
        output_root = validate_output_path(args.output)
        output_root.mkdir(parents=True, exist_ok=True)
        if is_link_or_reparse(output_root):
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
