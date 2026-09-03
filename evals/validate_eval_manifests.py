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
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
from typing import Iterable

_METADATA_BOOTSTRAP_FAILED = False
try:
    if __package__:
        from evals.maintenance_metadata import BoundedYamlParseError, parse_bounded_yaml
    else:
        _metadata_path = Path(__file__).with_name("maintenance_metadata.py")
        _metadata_spec = importlib.util.spec_from_file_location(
            "_p537_eval_maintenance_metadata",
            _metadata_path,
        )
        if _metadata_spec is None or _metadata_spec.loader is None:
            raise ImportError
        _metadata_module = importlib.util.module_from_spec(_metadata_spec)
        _metadata_spec.loader.exec_module(_metadata_module)
        BoundedYamlParseError = _metadata_module.BoundedYamlParseError
        parse_bounded_yaml = _metadata_module.parse_bounded_yaml
except Exception:
    _METADATA_BOOTSTRAP_FAILED = True

    class BoundedYamlParseError(ValueError):
        """The shared maintenance parser could not be loaded safely."""

        def __init__(self, code: str) -> None:
            super().__init__(code)
            self.code = code

    def parse_bounded_yaml(_text: str) -> dict[str, object]:
        raise BoundedYamlParseError("metadata-bootstrap")


SCHEMA_VERSION = 1
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROUTING_ID = re.compile(r"^[a-z0-9]+(?:-+[a-z0-9]+)*$")
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
NON_SKILL_OWNER_KINDS = {
    "browser-workflow": "workflow",
    "incident-response": "workflow",
    "legal-guidance": "workflow",
    "no-skill": "none",
    "ordinary-implementation": "workflow",
    "release-workflow": "workflow",
    "repository-analysis": "workflow",
    "translation-workflow": "workflow",
}
ROUTING_MATRIX_FIELDS = {
    "schemaVersion",
    "nonSkillOwners",
    "invocationCases",
    "boundaries",
    "coverageCases",
}
REQUIRED_COVERAGE_KINDS = {
    "specialist-handoff",
    "progressive-disclosure",
    "full-catalog-collision",
}
CASE_SECTIONS = {"cases", "triggerCases", "liveCases"}
EXPECTED_REQUIRED_FIELDS = {
    "requiredSignals",
    "prohibitedSignals",
    "repositoryState",
}
EXPECTED_OPTIONAL_FIELDS = {"outcome"}
TRIGGER_CASE_FIELDS = {"id", "prompt", "expectActivation", "expectedOwner"}
BEHAVIORAL_ROUTING_FIELDS = {"expectActivation", "expectedOwner"}
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
    "falsePositiveControls",
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
    "allow_implicit_invocation",
    "boundaries",
    "caseRefs",
    "coverageCases",
    "directions",
    "explicitTrigger",
    "from",
    "invocationCases",
    "kind",
    "naturalLanguageTrigger",
    "nonSkillOwners",
    "policy",
    "section",
    "skill",
    "skills",
    "to",
    "triggers",
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
    boundary_count: int = 0

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


def _normalize_signal(value: str) -> str:
    """Normalize a signal for semantic duplicate and contradiction checks."""

    return " ".join(value.split()).casefold()


def _validate_signal_list(
    value: object,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> set[str] | None:
    """Validate and normalize a signal list without disclosing its contents."""

    if not _string_list(value):
        result.errors.append(f"{label}:{location}: must be a non-empty string array")
        return None
    assert isinstance(value, list)
    normalized = [_normalize_signal(item) for item in value]
    if len(normalized) != len(set(normalized)):
        result.errors.append(
            f"{label}:{location}: signals must be unique after whitespace and case normalization"
        )
    return set(normalized)


def _reject_signal_overlap(
    required: set[str] | None,
    prohibited: set[str] | None,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> None:
    """Reject a direct signal contradiction without echoing the signal text."""

    if required is not None and prohibited is not None and required & prohibited:
        result.errors.append(
            f"{label}:{location}: required and prohibited signals must not overlap"
        )


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
    _validate_exact_fields(
        value,
        required=EXPECTED_REQUIRED_FIELDS,
        optional=EXPECTED_OPTIONAL_FIELDS,
        label=label,
        location=location,
        result=result,
    )
    required = _validate_signal_list(
        value.get("requiredSignals"),
        label=label,
        location=f"{location}.requiredSignals",
        result=result,
    )
    prohibited = _validate_signal_list(
        value.get("prohibitedSignals"),
        label=label,
        location=f"{location}.prohibitedSignals",
        result=result,
    )
    _reject_signal_overlap(
        required,
        prohibited,
        label=label,
        location=location,
        result=result,
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
) -> list[tuple[int, str]]:
    location = "$.suiteExpectations"
    if not isinstance(value, dict):
        result.errors.append(f"{label}:{location}: must be an object")
        return []
    required = _validate_signal_list(
        value.get("requiredSignals"),
        label=label,
        location=f"{location}.requiredSignals",
        result=result,
    )
    prohibited = _validate_signal_list(
        value.get("prohibitedSignals"),
        label=label,
        location=f"{location}.prohibitedSignals",
        result=result,
    )
    _reject_signal_overlap(
        required,
        prohibited,
        label=label,
        location=location,
        result=result,
    )
    if not _repository_state(value.get("repositoryState")):
        result.errors.append(
            f"{label}:{location}.repositoryState: must be a non-empty string or string array"
        )

    controls = value.get("falsePositiveControls")
    controls_location = f"{location}.falsePositiveControls"
    if not isinstance(controls, list) or not controls:
        result.errors.append(
            f"{label}:{controls_location}: must be a non-empty behavioral-case ID array"
        )
        return []
    references: list[tuple[int, str]] = []
    seen: set[str] = set()
    for index, control_id in enumerate(controls):
        control_location = f"{controls_location}[{index}]"
        if not isinstance(control_id, str) or not SLUG.fullmatch(control_id):
            result.errors.append(
                f"{label}:{control_location}: must be a behavioral-case ID"
            )
            continue
        if control_id in seen:
            result.errors.append(
                f"{label}:{control_location}: false-positive control ID is duplicated"
            )
        else:
            seen.add(control_id)
        references.append((index, control_id))
    return references


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
    for field_name in sorted(BEHAVIORAL_ROUTING_FIELDS & set(case)):
        result.errors.append(
            f"{label}:{location}.{field_name}: routing fields are not permitted in behavioral cases"
        )
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
    _validate_exact_fields(
        case,
        required=TRIGGER_CASE_FIELDS,
        label=label,
        location=location,
        result=result,
    )
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

    owner = case.get("expectedOwner")
    if not _nonempty_string(owner):
        result.errors.append(f"{label}:{location}.expectedOwner: must be a non-empty string")
    else:
        assert isinstance(owner, str)
        if not SLUG.fullmatch(owner):
            result.errors.append(
                f"{label}:{location}.expectedOwner: must be a canonical bare owner ID"
            )
        elif owner not in skill_slugs and owner not in NON_SKILL_OWNER_KINDS:
            result.errors.append(f"{label}:{location}.expectedOwner: owner is not recognized")
        elif activation_value is True and owner != suite_slug:
            result.errors.append(f"{label}:{location}.expectedOwner: positive trigger must name its suite")
        elif activation_value is False and owner == suite_slug:
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
    positive_signals: list[set[str]] = []
    for field_name in signal_fields:
        normalized = _validate_signal_list(
            case[field_name],
            label=label,
            location=f"{location}.{field_name}",
            result=result,
        )
        if normalized is not None:
            positive_signals.append(normalized)
    prohibited = None
    if "prohibitedSignals" in case:
        prohibited = _validate_signal_list(
            case["prohibitedSignals"],
            label=label,
            location=f"{location}.prohibitedSignals",
            result=result,
        )
    if prohibited is not None:
        for positive in positive_signals:
            _reject_signal_overlap(
                positive,
                prohibited,
                label=label,
                location=location,
                result=result,
            )

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
    control_references = _validate_suite_expectations(
        manifest.get("suiteExpectations"),
        label=label,
        result=result,
    )

    seen_ids: dict[str, str] = {}
    behavioral_ids: set[str] = set()
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
            behavioral_ids.add(case_id)
            if case_id in seen_ids:
                result.errors.append(f"{label}:{location}.id: ID duplicates another case in this suite")
            else:
                seen_ids[case_id] = location

    for control_index, control_id in control_references:
        if control_id not in behavioral_ids:
            result.errors.append(
                f"{label}:$.suiteExpectations.falsePositiveControls[{control_index}]: "
                "must reference a behavioral case in this suite"
            )

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


def _validate_exact_fields(
    value: dict[object, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
    label: str,
    location: str,
    result: ValidationResult,
) -> bool:
    """Validate a closed object shape without disclosing unknown key values."""

    keys = {key for key in value if isinstance(key, str)}
    allowed = required | (optional or set())
    for field_name in sorted(required - keys):
        result.errors.append(f"{label}:{location}.{field_name}: required field is missing")
    unknown_count = sum(
        not isinstance(key, str) or key not in allowed for key in value
    )
    if unknown_count:
        result.errors.append(
            f"{label}:{location}.<field>: contains {unknown_count} unsupported field(s)"
        )
    return not (required - keys) and not unknown_count


def _manifest_case_index(
    manifests: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, dict[str, object]]]]:
    """Build a best-effort index for already structurally validated manifests."""

    index: dict[str, dict[str, dict[str, dict[str, object]]]] = {}
    for suite, manifest in manifests.items():
        sections: dict[str, dict[str, dict[str, object]]] = {}
        for section in CASE_SECTIONS:
            cases: dict[str, dict[str, object]] = {}
            raw_cases = manifest.get(section, [])
            if isinstance(raw_cases, list):
                for case in raw_cases:
                    if (
                        isinstance(case, dict)
                        and isinstance(case.get("id"), str)
                        and case["id"] not in cases
                    ):
                        cases[case["id"]] = case
            sections[section] = cases
        index[suite] = sections
    return index


def _load_invocation_policy(
    root: Path,
    skill_slug: str,
    *,
    label: str,
    location: str,
    result: ValidationResult,
) -> bool | None:
    """Return effective implicit invocation, whose documented default is true."""

    metadata_path = root / "skills" / skill_slug / "agents" / "openai.yaml"
    current = root / "skills" / skill_slug
    for path in (current / "agents", metadata_path):
        if _reject_link_or_inspection_gap(
            path,
            label=label,
            location=location,
            result=result,
        ):
            return None
    if not metadata_path.is_file():
        result.errors.append(
            f"{label}:{location}: agents/openai.yaml is required for invocation validation"
        )
        return None
    try:
        text = metadata_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        result.fatal_errors.append(
            f"{label}:{location}: agents/openai.yaml could not be read "
            f"({error.__class__.__name__})"
        )
        return None
    try:
        metadata = parse_bounded_yaml(text)
    except BoundedYamlParseError:
        result.errors.append(
            f"{label}:{location}: agents/openai.yaml is outside the supported metadata subset"
        )
        return None
    policy = metadata.get("policy")
    if policy is None:
        return True
    if not isinstance(policy, dict):
        result.errors.append(
            f"{label}:{location}: policy must be a mapping when present"
        )
        return None
    implicit = policy.get("allow_implicit_invocation", True)
    if type(implicit) is not bool:
        result.errors.append(
            f"{label}:{location}: allow_implicit_invocation must be a boolean"
        )
        return None
    return implicit


def _skill_mentions(prompt: object) -> list[str]:
    if not isinstance(prompt, str):
        return []
    return re.findall(
        r"(?<![A-Za-z0-9_-])\$([a-z0-9]+(?:-[a-z0-9]+)*)(?![A-Za-z0-9_-])",
        prompt,
    )


def _validate_owner_registry(
    value: object,
    *,
    label: str,
    result: ValidationResult,
) -> None:
    location = "$.nonSkillOwners"
    if not isinstance(value, list):
        result.errors.append(f"{label}:{location}: must be an array")
        return
    seen: set[str] = set()
    ordered_ids: list[str] = []
    for index, item in enumerate(value):
        item_location = f"{location}[{index}]"
        if not isinstance(item, dict):
            result.errors.append(f"{label}:{item_location}: owner must be an object")
            continue
        _validate_exact_fields(
            item,
            required={"id", "kind", "description"},
            label=label,
            location=item_location,
            result=result,
        )
        owner_id = item.get("id")
        kind = item.get("kind")
        if not isinstance(owner_id, str) or owner_id not in NON_SKILL_OWNER_KINDS:
            result.errors.append(f"{label}:{item_location}.id: owner is not registered")
            continue
        ordered_ids.append(owner_id)
        if owner_id in seen:
            result.errors.append(f"{label}:{item_location}.id: owner ID is duplicated")
        seen.add(owner_id)
        if kind != NON_SKILL_OWNER_KINDS[owner_id]:
            result.errors.append(f"{label}:{item_location}.kind: owner kind is incorrect")
        if not _nonempty_string(item.get("description")):
            result.errors.append(
                f"{label}:{item_location}.description: must be a non-empty string"
            )
    if seen != set(NON_SKILL_OWNER_KINDS):
        result.errors.append(
            f"{label}:{location}: must register every canonical non-skill owner exactly once"
        )
    if ordered_ids != sorted(ordered_ids):
        result.errors.append(f"{label}:{location}: owners must be sorted by ID")


def _validate_invocation_cases(
    value: object,
    *,
    root: Path,
    skill_slugs: set[str],
    case_index: dict[str, dict[str, dict[str, dict[str, object]]]],
    label: str,
    result: ValidationResult,
) -> None:
    location = "$.invocationCases"
    if not isinstance(value, list):
        result.errors.append(f"{label}:{location}: must be an array")
        return
    seen: set[str] = set()
    ordered_skills: list[str] = []
    for index, item in enumerate(value):
        item_location = f"{location}[{index}]"
        if not isinstance(item, dict):
            result.errors.append(f"{label}:{item_location}: invocation row must be an object")
            continue
        _validate_exact_fields(
            item,
            required={"skill", "explicitTrigger", "naturalLanguageTrigger"},
            label=label,
            location=item_location,
            result=result,
        )
        skill = item.get("skill")
        if not isinstance(skill, str) or skill not in skill_slugs:
            result.errors.append(f"{label}:{item_location}.skill: skill is not discovered")
            continue
        ordered_skills.append(skill)
        if skill in seen:
            result.errors.append(f"{label}:{item_location}.skill: skill is duplicated")
        seen.add(skill)
        triggers = case_index.get(skill, {}).get("triggerCases", {})
        referenced: dict[str, dict[str, object] | None] = {}
        for field_name in ("explicitTrigger", "naturalLanguageTrigger"):
            trigger_id = item.get(field_name)
            if not isinstance(trigger_id, str) or not SLUG.fullmatch(trigger_id):
                result.errors.append(
                    f"{label}:{item_location}.{field_name}: must be a trigger-case ID"
                )
                referenced[field_name] = None
            else:
                trigger = triggers.get(trigger_id)
                referenced[field_name] = trigger
                if trigger is None:
                    result.errors.append(
                        f"{label}:{item_location}.{field_name}: referenced trigger does not exist"
                    )

        explicit = referenced.get("explicitTrigger")
        if explicit is not None:
            if explicit.get("expectActivation") is not True or explicit.get("expectedOwner") != skill:
                result.errors.append(
                    f"{label}:{item_location}.explicitTrigger: must be a positive trigger owned by its skill"
                )
            mentions = _skill_mentions(explicit.get("prompt"))
            if skill not in mentions or any(mention != skill for mention in mentions):
                result.errors.append(
                    f"{label}:{item_location}.explicitTrigger: prompt must explicitly name only its exact skill"
                )

        natural = referenced.get("naturalLanguageTrigger")
        policy = _load_invocation_policy(
            root,
            skill,
            label=label,
            location=f"{item_location}.naturalLanguageTrigger",
            result=result,
        )
        if natural is not None:
            if _skill_mentions(natural.get("prompt")):
                result.errors.append(
                    f"{label}:{item_location}.naturalLanguageTrigger: prompt must not explicitly name a skill"
                )
            if policy is True and (
                natural.get("expectActivation") is not True
                or natural.get("expectedOwner") != skill
            ):
                result.errors.append(
                    f"{label}:{item_location}.naturalLanguageTrigger: implicit policy requires a positive trigger owned by its skill"
                )
            elif policy is False and (
                natural.get("expectActivation") is not False
                or natural.get("expectedOwner") == skill
            ):
                result.errors.append(
                    f"{label}:{item_location}.naturalLanguageTrigger: explicit-only policy requires a negative trigger owned elsewhere"
                )
    if seen != skill_slugs:
        result.errors.append(
            f"{label}:{location}: must contain exactly one row for every discovered skill"
        )
    if ordered_skills != sorted(ordered_skills):
        result.errors.append(f"{label}:{location}: rows must be sorted by skill")


def _validate_boundaries(
    value: object,
    *,
    skill_slugs: set[str],
    case_index: dict[str, dict[str, dict[str, dict[str, object]]]],
    label: str,
    result: ValidationResult,
) -> None:
    location = "$.boundaries"
    if not isinstance(value, list):
        result.errors.append(f"{label}:{location}: must be an array")
        return
    result.boundary_count = len(value)
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    ordered_pairs: list[tuple[str, str]] = []
    for index, item in enumerate(value):
        item_location = f"{location}[{index}]"
        if not isinstance(item, dict):
            result.errors.append(f"{label}:{item_location}: boundary must be an object")
            continue
        _validate_exact_fields(
            item,
            required={"id", "skills", "directions"},
            label=label,
            location=item_location,
            result=result,
        )
        boundary_id = item.get("id")
        if not isinstance(boundary_id, str) or not ROUTING_ID.fullmatch(boundary_id):
            result.errors.append(f"{label}:{item_location}.id: must be a lowercase routing ID")
        elif boundary_id in seen_ids:
            result.errors.append(f"{label}:{item_location}.id: boundary ID is duplicated")
        else:
            seen_ids.add(boundary_id)
        skills = item.get("skills")
        if (
            not isinstance(skills, list)
            or len(skills) != 2
            or not all(isinstance(skill, str) and skill in skill_slugs for skill in skills)
            or skills[0] == skills[1]
        ):
            result.errors.append(
                f"{label}:{item_location}.skills: must contain two distinct discovered skills"
            )
            continue
        pair = (skills[0], skills[1])
        if list(pair) != sorted(pair):
            result.errors.append(f"{label}:{item_location}.skills: pair must be sorted")
        if pair in seen_pairs:
            result.errors.append(f"{label}:{item_location}.skills: boundary pair is duplicated")
        seen_pairs.add(pair)
        ordered_pairs.append(pair)
        directions = item.get("directions")
        if not isinstance(directions, list) or len(directions) != 2:
            result.errors.append(
                f"{label}:{item_location}.directions: must contain both directional handoffs"
            )
            continue
        expected_directions = ((pair[0], pair[1]), (pair[1], pair[0]))
        seen_directions: set[tuple[str, str]] = set()
        for direction_index, direction in enumerate(directions):
            direction_location = f"{item_location}.directions[{direction_index}]"
            if not isinstance(direction, dict):
                result.errors.append(
                    f"{label}:{direction_location}: direction must be an object"
                )
                continue
            _validate_exact_fields(
                direction,
                required={"from", "to", "triggers"},
                label=label,
                location=direction_location,
                result=result,
            )
            from_skill = direction.get("from")
            to_skill = direction.get("to")
            direction_pair = (from_skill, to_skill)
            if direction_pair != expected_directions[direction_index]:
                result.errors.append(
                    f"{label}:{direction_location}: directions must be ordered from first-to-second and second-to-first"
                )
            if (
                not isinstance(from_skill, str)
                or not isinstance(to_skill, str)
                or from_skill not in pair
                or to_skill not in pair
                or from_skill == to_skill
            ):
                continue
            if direction_pair in seen_directions:
                result.errors.append(
                    f"{label}:{direction_location}: direction is duplicated"
                )
            seen_directions.add(direction_pair)
            trigger_ids = direction.get("triggers")
            if not _string_list(trigger_ids):
                result.errors.append(
                    f"{label}:{direction_location}.triggers: must be a non-empty trigger ID array"
                )
                continue
            assert isinstance(trigger_ids, list)
            if len(set(trigger_ids)) != len(trigger_ids):
                result.errors.append(
                    f"{label}:{direction_location}.triggers: trigger IDs must be unique"
                )
            source_triggers = case_index.get(from_skill, {}).get("triggerCases", {})
            for trigger_index, trigger_id in enumerate(trigger_ids):
                trigger_location = f"{direction_location}.triggers[{trigger_index}]"
                trigger = source_triggers.get(trigger_id)
                if trigger is None:
                    result.errors.append(
                        f"{label}:{trigger_location}: referenced negative trigger does not exist"
                    )
                elif (
                    trigger.get("expectActivation") is not False
                    or trigger.get("expectedOwner") != to_skill
                ):
                    result.errors.append(
                        f"{label}:{trigger_location}: trigger must be negative and owned by the opposite skill"
                    )
    if ordered_pairs != sorted(ordered_pairs):
        result.errors.append(f"{label}:{location}: boundaries must be sorted by skill pair")


def _validate_coverage_cases(
    value: object,
    *,
    skill_slugs: set[str],
    case_index: dict[str, dict[str, dict[str, dict[str, object]]]],
    label: str,
    result: ValidationResult,
) -> None:
    location = "$.coverageCases"
    if not isinstance(value, list):
        result.errors.append(f"{label}:{location}: must be an array")
        return
    seen_ids: set[str] = set()
    kinds: set[str] = set()
    for index, item in enumerate(value):
        item_location = f"{location}[{index}]"
        if not isinstance(item, dict):
            result.errors.append(f"{label}:{item_location}: coverage case must be an object")
            continue
        _validate_exact_fields(
            item,
            required={
                "id",
                "kind",
                "caseRefs",
                "requiredSignals",
                "prohibitedSignals",
            },
            label=label,
            location=item_location,
            result=result,
        )
        coverage_id = item.get("id")
        if not isinstance(coverage_id, str) or not SLUG.fullmatch(coverage_id):
            result.errors.append(f"{label}:{item_location}.id: must be a lowercase slug")
        elif coverage_id in seen_ids:
            result.errors.append(f"{label}:{item_location}.id: coverage ID is duplicated")
        else:
            seen_ids.add(coverage_id)
        kind = item.get("kind")
        if not isinstance(kind, str) or kind not in REQUIRED_COVERAGE_KINDS:
            result.errors.append(f"{label}:{item_location}.kind: coverage kind is not recognized")
        else:
            kinds.add(kind)
        required_signals = _validate_signal_list(
            item.get("requiredSignals"),
            label=label,
            location=f"{item_location}.requiredSignals",
            result=result,
        )
        prohibited_signals = _validate_signal_list(
            item.get("prohibitedSignals"),
            label=label,
            location=f"{item_location}.prohibitedSignals",
            result=result,
        )
        _reject_signal_overlap(
            required_signals,
            prohibited_signals,
            label=label,
            location=item_location,
            result=result,
        )
        refs = item.get("caseRefs")
        if not isinstance(refs, list) or not refs:
            result.errors.append(f"{label}:{item_location}.caseRefs: must be a non-empty array")
            continue
        seen_refs: set[tuple[str, str, str]] = set()
        for ref_index, ref in enumerate(refs):
            ref_location = f"{item_location}.caseRefs[{ref_index}]"
            if not isinstance(ref, dict):
                result.errors.append(f"{label}:{ref_location}: case reference must be an object")
                continue
            _validate_exact_fields(
                ref,
                required={"suite", "section", "id"},
                label=label,
                location=ref_location,
                result=result,
            )
            suite = ref.get("suite")
            section = ref.get("section")
            case_id = ref.get("id")
            if not isinstance(suite, str) or suite not in skill_slugs:
                result.errors.append(f"{label}:{ref_location}.suite: suite is not discovered")
                continue
            if not isinstance(section, str) or section not in CASE_SECTIONS:
                result.errors.append(f"{label}:{ref_location}.section: section is not recognized")
                continue
            if not isinstance(case_id, str) or not SLUG.fullmatch(case_id):
                result.errors.append(f"{label}:{ref_location}.id: must be a case ID")
                continue
            reference = (suite, section, case_id)
            if reference in seen_refs:
                result.errors.append(f"{label}:{ref_location}: case reference is duplicated")
            seen_refs.add(reference)
            if case_id not in case_index.get(suite, {}).get(section, {}):
                result.errors.append(f"{label}:{ref_location}: referenced case does not exist")
    missing_kinds = REQUIRED_COVERAGE_KINDS - kinds
    if missing_kinds:
        result.errors.append(
            f"{label}:{location}: must cover every required coverage kind"
        )


def _validate_routing_matrix(
    matrix: object,
    *,
    root: Path,
    skill_slugs: set[str],
    manifests: dict[str, dict[str, object]],
    label: str,
    result: ValidationResult,
) -> None:
    if not isinstance(matrix, dict):
        result.errors.append(f"{label}:$: routing matrix must contain a JSON object")
        return
    _validate_exact_fields(
        matrix,
        required=ROUTING_MATRIX_FIELDS,
        label=label,
        location="$",
        result=result,
    )
    if type(matrix.get("schemaVersion")) is not int or matrix.get("schemaVersion") != SCHEMA_VERSION:
        result.errors.append(f"{label}:$.schemaVersion: must be integer 1")
    case_index = _manifest_case_index(manifests)
    _validate_owner_registry(matrix.get("nonSkillOwners"), label=label, result=result)
    _validate_invocation_cases(
        matrix.get("invocationCases"),
        root=root,
        skill_slugs=skill_slugs,
        case_index=case_index,
        label=label,
        result=result,
    )
    _validate_boundaries(
        matrix.get("boundaries"),
        skill_slugs=skill_slugs,
        case_index=case_index,
        label=label,
        result=result,
    )
    _validate_coverage_cases(
        matrix.get("coverageCases"),
        skill_slugs=skill_slugs,
        case_index=case_index,
        label=label,
        result=result,
    )
    for location, text in _walk_strings(matrix):
        if _contains_personal_home(text):
            result.errors.append(f"{label}:{location}: contains a personal-home absolute path")


def validate_repository(root: Path) -> ValidationResult:
    """Validate every immediate evaluation manifest beneath *root*."""

    result = ValidationResult()
    if _METADATA_BOOTSTRAP_FAILED:
        result.fatal_errors.append("shared maintenance metadata parser is unavailable")
        return result
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

    manifests: dict[str, dict[str, object]] = {}
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
        if isinstance(manifest, dict):
            manifests[suite_directory.name] = manifest
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

    matrix_path = evals_root / "routing-matrix.json"
    matrix_label = "evals/routing-matrix.json"
    try:
        linked_matrix = _is_link_or_reparse(matrix_path)
    except PathInspectionError as error:
        result.fatal_errors.append(
            f"{matrix_label}:$: routing matrix could not be inspected ({error})"
        )
        return result
    if linked_matrix:
        result.errors.append(
            f"{matrix_label}:$: routing matrix must not be a link or reparse point"
        )
        return result
    if not matrix_path.is_file():
        result.errors.append(f"{matrix_label}:$: routing matrix is missing")
        return result
    try:
        matrix_text = matrix_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        result.fatal_errors.append(
            f"{matrix_label}:$: could not read UTF-8 JSON ({error.__class__.__name__})"
        )
        return result
    try:
        matrix = json.loads(matrix_text)
    except json.JSONDecodeError as error:
        result.fatal_errors.append(
            f"{matrix_label}:$: invalid JSON at line {error.lineno}, column {error.colno}"
        )
        return result
    _validate_routing_matrix(
        matrix,
        root=root,
        skill_slugs=skill_slugs,
        manifests=manifests,
        label=matrix_label,
        result=result,
    )
    return result


def _print_result(result: ValidationResult) -> None:
    for diagnostic in sorted(set(result.fatal_errors + result.errors)):
        print(f"ERROR: {diagnostic}")
    counts = (
        f"{result.suite_count} suites, {result.case_count} cases, "
        f"{result.trigger_count} triggers, {result.live_count} live cases, "
        f"{result.boundary_count} boundaries"
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
    if _METADATA_BOOTSTRAP_FAILED:
        print("ERROR: shared maintenance metadata parser is unavailable")
        return 2
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
