#!/usr/bin/env python3
"""Validate the common contract shared by repository evaluation manifests.

This maintenance check is read-only, uses only the Python standard library,
and never executes commands or live cases described by a manifest. Structural
validation cannot establish that a referenced command is safe to run or that
an evaluation measures the intended behavior.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
from typing import Iterable


SCHEMA_VERSION = 1
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_TOP_LEVEL_FIELDS = {
    "schemaVersion",
    "suite",
    "suiteExpectations",
    "cases",
    "triggerCases",
    "liveCases",
}
REQUIRED_TOP_LEVEL_FIELDS = {
    "schemaVersion",
    "suiteExpectations",
    "cases",
    "triggerCases",
}
PATH_FIELDS = {
    "authorizedPaths",
    "canaryPath",
    "injectCanaryPath",
    "overlayPaths",
    "path",
    "scannerPaths",
    "stagePaths",
}
PROVISIONAL_OWNERS = {
    "implementation-workflow",
    "legal-guidance",
    "ordinary-implementation",
    "ordinary implementation",
    "release-workflow",
    "repository-analysis",
}
PYTHON_COMMANDS = {"python", "python.exe", "python3", "python3.exe", "py", "py.exe"}
DOTNET_COMMANDS = {"dotnet", "dotnet.exe"}
FORBIDDEN_PYTHON_MODULES = {
    "easy_install",
    "ensurepip",
    "pip",
    "pipenv",
    "poetry",
    "venv",
}
FORBIDDEN_DOTNET_OPERATIONS = {
    "add",
    "new",
    "nuget",
    "pack",
    "publish",
    "remove",
    "restore",
    "tool",
    "workload",
}
SHELL_OPERATOR = re.compile(r"[;&|<>`$]")
WINDOWS_PERSONAL_HOME = re.compile(
    r"(?i)(?:[a-z]:[\\/](?:users|documents and settings)[\\/][^\\/\s\"']+)"
)
POSIX_PERSONAL_HOME = re.compile(
    r"(?i)(?<![a-z0-9])/(?:home/[^/\s\"'`]+|users/[^/\s\"'`]+|root)(?=[/\s\"'`)\]}:]|$)"
)
TILDE_HOME = re.compile(r"(?:^|[\s\"'`(=])~[\\/]")

DIAGNOSTIC_FIELD_NAMES = ALLOWED_TOP_LEVEL_FIELDS | PATH_FIELDS | {
    "after",
    "argv",
    "authorization",
    "authorizationRequired",
    "before",
    "description",
    "enabledByDefault",
    "expectActivation",
    "expected",
    "expectedOwner",
    "expectedSignals",
    "fixture",
    "id",
    "outcome",
    "prompt",
    "prohibitedSignals",
    "purpose",
    "repositoryState",
    "requiredSignals",
    "trackOutput",
    "verificationCommands",
}
WINDOWS_RESERVED_PATH_NAMES = {
    "aux",
    "con",
    "nul",
    "prn",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}


class PathInspectionError(OSError):
    """Raised when link or reparse metadata cannot be inspected safely."""


@dataclass
class ValidationResult:
    """Collected diagnostics and coverage counts."""

    errors: list[str] = field(default_factory=list)
    fatal_errors: list[str] = field(default_factory=list)
    suite_count: int = 0
    case_count: int = 0
    trigger_count: int = 0
    live_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors and not self.fatal_errors

    @property
    def exit_code(self) -> int:
        if self.fatal_errors:
            return 2
        return 0 if not self.errors else 1


def _is_link_or_reparse(path: Path) -> bool:
    """Return whether *path* is a symlink or Windows reparse point."""

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise PathInspectionError(error.__class__.__name__) from error
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & reparse_flag)


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: object, *, nonempty: bool = True) -> bool:
    if not isinstance(value, list):
        return False
    if nonempty and not value:
        return False
    return all(_nonempty_string(item) for item in value)


def _repository_state(value: object) -> bool:
    """Accept the current scalar contract and a future list representation."""

    return _nonempty_string(value) or _string_list(value)


def _contains_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _contains_personal_home(value: str) -> bool:
    return bool(
        WINDOWS_PERSONAL_HOME.search(value)
        or POSIX_PERSONAL_HOME.search(value)
        or TILDE_HOME.search(value)
    )


def _walk_strings(value: object, location: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield location, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{location}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            shown = _diagnostic_key(key)
            key_location = f"{location}.{shown}"
            if isinstance(key, str):
                yield key_location, key
            yield from _walk_strings(item, key_location)


def _diagnostic_key(key: object) -> str:
    """Return only schema-owned field names for privacy-safe diagnostics."""

    return key if isinstance(key, str) and key in DIAGNOSTIC_FIELD_NAMES else "<field>"


def _relative_path_parts(value: str) -> tuple[str, ...] | None:
    """Return safe repository-relative parts, or ``None`` for unsafe input."""

    if not value or value != value.strip() or _contains_control_characters(value):
        return None
    if value.startswith(("/", "\\", "~")) or PureWindowsPath(value).is_absolute():
        return None
    normalized = value.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("//"):
        return None
    path = PurePosixPath(normalized)
    parts = path.parts
    if not parts or parts == (".",):
        return None
    if any(part in {"", ".", ".."} or part.lower() == ".git" for part in parts):
        return None
    if any(any(character in part for character in "*?[]") for part in parts):
        return None
    if any(
        ":" in part
        or part.endswith((" ", "."))
        or part.split(".", 1)[0].casefold() in WINDOWS_RESERVED_PATH_NAMES
        for part in parts
    ):
        return None
    return parts


def _validate_path_value(
    value: object,
    *,
    label: str,
    location: str,
    result: ValidationResult,
    allow_empty_list: bool = True,
) -> None:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list) and (value or allow_empty_list):
        values = value
    else:
        result.errors.append(f"{label}:{location}: path metadata must be a string or string array")
        return
    for index, item in enumerate(values):
        item_location = location if isinstance(value, str) else f"{location}[{index}]"
        if not isinstance(item, str) or _relative_path_parts(item) is None:
            result.errors.append(
                f"{label}:{item_location}: path metadata must be a safe repository-relative path"
            )


def _validate_known_paths(
    value: object,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_known_paths(
                item,
                label=label,
                location=f"{location}[{index}]",
                result=result,
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            child_location = f"{location}.{_diagnostic_key(key)}"
            if key in PATH_FIELDS:
                _validate_path_value(
                    item,
                    label=label,
                    location=child_location,
                    result=result,
                )
            else:
                _validate_known_paths(
                    item,
                    label=label,
                    location=child_location,
                    result=result,
                )


def _fixture_parts(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, str):
        return None
    parts = _relative_path_parts(value)
    if parts and parts[0] == "fixtures":
        parts = parts[1:]
    return parts or None


def _reject_link_or_inspection_gap(
    path: Path,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> bool:
    """Reject a link/reparse point or a path whose metadata is unavailable."""

    try:
        linked = _is_link_or_reparse(path)
    except PathInspectionError as error:
        result.errors.append(
            f"{label}:{location}: fixture path could not be inspected ({error})"
        )
        return True
    if linked:
        result.errors.append(
            f"{label}:{location}: fixture path must not traverse a link or reparse point"
        )
        return True
    return False


def _validate_fixture_descendants(
    root: Path,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> None:
    """Inspect a fixture tree without following linked or reparse entries."""

    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as error:
            result.errors.append(
                f"{label}:{location}: fixture tree could not be inspected "
                f"({error.__class__.__name__})"
            )
            return
        for entry in entries:
            child = Path(entry.path)
            if _reject_link_or_inspection_gap(
                child,
                label=label,
                location=location,
                result=result,
            ):
                return
            try:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(child)
            except OSError as error:
                result.errors.append(
                    f"{label}:{location}: fixture tree could not be inspected "
                    f"({error.__class__.__name__})"
                )
                return


def _validate_fixture(
    value: object,
    *,
    suite_directory: Path,
    label: str,
    location: str,
    result: ValidationResult,
) -> None:
    parts = _fixture_parts(value)
    if parts is None:
        result.errors.append(
            f"{label}:{location}: fixture must be a safe path or alias beneath the suite fixtures directory"
        )
        return

    fixtures_root = suite_directory / "fixtures"
    current = fixtures_root
    if _reject_link_or_inspection_gap(
        current,
        label=label,
        location=location,
        result=result,
    ):
        return
    for part in parts:
        current = current / part
        if _reject_link_or_inspection_gap(
            current,
            label=label,
            location=location,
            result=result,
        ):
            return
    try:
        exists = current.exists()
        supported_type = current.is_file() or current.is_dir()
    except OSError:
        result.errors.append(f"{label}:{location}: fixture path could not be inspected")
        return
    if not exists:
        result.errors.append(f"{label}:{location}: referenced fixture does not exist")
    elif not supported_type:
        result.errors.append(f"{label}:{location}: fixture must be a regular file or directory")
    elif current.is_dir():
        _validate_fixture_descendants(
            current,
            label=label,
            location=location,
            result=result,
        )


def _validate_evidence_object(
    value: object,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, dict):
        result.errors.append(f"{label}:{location}: expected evidence must be an object")
        return
    for field_name in ("requiredSignals", "prohibitedSignals"):
        if not _string_list(value.get(field_name)):
            result.errors.append(
                f"{label}:{location}.{field_name}: must be a non-empty string array"
            )
    if not _repository_state(value.get("repositoryState")):
        result.errors.append(
            f"{label}:{location}.repositoryState: must be a non-empty string or string array"
        )
    if "outcome" in value and not _nonempty_string(value["outcome"]):
        result.errors.append(f"{label}:{location}.outcome: must be a non-empty string")


def _validate_suite_expectations(
    value: object,
    *,
    label: str,
    result: ValidationResult,
) -> None:
    location = "$.suiteExpectations"
    if not isinstance(value, dict):
        result.errors.append(f"{label}:{location}: must be an object")
        return
    for field_name in ("requiredSignals", "prohibitedSignals"):
        if not _string_list(value.get(field_name)):
            result.errors.append(
                f"{label}:{location}.{field_name}: must be a non-empty string array"
            )
    if not _repository_state(value.get("repositoryState")):
        result.errors.append(
            f"{label}:{location}.repositoryState: must be a non-empty string or string array"
        )


def _command_path_is_unsafe(value: str) -> bool:
    """Recognize unsafe direct or option-attached command path values."""

    if not value:
        return False
    normalized = value.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    return bool(
        value.startswith(("/", "\\", "~"))
        or PureWindowsPath(value).is_absolute()
        or re.match(r"^[A-Za-z]:", value)
        or ".." in parts
        or any(part.lower() == ".git" for part in parts)
    )


def _command_path_candidates(argument: str) -> list[str]:
    """Return direct and recognized option-attached path candidates."""

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


def _validate_argv(
    argv: object,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> None:
    if not _string_list(argv):
        result.errors.append(f"{label}:{location}: argv must be a non-empty string array")
        return
    assert isinstance(argv, list)

    executable = argv[0].lower()
    if executable not in PYTHON_COMMANDS | DOTNET_COMMANDS:
        result.errors.append(f"{label}:{location}[0]: command family is not permitted")
        return

    for index, argument in enumerate(argv):
        assert isinstance(argument, str)
        argument_location = f"{location}[{index}]"
        if _contains_control_characters(argument) or SHELL_OPERATOR.search(argument):
            result.errors.append(f"{label}:{argument_location}: command argument contains shell syntax")
        path_candidates = _command_path_candidates(argument)
        if any(_command_path_is_unsafe(candidate) for candidate in path_candidates):
            result.errors.append(
                f"{label}:{argument_location}: command arguments must not use unsafe paths"
            )

    if executable in PYTHON_COMMANDS:
        lowered = [argument.lower() for argument in argv[1:]]
        inline_execution = any(
            argument == "-"
            or argument.startswith("-c")
            or argument.startswith("--command")
            or bool(re.fullmatch(r"-[a-z]*c", argument))
            for argument in lowered
        )
        if inline_execution:
            result.errors.append(f"{label}:{location}: inline or stdin Python execution is not permitted")
        for index, argument in enumerate(lowered[:-1]):
            module_root = lowered[index + 1].split(".", 1)[0]
            if argument == "-m" and module_root in FORBIDDEN_PYTHON_MODULES:
                result.errors.append(f"{label}:{location}: Python installer operations are not permitted")
        if lowered and Path(lowered[0]).name == "setup.py" and "install" in lowered[1:]:
            result.errors.append(f"{label}:{location}: Python installer operations are not permitted")
    else:
        operations = {argument.lower() for argument in argv[1:]}
        restore_switch = any(
            argument.lower().lstrip("-/").split(":", 1)[0].split("=", 1)[0]
            == "restore"
            for argument in argv[1:]
        )
        if operations & FORBIDDEN_DOTNET_OPERATIONS or restore_switch:
            result.errors.append(f"{label}:{location}: .NET installer or mutating setup operations are not permitted")


def _validate_verification_commands(
    value: object,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, dict):
        result.errors.append(f"{label}:{location}: verificationCommands must be an object")
        return
    for phase in ("before", "after"):
        commands = value.get(phase)
        phase_location = f"{location}.{phase}"
        if not isinstance(commands, list) or not commands:
            result.errors.append(f"{label}:{phase_location}: must be a non-empty command array")
            continue
        for index, command in enumerate(commands):
            command_location = f"{phase_location}[{index}]"
            if not isinstance(command, dict):
                result.errors.append(f"{label}:{command_location}: command must be an object")
                continue
            if not _nonempty_string(command.get("purpose")):
                result.errors.append(f"{label}:{command_location}.purpose: must be a non-empty string")
            _validate_argv(
                command.get("argv"),
                label=label,
                location=f"{command_location}.argv",
                result=result,
            )


def _validate_behavioral_case(
    case: object,
    *,
    suite_directory: Path,
    label: str,
    location: str,
    result: ValidationResult,
) -> str | None:
    if not isinstance(case, dict):
        result.errors.append(f"{label}:{location}: behavioral case must be an object")
        return None
    case_id = case.get("id")
    if not isinstance(case_id, str) or not SLUG.fullmatch(case_id):
        result.errors.append(f"{label}:{location}.id: must be a lowercase slug")
        valid_id = None
    else:
        valid_id = case_id
    for field_name in ("description", "prompt"):
        if not _nonempty_string(case.get(field_name)):
            result.errors.append(f"{label}:{location}.{field_name}: must be a non-empty string")
    if "fixture" not in case:
        result.errors.append(f"{label}:{location}.fixture: is required")
    else:
        _validate_fixture(
            case["fixture"],
            suite_directory=suite_directory,
            label=label,
            location=f"{location}.fixture",
            result=result,
        )
    _validate_evidence_object(
        case.get("expected"),
        label=label,
        location=f"{location}.expected",
        result=result,
    )
    if "verificationCommands" in case:
        _validate_verification_commands(
            case["verificationCommands"],
            label=label,
            location=f"{location}.verificationCommands",
            result=result,
        )
    return valid_id


def _normalize_owner(owner: str) -> str:
    return owner[1:] if owner.startswith("$") else owner


def _validate_trigger_case(
    case: object,
    *,
    suite_slug: str,
    skill_slugs: set[str],
    label: str,
    location: str,
    result: ValidationResult,
) -> tuple[str | None, bool | None]:
    if not isinstance(case, dict):
        result.errors.append(f"{label}:{location}: trigger case must be an object")
        return None, None
    case_id = case.get("id")
    if not isinstance(case_id, str) or not SLUG.fullmatch(case_id):
        result.errors.append(f"{label}:{location}.id: must be a lowercase slug")
        valid_id = None
    else:
        valid_id = case_id
    if not _nonempty_string(case.get("prompt")):
        result.errors.append(f"{label}:{location}.prompt: must be a non-empty string")
    activation = case.get("expectActivation")
    if type(activation) is not bool:
        result.errors.append(f"{label}:{location}.expectActivation: must be a boolean")
        activation_value = None
    else:
        activation_value = activation

    if "expectedOwner" in case:
        owner = case["expectedOwner"]
        if not _nonempty_string(owner):
            result.errors.append(f"{label}:{location}.expectedOwner: must be a non-empty string")
        else:
            assert isinstance(owner, str)
            normalized = _normalize_owner(owner)
            if normalized not in skill_slugs and owner not in PROVISIONAL_OWNERS:
                result.errors.append(f"{label}:{location}.expectedOwner: owner is not recognized")
            elif activation_value is True and normalized != suite_slug:
                result.errors.append(f"{label}:{location}.expectedOwner: positive trigger must name its suite")
            elif activation_value is False and normalized == suite_slug:
                result.errors.append(f"{label}:{location}.expectedOwner: negative trigger must not name its suite")
    return valid_id, activation_value


def _validate_live_case(
    case: object,
    *,
    suite_directory: Path,
    label: str,
    location: str,
    result: ValidationResult,
) -> str | None:
    if not isinstance(case, dict):
        result.errors.append(f"{label}:{location}: live case must be an object")
        return None
    case_id = case.get("id")
    if not isinstance(case_id, str) or not SLUG.fullmatch(case_id):
        result.errors.append(f"{label}:{location}.id: must be a lowercase slug")
        valid_id = None
    else:
        valid_id = case_id

    if "authorizationRequired" in case:
        if type(case["authorizationRequired"]) is not bool:
            result.errors.append(
                f"{label}:{location}.authorizationRequired: must be a boolean"
            )
        elif case["authorizationRequired"] is not True:
            result.errors.append(
                f"{label}:{location}.authorizationRequired: must be true when present"
            )
    if (
        "authorization" in case
        and case["authorization"] != "separate-explicit-approval-required"
    ):
        result.errors.append(
            f"{label}:{location}.authorization: must require separate explicit approval"
        )
    authorization_ok = (
        case.get("authorizationRequired") is True
        or case.get("authorization") == "separate-explicit-approval-required"
    )
    if not authorization_ok:
        result.errors.append(f"{label}:{location}: live case requires separate explicit authorization")

    for field_name in ("enabledByDefault", "trackOutput"):
        if field_name in case and type(case[field_name]) is not bool:
            result.errors.append(f"{label}:{location}.{field_name}: must be a boolean")
        elif case.get(field_name) is True:
            result.errors.append(f"{label}:{location}.{field_name}: must not be true for a live case")

    signal_fields = [field_name for field_name in ("requiredSignals", "expectedSignals") if field_name in case]
    if not signal_fields:
        result.errors.append(f"{label}:{location}: live case requires requiredSignals or expectedSignals")
    for field_name in signal_fields:
        if not _string_list(case[field_name]):
            result.errors.append(f"{label}:{location}.{field_name}: must be a non-empty string array")
    if "prohibitedSignals" in case and not _string_list(case["prohibitedSignals"]):
        result.errors.append(f"{label}:{location}.prohibitedSignals: must be a non-empty string array")

    if "fixture" in case:
        _validate_fixture(
            case["fixture"],
            suite_directory=suite_directory,
            label=label,
            location=f"{location}.fixture",
            result=result,
        )
    return valid_id


def _validate_manifest(
    manifest: object,
    *,
    suite_slug: str,
    suite_directory: Path,
    skill_slugs: set[str],
    label: str,
    result: ValidationResult,
) -> None:
    if not isinstance(manifest, dict):
        result.errors.append(f"{label}:$: manifest must contain a JSON object")
        return

    missing = REQUIRED_TOP_LEVEL_FIELDS - set(manifest)
    for field_name in sorted(missing):
        result.errors.append(f"{label}:$.{field_name}: required top-level field is missing")
    unknown_fields = sorted(set(manifest) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown_fields:
        result.errors.append(
            f"{label}:$.<field>: manifest contains {len(unknown_fields)} "
            "unsupported top-level field(s)"
        )

    if type(manifest.get("schemaVersion")) is not int or manifest.get("schemaVersion") != SCHEMA_VERSION:
        result.errors.append(f"{label}:$.schemaVersion: must be integer 1")
    if "suite" in manifest and manifest["suite"] != suite_slug:
        result.errors.append(f"{label}:$.suite: must match the evaluation directory")
    _validate_suite_expectations(
        manifest.get("suiteExpectations"),
        label=label,
        result=result,
    )

    seen_ids: dict[str, str] = {}
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        result.errors.append(f"{label}:$.cases: must be a non-empty array")
        case_items: list[object] = []
    else:
        case_items = cases
        result.case_count += len(cases)
    for index, case in enumerate(case_items):
        location = f"$.cases[{index}]"
        case_id = _validate_behavioral_case(
            case,
            suite_directory=suite_directory,
            label=label,
            location=location,
            result=result,
        )
        if case_id is not None:
            if case_id in seen_ids:
                result.errors.append(f"{label}:{location}.id: ID duplicates another case in this suite")
            else:
                seen_ids[case_id] = location

    triggers = manifest.get("triggerCases")
    if not isinstance(triggers, list) or not triggers:
        result.errors.append(f"{label}:$.triggerCases: must be a non-empty array")
        trigger_items: list[object] = []
    else:
        trigger_items = triggers
        result.trigger_count += len(triggers)
    positive_count = 0
    negative_count = 0
    for index, trigger in enumerate(trigger_items):
        location = f"$.triggerCases[{index}]"
        case_id, activation = _validate_trigger_case(
            trigger,
            suite_slug=suite_slug,
            skill_slugs=skill_slugs,
            label=label,
            location=location,
            result=result,
        )
        positive_count += activation is True
        negative_count += activation is False
        if case_id is not None:
            if case_id in seen_ids:
                result.errors.append(f"{label}:{location}.id: ID duplicates another case in this suite")
            else:
                seen_ids[case_id] = location
    if trigger_items and not positive_count:
        result.errors.append(f"{label}:$.triggerCases: must contain at least one positive trigger")
    if trigger_items and not negative_count:
        result.errors.append(f"{label}:$.triggerCases: must contain at least one negative trigger")

    live_cases = manifest.get("liveCases", [])
    if not isinstance(live_cases, list):
        result.errors.append(f"{label}:$.liveCases: must be an array when present")
        live_items: list[object] = []
    else:
        live_items = live_cases
        result.live_count += len(live_cases)
    for index, live_case in enumerate(live_items):
        location = f"$.liveCases[{index}]"
        case_id = _validate_live_case(
            live_case,
            suite_directory=suite_directory,
            label=label,
            location=location,
            result=result,
        )
        if case_id is not None:
            if case_id in seen_ids:
                result.errors.append(f"{label}:{location}.id: ID duplicates another case in this suite")
            else:
                seen_ids[case_id] = location

    _validate_known_paths(manifest, label=label, location="$", result=result)
    for location, text in _walk_strings(manifest):
        if _contains_personal_home(text):
            result.errors.append(f"{label}:{location}: contains a personal-home absolute path")


def _load_skill_slugs(root: Path, result: ValidationResult) -> set[str]:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        result.fatal_errors.append("skills/ is unavailable or is not a real directory")
        return set()
    try:
        if _is_link_or_reparse(skills_root):
            result.fatal_errors.append("skills/ is unavailable or is not a real directory")
            return set()
        entries = sorted(skills_root.iterdir(), key=lambda path: path.name)
    except (OSError, PathInspectionError) as error:
        result.fatal_errors.append(f"skills/ could not be inspected ({error.__class__.__name__})")
        return set()

    skill_slugs: set[str] = set()
    for entry in entries:
        try:
            linked = _is_link_or_reparse(entry)
        except PathInspectionError as error:
            result.fatal_errors.append(
                f"skills/<entry> could not be inspected ({error})"
            )
            continue
        if (
            not linked
            and entry.is_dir()
            and SLUG.fullmatch(entry.name)
            and (entry / "SKILL.md").is_file()
        ):
            skill_slugs.add(entry.name)
    return skill_slugs


def validate_repository(root: Path) -> ValidationResult:
    """Validate every immediate evaluation manifest beneath *root*."""

    result = ValidationResult()
    skill_slugs = _load_skill_slugs(root, result)
    evals_root = root / "evals"
    if not evals_root.is_dir():
        result.fatal_errors.append("evals/ is unavailable or is not a real directory")
        return result
    try:
        if _is_link_or_reparse(evals_root):
            result.fatal_errors.append("evals/ is unavailable or is not a real directory")
            return result
        suite_directories = sorted(
            (
                entry
                for entry in evals_root.iterdir()
                if not entry.name.startswith(".")
                and entry.name != "__pycache__"
                and (_is_link_or_reparse(entry) or entry.is_dir())
            ),
            key=lambda path: path.name,
        )
    except (OSError, PathInspectionError) as error:
        result.fatal_errors.append(f"evals/ could not be inspected ({error.__class__.__name__})")
        return result

    for suite_directory in suite_directories:
        safe_slug = suite_directory.name if SLUG.fullmatch(suite_directory.name) else "<invalid-suite>"
        label = f"evals/{safe_slug}/cases.json"
        if not SLUG.fullmatch(suite_directory.name):
            result.errors.append(f"{label}:$: evaluation directory must use a lowercase slug")
        try:
            linked_suite = _is_link_or_reparse(suite_directory)
        except PathInspectionError as error:
            result.fatal_errors.append(
                f"{label}:$: evaluation directory could not be inspected ({error})"
            )
            continue
        if linked_suite:
            result.errors.append(f"{label}:$: evaluation directory must not be a link or reparse point")
            continue
        manifest_path = suite_directory / "cases.json"
        try:
            linked_manifest = _is_link_or_reparse(manifest_path)
        except PathInspectionError as error:
            result.fatal_errors.append(
                f"{label}:$: cases.json could not be inspected ({error})"
            )
            continue
        if linked_manifest:
            result.errors.append(f"{label}:$: cases.json must not be a link or reparse point")
            continue
        if not manifest_path.is_file():
            result.errors.append(f"{label}:$: cases.json is missing")
            continue
        try:
            text = manifest_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            result.fatal_errors.append(f"{label}:$: could not read UTF-8 JSON ({error.__class__.__name__})")
            continue
        try:
            manifest = json.loads(text)
        except json.JSONDecodeError as error:
            result.fatal_errors.append(
                f"{label}:$: invalid JSON at line {error.lineno}, column {error.colno}"
            )
            continue
        result.suite_count += 1
        _validate_manifest(
            manifest,
            suite_slug=suite_directory.name,
            suite_directory=suite_directory,
            skill_slugs=skill_slugs,
            label=label,
            result=result,
        )

    if not suite_directories:
        result.fatal_errors.append("evals/ contains no evaluation suites")
    return result


def _print_result(result: ValidationResult) -> None:
    for diagnostic in sorted(set(result.fatal_errors + result.errors)):
        print(f"ERROR: {diagnostic}")
    counts = (
        f"{result.suite_count} suites, {result.case_count} cases, "
        f"{result.trigger_count} triggers, {result.live_count} live cases"
    )
    if result.ok:
        print(f"PASS: eval manifests are valid ({counts})")
    elif result.fatal_errors:
        print(f"FAIL: eval manifest inspection failed ({counts})")
    else:
        print(f"FAIL: eval manifests have {len(set(result.errors))} error(s) ({counts})")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the common contract shared by evals/*/cases.json manifests."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of evals/)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        root = arguments.root.resolve(strict=True)
    except OSError as error:
        print(f"ERROR: repository root is unavailable ({error.__class__.__name__})")
        return 2
    if not root.is_dir():
        print("ERROR: repository root must be a directory")
        return 2

    result = validate_repository(root)
    _print_result(result)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
