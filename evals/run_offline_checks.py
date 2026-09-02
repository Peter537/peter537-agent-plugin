#!/usr/bin/env python3
"""Run the repository's deterministic, dependency-free offline checks.

The runner is deliberately conservative. It validates repository-owned text,
calls only fixed maintenance commands, suppresses child output, and verifies
that the Git-visible repository state is byte-identical when it finishes. It
does not execute commands declared by eval manifests, materialize fixtures, or
perform model, network, runtime, installation, MCP, or release checks.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import sys
import tempfile
import tokenize
from typing import Callable, Iterable, Mapping, Sequence
import unicodedata
from urllib.parse import unquote_to_bytes

_METADATA_BOOTSTRAP_FAILED = False
try:
    if __package__:
        from evals.maintenance_metadata import (
            BoundedYamlParseError,
            parse_bounded_yaml as _parse_bounded_yaml,
        )
    else:
        _metadata_path = Path(__file__).with_name("maintenance_metadata.py")
        _metadata_spec = importlib.util.spec_from_file_location(
            "_p537_offline_maintenance_metadata",
            _metadata_path,
        )
        if _metadata_spec is None or _metadata_spec.loader is None:
            raise ImportError
        _metadata_module = importlib.util.module_from_spec(_metadata_spec)
        _metadata_spec.loader.exec_module(_metadata_module)
        BoundedYamlParseError = _metadata_module.BoundedYamlParseError
        _parse_bounded_yaml = _metadata_module.parse_bounded_yaml
except Exception:
    _METADATA_BOOTSTRAP_FAILED = True

    class BoundedYamlParseError(ValueError):
        """The shared maintenance parser could not be loaded safely."""

        def __init__(self, code: str) -> None:
            super().__init__(code)
            self.code = code

    def _parse_bounded_yaml(_text: str) -> dict[str, object]:
        raise BoundedYamlParseError("metadata-bootstrap")


CHILD_TIMEOUT_SECONDS = 120
RECURSION_GUARD_ENV = "P537_OFFLINE_CHECKS_ACTIVE"

_TRUSTED_INFRASTRUCTURE_CODES = {
    "child-launch",
    "child-result",
    "child-runner",
    "child-timeout",
    "directory-inspection",
    "evals-discovery",
    "file-read",
    "git-command",
    "git-index",
    "git-output",
    "git-root",
    "linked-repository-path",
    "path-inspection",
    "execution-race",
    "root-unavailable",
    "temporary-storage",
    "test-discovery",
    "unsafe-repository-path",
    "unsafe-root",
    "unsafe-temporary-root",
    "unsupported-repository-entry",
}

_BUILD_OR_CACHE_PARTS = {
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "bin",
    "build",
    "dist",
    "node_modules",
    "obj",
    "out",
    "target",
    "venv",
}
_EXTERNAL_SCHEMES = {
    "app",
    "codex",
    "data",
    "ftp",
    "http",
    "https",
    "mailto",
    "plugin",
    "skill",
    "tel",
}
_HEADING = re.compile(r"^[ ]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_REFERENCE_DEFINITION = re.compile(
    r"^[ ]{0,3}\[([^\]\n]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))",
    flags=re.MULTILINE,
)
_REFERENCE_USE = re.compile(r"(?<!\\)!?\[([^\]\n]+)\]\[([^\]\n]*)\]")
_CUSTOM_HEADING_ID = re.compile(r"\s*\{#([A-Za-z][A-Za-z0-9_.:-]*)\}\s*$")
_SENSITIVE_PATH_COMPONENT = re.compile(
    r"(?i)(?:secret|token|password|credential|canary|private)"
)
_STATE_SENTINELS = {
    "<HEAD>",
    "<git-status>",
    "<index>",
    "<refs>",
    "<repository-config>",
    "<symbolic-ref>",
    "<tracked-paths>",
    "<untracked-paths>",
}


class InfrastructureError(RuntimeError):
    """A safe, reliable check could not be performed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ContentValidationError(ValueError):
    """Repository content is outside a bounded static contract."""


def _safe_infrastructure_code(error: InfrastructureError) -> str:
    """Return only runner-authored diagnostic codes, never injected values."""

    return (
        error.code
        if error.code in _TRUSTED_INFRASTRUCTURE_CODES
        else "child-runner"
    )


class DuplicateJsonKey(ContentValidationError):
    """A JSON object contains a duplicate key."""


@dataclass(frozen=True)
class ChildResult:
    """Redaction-friendly result from a fixed child process."""

    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class RepositoryState:
    """Git-visible repository state captured without exposing file content."""

    status: str
    head_commit: str
    symbolic_head: str
    refs_digest: str
    index_digest: str
    repository_config_digest: str
    tracked_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    paths: tuple[str, ...]
    digests: tuple[tuple[str, str], ...]


@dataclass
class RunCounts:
    repository_files: int = 0
    eval_suites: int = 0
    materializers: int = 0
    maintenance_tests: int = 0
    distributed_test_suites: int = 0


@dataclass
class RunResult:
    """Structured output and status for one offline run."""

    lines: list[str] = field(default_factory=list)
    counts: RunCounts = field(default_factory=RunCounts)
    has_failure: bool = False
    has_infrastructure_failure: bool = False

    @property
    def exit_code(self) -> int:
        if self.has_infrastructure_failure:
            return 2
        return 1 if self.has_failure else 0

    def pass_check(self, stage: str, detail: str) -> None:
        self.lines.append(f"PASS: {stage}: {detail}")

    def fail_check(self, stage: str, detail: str) -> None:
        self.has_failure = True
        self.lines.append(f"FAIL: {stage}: {detail}")

    def block_check(
        self, stage: str, detail: str, *, infrastructure: bool = True
    ) -> None:
        self.has_failure = True
        self.has_infrastructure_failure |= infrastructure
        self.lines.append(f"BLOCKED: {stage}: {detail}")

    def finish(self) -> None:
        counts = self.counts
        summary = (
            f"{counts.repository_files} files, {counts.eval_suites} eval suites, "
            f"{counts.materializers} materializers, "
            f"{counts.maintenance_tests} maintenance test modules, "
            f"{counts.distributed_test_suites} distributed test suites"
        )
        if self.exit_code == 2:
            self.lines.append(f"BLOCKED: offline checks could not complete ({summary})")
        elif self.exit_code == 1:
            self.lines.append(f"FAIL: offline checks found errors ({summary})")
        else:
            self.lines.append(f"PASS: offline checks completed ({summary})")


ChildRunner = Callable[..., ChildResult]


def run_child(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int = CHILD_TIMEOUT_SECONDS,
) -> ChildResult:
    """Run one fixed argv without a shell and without inheriting stdin."""

    try:
        completed = subprocess.run(
            [str(argument) for argument in argv],
            cwd=str(cwd),
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise InfrastructureError("child-timeout") from error
    except (OSError, UnicodeError, ValueError) as error:
        raise InfrastructureError("child-launch") from error
    return ChildResult(completed.returncode, completed.stdout, completed.stderr)


def is_link_or_reparse(path: Path) -> bool:
    """Return whether *path* is a symbolic link or Windows reparse point."""

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise InfrastructureError("path-inspection") from error
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & reparse_flag)


def _child_environment() -> dict[str, str]:
    # Do not pass arbitrary parent credentials or service configuration to
    # repository-owned checks. Keep only the small process/runtime surface
    # needed to start Python, Git, and temporary-directory based tests.
    inherited = {key.casefold(): (key, value) for key, value in os.environ.items()}
    environment: dict[str, str] = {}
    for requested in (
        "COMSPEC",
        "LANG",
        "LC_ALL",
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "WINDIR",
    ):
        item = inherited.get(requested.casefold())
        if item is not None:
            environment[item[0]] = item[1]
    environment.update(
        {
            "CLICOLOR": "0",
            "FORCE_COLOR": "0",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
            RECURSION_GUARD_ENV: "1",
        }
    )
    return environment


def _invoke_child(
    child_runner: ChildRunner,
    argv: Sequence[str],
    *,
    root: Path,
    environment: Mapping[str, str],
    timeout: int,
) -> ChildResult:
    try:
        result = child_runner(
            tuple(str(argument) for argument in argv),
            cwd=root,
            env=environment,
            timeout=timeout,
        )
    except InfrastructureError:
        raise
    except Exception as error:  # An injected runner is also an infrastructure seam.
        raise InfrastructureError("child-runner") from error
    try:
        return ChildResult(
            int(result.returncode), str(result.stdout), str(result.stderr)
        )
    except (AttributeError, TypeError, ValueError) as error:
        raise InfrastructureError("child-result") from error


def _run_git(
    root: Path,
    arguments: Sequence[str],
    *,
    child_runner: ChildRunner,
    environment: Mapping[str, str],
    timeout: int,
) -> str:
    result = _invoke_child(
        child_runner,
        ("git", *arguments),
        root=root,
        environment=environment,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise InfrastructureError("git-command")
    return result.stdout


def _prepare_root(path: Path) -> Path:
    if any(part == ".." for part in path.parts):
        raise InfrastructureError("unsafe-root")
    candidate = path if path.is_absolute() else Path.cwd() / path
    if is_link_or_reparse(candidate):
        raise InfrastructureError("unsafe-root")
    try:
        root = candidate.resolve(strict=True)
    except OSError as error:
        raise InfrastructureError("root-unavailable") from error
    if not root.is_dir() or is_link_or_reparse(root):
        raise InfrastructureError("root-unavailable")
    return root


def _split_nul(output: str) -> tuple[str, ...]:
    if not output:
        return ()
    if not output.endswith("\0"):
        raise InfrastructureError("git-output")
    return tuple(item for item in output[:-1].split("\0") if item)


def _normalize_relative(raw: str) -> str:
    if not raw or "\0" in raw or "\r" in raw or "\n" in raw or "\\" in raw:
        raise InfrastructureError("unsafe-repository-path")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise InfrastructureError("unsafe-repository-path")
    if ".git" in pure.parts:
        raise InfrastructureError("unsafe-repository-path")
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in raw):
        raise InfrastructureError("unsafe-repository-path")
    return pure.as_posix()


def safe_diagnostic_path(relative: str) -> str:
    """Render a repository-relative path without exposing sensitive tokens."""

    if relative in _STATE_SENTINELS:
        return relative
    try:
        normalized = _normalize_relative(relative)
    except InfrastructureError:
        return "<redacted-path>"
    rendered: list[str] = []
    for component in PurePosixPath(normalized).parts:
        compact = re.sub(r"[^A-Za-z0-9]", "", component)
        high_entropy = (
            bool(re.fullmatch(r"[A-Fa-f0-9]{16,}", compact))
            or (
                len(compact) >= 24
                and any(character.isalpha() for character in compact)
                and any(character.isdigit() for character in compact)
                and (
                    any(character.isupper() for character in compact)
                    or len(set(compact.casefold())) >= 12
                )
            )
        )
        if _SENSITIVE_PATH_COMPONENT.search(component) or high_entropy:
            rendered.append("<redacted>")
        else:
            rendered.append(component)
    return PurePosixPath(*rendered).as_posix()


def _safe_suite_label(suite: str) -> str:
    rendered = safe_diagnostic_path(suite)
    return rendered if "/" not in rendered else "<redacted-suite>"


def _exact_child(parent: Path, expected: str) -> Path | None:
    try:
        with os.scandir(parent) as entries:
            matches = [entry.name for entry in entries if entry.name.casefold() == expected.casefold()]
    except OSError as error:
        raise InfrastructureError("path-inspection") from error
    if expected not in matches:
        if matches:
            raise ContentValidationError("path-casing")
        return None
    return parent / expected


def resolve_repository_path(
    root: Path, relative: str, *, missing_ok: bool = False
) -> Path | None:
    """Resolve a root-relative path without following links or case aliases."""

    normalized = _normalize_relative(relative)
    current = root
    for index, component in enumerate(PurePosixPath(normalized).parts):
        child = _exact_child(current, component)
        if child is None:
            if missing_ok:
                return None
            raise ContentValidationError("missing-path")
        if is_link_or_reparse(child):
            raise InfrastructureError("linked-repository-path")
        if index < len(PurePosixPath(normalized).parts) - 1 and not child.is_dir():
            raise ContentValidationError("non-directory-parent")
        current = child
    return current


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
    except OSError as error:
        raise InfrastructureError("file-read") from error
    return digest.hexdigest()


def _capture_state(
    root: Path,
    *,
    child_runner: ChildRunner,
    environment: Mapping[str, str],
    timeout: int,
) -> RepositoryState:
    top_level = _run_git(
        root,
        ("rev-parse", "--show-toplevel"),
        child_runner=child_runner,
        environment=environment,
        timeout=timeout,
    ).strip()
    try:
        discovered_root = Path(top_level).resolve(strict=True)
    except OSError as error:
        raise InfrastructureError("git-root") from error
    if os.path.normcase(str(discovered_root)) != os.path.normcase(str(root)):
        raise InfrastructureError("git-root")

    status = _run_git(
        root,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        child_runner=child_runner,
        environment=environment,
        timeout=timeout,
    )
    tracked_paths = tuple(
        sorted(
            {
                _normalize_relative(raw)
                for raw in _split_nul(
                    _run_git(
                        root,
                        ("ls-files", "-z", "--cached"),
                        child_runner=child_runner,
                        environment=environment,
                        timeout=timeout,
                    )
                )
            }
        )
    )
    untracked_paths = tuple(
        sorted(
            {
                _normalize_relative(raw)
                for raw in _split_nul(
                    _run_git(
                        root,
                        ("ls-files", "-z", "--others", "--exclude-standard"),
                        child_runner=child_runner,
                        environment=environment,
                        timeout=timeout,
                    )
                )
            }
        )
    )
    paths = tuple(sorted(set(tracked_paths) | set(untracked_paths)))

    head_commit = _run_git(
        root,
        ("rev-parse", "--verify", "HEAD"),
        child_runner=child_runner,
        environment=environment,
        timeout=timeout,
    ).strip()
    if not re.fullmatch(r"[0-9A-Fa-f]{40,64}", head_commit):
        raise InfrastructureError("git-output")

    symbolic = _invoke_child(
        child_runner,
        ("git", "symbolic-ref", "--quiet", "HEAD"),
        root=root,
        environment=environment,
        timeout=timeout,
    )
    if symbolic.returncode == 0:
        symbolic_head = symbolic.stdout.strip()
        if not symbolic_head.startswith("refs/") or "\n" in symbolic_head:
            raise InfrastructureError("git-output")
    elif symbolic.returncode == 1:
        symbolic_head = "<detached>"
    else:
        raise InfrastructureError("git-command")

    refs_result = _run_git(
        root,
        (
            "for-each-ref",
            "--sort=refname",
            "--format=%(refname)%00%(objectname)%00",
        ),
        child_runner=child_runner,
        environment=environment,
        timeout=timeout,
    )
    refs_digest = hashlib.sha256(refs_result.encode("utf-8")).hexdigest()

    index_location = _run_git(
        root,
        ("rev-parse", "--path-format=absolute", "--git-path", "index"),
        child_runner=child_runner,
        environment=environment,
        timeout=timeout,
    ).strip()
    if not index_location or "\n" in index_location or "\0" in index_location:
        raise InfrastructureError("git-output")
    index_path = Path(index_location)
    if not index_path.is_absolute():
        index_path = root / index_path
    if is_link_or_reparse(index_path):
        raise InfrastructureError("linked-repository-path")
    if not index_path.is_file():
        raise InfrastructureError("git-index")
    index_digest = _hash_file(index_path)

    config_result = _run_git(
        root,
        ("config", "--local", "--null", "--list", "--show-origin"),
        child_runner=child_runner,
        environment=environment,
        timeout=timeout,
    )
    repository_config_digest = hashlib.sha256(
        config_result.encode("utf-8")
    ).hexdigest()

    # Hash each Git-visible file only after all Git metadata has been captured.
    # The commands above run with optional locks disabled and must not refresh
    # the index as a side effect.
    digests: list[tuple[str, str]] = []
    for relative in paths:
        path = resolve_repository_path(root, relative, missing_ok=True)
        if path is None:
            digests.append((relative, "missing"))
        elif path.is_file():
            digests.append((relative, _hash_file(path)))
        elif path.is_dir():
            digests.append((relative, "directory"))
        else:
            raise InfrastructureError("unsupported-repository-entry")
    return RepositoryState(
        status,
        head_commit,
        symbolic_head,
        refs_digest,
        index_digest,
        repository_config_digest,
        tracked_paths,
        untracked_paths,
        paths,
        tuple(digests),
    )


def _check_temporary_storage(root: Path) -> None:
    try:
        with tempfile.TemporaryDirectory(prefix="p537-offline-check-") as directory:
            temporary = Path(directory).resolve(strict=True)
            try:
                temporary.relative_to(root)
            except ValueError:
                pass
            else:
                raise InfrastructureError("unsafe-temporary-root")
            marker = temporary / "write-test"
            marker.write_bytes(b"offline-check")
            marker.unlink()
    except InfrastructureError:
        raise
    except OSError as error:
        raise InfrastructureError("temporary-storage") from error


def _excluded_from_static(relative: str, *, tracked: bool) -> bool:
    parts = PurePosixPath(relative).parts
    if len(parts) >= 4 and parts[0] == "evals" and parts[2] == "fixtures":
        return True
    return not tracked and any(part in _BUILD_OR_CACHE_PARTS for part in parts)


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContentValidationError("utf8") from error


def _reject_duplicate_json(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonKey("duplicate-key")
        value[key] = item
    return value


def validate_json_file(path: Path) -> None:
    text = _load_text(path)
    try:
        json.loads(text, object_pairs_hook=_reject_duplicate_json)
    except (json.JSONDecodeError, DuplicateJsonKey) as error:
        raise ContentValidationError("json") from error


def parse_bounded_yaml(text: str) -> dict[str, object]:
    """Parse bounded YAML while preserving the runner's public error type."""

    try:
        return _parse_bounded_yaml(text)
    except BoundedYamlParseError as error:
        raise ContentValidationError(error.code) from error


def _frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ContentValidationError("frontmatter-missing")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])
    raise ContentValidationError("frontmatter-unterminated")


def validate_yaml_file(path: Path, *, frontmatter: bool) -> None:
    text = _load_text(path)
    parse_bounded_yaml(_frontmatter(text) if frontmatter else text)


def validate_python_file(path: Path, relative: str) -> None:
    try:
        with tokenize.open(path) as stream:
            source = stream.read()
        compile(source, relative, "exec", dont_inherit=True)
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:
        raise ContentValidationError("python") from error


def _blank_fenced_code(text: str) -> str:
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in lines:
        stripped = line.lstrip(" ")
        leading = len(line) - len(stripped)
        marker = re.match(r"(`{3,}|~{3,})", stripped) if leading <= 3 else None
        if fence_character is None and marker:
            token = marker.group(1)
            fence_character = token[0]
            fence_length = len(token)
            output.append("".join("\n" if char == "\n" else " " for char in line))
            continue
        if fence_character is not None:
            closes = re.match(
                rf"{re.escape(fence_character)}{{{fence_length},}}[ \t]*(?:\r?\n)?$",
                stripped,
            )
            output.append("".join("\n" if char == "\n" else " " for char in line))
            if closes:
                fence_character = None
            continue
        output.append(line)
    return "".join(output)


def _blank_markdown_code(text: str) -> str:
    visible = list(_blank_fenced_code(text))
    searchable = "".join(visible)
    index = 0
    while index < len(visible):
        if visible[index] != "`":
            index += 1
            continue
        end_run = index
        while end_run < len(visible) and visible[end_run] == "`":
            end_run += 1
        token = "`" * (end_run - index)
        closing = searchable.find(token, end_run)
        if closing < 0:
            index = end_run
            continue
        for position in range(index, closing + len(token)):
            if visible[position] not in "\r\n":
                visible[position] = " "
        index = closing + len(token)
    return "".join(visible)


def _reference_name(value: str) -> str:
    return " ".join(value.split()).casefold()


def _inline_destinations(text: str) -> list[tuple[int, str]]:
    destinations: list[tuple[int, str]] = []
    index = 0
    while index < len(text):
        opening = text.find("[", index)
        if opening < 0:
            break
        if opening > 0 and text[opening - 1] == "\\":
            index = opening + 1
            continue

        close = opening + 1
        escaped_label = False
        while close < len(text):
            character = text[close]
            if escaped_label:
                escaped_label = False
            elif character == "\\":
                escaped_label = True
            elif character == "]":
                break
            elif character in "\r\n":
                break
            close += 1
        if (
            close >= len(text)
            or text[close] != "]"
            or close + 1 >= len(text)
            or text[close + 1] != "("
        ):
            index = opening + 1
            continue

        marker = close
        cursor = close + 2
        while cursor < len(text) and text[cursor] in " \t\r\n":
            cursor += 1
        if cursor >= len(text):
            break
        if text[cursor] == "<":
            end = cursor + 1
            while end < len(text) and text[end] != ">":
                if text[end] == "\\":
                    end += 1
                end += 1
            if end < len(text):
                destinations.append((text.count("\n", 0, marker) + 1, text[cursor + 1 : end]))
                index = end + 1
                continue
        start = cursor
        depth = 0
        escaped = False
        while cursor < len(text):
            character = text[cursor]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    break
                depth -= 1
            elif character.isspace() and depth == 0:
                break
            cursor += 1
        if cursor > start:
            destinations.append((text.count("\n", 0, marker) + 1, text[start:cursor]))
        index = max(cursor + 1, opening + 1)
    return destinations


def _decode_destination(raw: str) -> str:
    value = raw.strip()
    try:
        value = unquote_to_bytes(value).decode("utf-8", errors="strict")
    except (UnicodeDecodeError, ValueError) as error:
        raise ContentValidationError("encoded-link") from error
    return re.sub(r"\\([\\`*{}\[\]()#+.!_>-])", r"\1", value)


def _heading_ids(text: str) -> set[str]:
    identifiers: set[str] = set()
    counts: dict[str, int] = {}
    for line in text.splitlines():
        match = _HEADING.match(line)
        if not match:
            continue
        title = match.group(2).strip()
        custom = _CUSTOM_HEADING_ID.search(title)
        if custom:
            identifiers.add(custom.group(1))
            title = title[: custom.start()].rstrip()
        title = html.unescape(title)
        title = re.sub(r"[*_~]", "", title)
        title = re.sub(r"<[^>]*>", "", title)
        slug = "".join(
            character
            for character in title.casefold()
            if character.isalnum() or character in {" ", "-", "_"}
        ).replace(" ", "-")
        suffix = counts.get(slug, 0)
        counts[slug] = suffix + 1
        identifiers.add(slug if suffix == 0 else f"{slug}-{suffix}")
    return identifiers


def _is_absolute_destination(value: str) -> bool:
    return (
        value.startswith(("/", "\\", "//"))
        or PureWindowsPath(value).is_absolute()
        or bool(re.match(r"^[A-Za-z]:", value))
    )


def _validate_one_link(
    root: Path,
    source_relative: str,
    source_path: Path,
    destination: str,
) -> None:
    value = _decode_destination(destination)
    if not value:
        raise ContentValidationError("empty-link")
    scheme_match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", value)
    if scheme_match:
        if scheme_match.group(1).casefold() in _EXTERNAL_SCHEMES:
            return
        raise ContentValidationError("unsupported-link-scheme")
    if value.startswith("//"):
        return
    if _is_absolute_destination(value) or "\\" in value:
        raise ContentValidationError("absolute-link")

    path_part, separator, fragment = value.partition("#")
    path_part = path_part.split("?", 1)[0]
    if path_part:
        base = PurePosixPath(source_relative).parent
        combined = base.joinpath(PurePosixPath(path_part))
        parts: list[str] = []
        for part in combined.parts:
            if part in {"", "."}:
                continue
            if part == "..":
                if not parts:
                    raise ContentValidationError("escaping-link")
                parts.pop()
            else:
                parts.append(part)
        if not parts:
            raise ContentValidationError("empty-link")
        target_relative = PurePosixPath(*parts).as_posix()
        target = resolve_repository_path(root, target_relative)
    else:
        target = source_path

    if separator and fragment:
        if not target.is_file() or target.suffix.casefold() not in {".md", ".mdx"}:
            raise ContentValidationError("fragment-target")
        target_text = _blank_fenced_code(_load_text(target))
        try:
            decoded_fragment = unquote_to_bytes(fragment).decode("utf-8", errors="strict")
        except (UnicodeDecodeError, ValueError) as error:
            raise ContentValidationError("encoded-fragment") from error
        if decoded_fragment not in _heading_ids(target_text):
            raise ContentValidationError("missing-fragment")


def validate_markdown_file(root: Path, relative: str, path: Path) -> None:
    text = _blank_markdown_code(_load_text(path))
    definitions: dict[str, tuple[int, str]] = {}
    definition_spans: list[tuple[int, int]] = []
    for match in _REFERENCE_DEFINITION.finditer(text):
        name = _reference_name(match.group(1))
        if name in definitions:
            raise ContentValidationError("duplicate-reference-definition")
        destination = match.group(2) or match.group(3)
        definitions[name] = (text.count("\n", 0, match.start()) + 1, destination)
        definition_spans.append(match.span())

    without_definitions = list(text)
    for start, end in definition_spans:
        for index in range(start, end):
            if without_definitions[index] not in "\r\n":
                without_definitions[index] = " "
    visible = "".join(without_definitions)

    destinations = list(definitions.values())
    destinations.extend(_inline_destinations(visible))
    for _line, destination in destinations:
        _validate_one_link(root, relative, path, destination)

    for match in _REFERENCE_USE.finditer(visible):
        name = _reference_name(match.group(2) or match.group(1))
        if name not in definitions:
            raise ContentValidationError("missing-reference-definition")


def _static_checks(
    root: Path,
    files: Sequence[str],
    tracked_paths: set[str],
    result: RunResult,
) -> set[str]:
    invalid_python: set[str] = set()
    categories: tuple[tuple[str, Callable[[Path, str], None]], ...] = (
        ("json", lambda path, _relative: validate_json_file(path)),
        ("python", lambda path, relative: validate_python_file(path, relative)),
        ("markdown", lambda path, relative: validate_markdown_file(root, relative, path)),
    )
    for category, validator in categories:
        selected = [
            relative
            for relative in files
            if not _excluded_from_static(
                relative, tracked=relative in tracked_paths
            )
            and (
                (category == "json" and relative.casefold().endswith(".json"))
                or (category == "python" and relative.casefold().endswith(".py"))
                or (
                    category == "markdown"
                    and relative.casefold().endswith((".md", ".mdx"))
                )
            )
        ]
        errors: list[str] = []
        for relative in selected:
            path = resolve_repository_path(root, relative)
            assert path is not None
            try:
                validator(path, relative)
            except ContentValidationError:
                errors.append(relative)
                if category == "python":
                    invalid_python.add(relative)
            except InfrastructureError:
                raise
        if errors:
            for relative in sorted(errors):
                result.fail_check(
                    f"static-{category}",
                    f"validation failed for {safe_diagnostic_path(relative)}",
                )
        else:
            result.pass_check(f"static-{category}", f"validated {len(selected)} file(s)")

    yaml_files = [
        relative
        for relative in files
        if not _excluded_from_static(relative, tracked=relative in tracked_paths)
        and (
            relative.casefold().endswith("/skill.md")
            or relative.casefold().endswith("/agents/openai.yaml")
        )
    ]
    yaml_errors: list[str] = []
    for relative in yaml_files:
        path = resolve_repository_path(root, relative)
        assert path is not None
        try:
            validate_yaml_file(path, frontmatter=relative.casefold().endswith("/skill.md"))
        except ContentValidationError:
            yaml_errors.append(relative)
    if yaml_errors:
        for relative in sorted(yaml_errors):
            result.fail_check(
                "static-yaml",
                f"validation failed for {safe_diagnostic_path(relative)}",
            )
    else:
        result.pass_check("static-yaml", f"validated {len(yaml_files)} metadata file(s)")
    return invalid_python


def _safe_directory_entries(path: Path) -> list[Path]:
    try:
        entries = sorted(path.iterdir(), key=lambda item: item.name)
    except OSError as error:
        raise InfrastructureError("directory-inspection") from error
    for entry in entries:
        if is_link_or_reparse(entry):
            raise InfrastructureError("linked-repository-path")
    return entries


@dataclass(frozen=True)
class ExecutionDiscovery:
    suites: tuple[str, ...]
    materializers: tuple[tuple[str, str], ...]
    dual_materializers: tuple[str, ...]
    maintenance_tests: tuple[str, ...]
    distributed_tests: tuple[tuple[str, tuple[str, ...]], ...]

    @property
    def distributed_test_suites(self) -> tuple[str, ...]:
        return tuple(suite for suite, _tests in self.distributed_tests)


def _visible_file(root: Path, relative: str, visible_paths: set[str]) -> bool:
    """Return whether a baseline Git-visible path is a safe, current file."""

    if relative not in visible_paths:
        return False
    path = resolve_repository_path(root, relative, missing_ok=True)
    if path is None:
        raise InfrastructureError("execution-race")
    if not path.is_file():
        raise InfrastructureError("execution-race")
    return True


def discover_execution_surface(
    root: Path, visible_paths: Iterable[str]
) -> ExecutionDiscovery:
    """Discover only executables present in the baseline Git-visible set."""

    evals = root / "evals"
    if not evals.is_dir() or is_link_or_reparse(evals):
        raise InfrastructureError("evals-discovery")
    visible = {_normalize_relative(relative) for relative in visible_paths}
    suites: list[str] = []
    materializers: list[tuple[str, str]] = []
    duals: list[str] = []
    distributed: list[tuple[str, tuple[str, ...]]] = []

    suite_candidates = sorted(
        {
            parts[1]
            for relative in visible
            for parts in (PurePosixPath(relative).parts,)
            if len(parts) == 3
            and parts[0] == "evals"
            and parts[2] == "cases.json"
            and not parts[1].startswith(".")
            and parts[1] != "__pycache__"
        }
    )
    for suite in suite_candidates:
        cases_relative = f"evals/{suite}/cases.json"
        if not _visible_file(root, cases_relative, visible):
            continue
        suites.append(suite)
        aliases = [
            name
            for name in ("materialize_fixtures.py", "materialize_packets.py")
            if _visible_file(root, f"evals/{suite}/{name}", visible)
        ]
        if len(aliases) > 1:
            duals.append(suite)
        elif aliases:
            materializers.append((suite, f"evals/{suite}/{aliases[0]}"))

        test_prefix = f"evals/{suite}/tests/"
        test_files = tuple(
            relative
            for relative in sorted(visible)
            if relative.startswith(test_prefix)
            and PurePosixPath(relative).name.startswith("test")
            and PurePosixPath(relative).suffix == ".py"
            and _visible_file(root, relative, visible)
        )
        if test_files:
            distributed.append((suite, test_files))

    maintenance = tuple(
        relative
        for relative in sorted(visible)
        if len(PurePosixPath(relative).parts) == 2
        and PurePosixPath(relative).parts[0] == "evals"
        and PurePosixPath(relative).name.startswith("test_")
        and PurePosixPath(relative).suffix == ".py"
        and _visible_file(root, relative, visible)
    )
    return ExecutionDiscovery(
        tuple(sorted(suites)),
        tuple(sorted(materializers)),
        tuple(sorted(duals)),
        maintenance,
        tuple(sorted(distributed)),
    )


def _fixed_child_check(
    result: RunResult,
    stage: str,
    argv: Sequence[str],
    *,
    root: Path,
    child_runner: ChildRunner,
    environment: Mapping[str, str],
    timeout: int,
    baseline: RepositoryState,
) -> None:
    try:
        current = _capture_state(
            root,
            child_runner=child_runner,
            environment=environment,
            timeout=timeout,
        )
    except (InfrastructureError, ContentValidationError) as error:
        detail = (
            f"pre-launch inspection unavailable ({_safe_infrastructure_code(error)})"
            if isinstance(error, InfrastructureError)
            else "pre-launch inspection failed safely"
        )
        result.block_check(stage, detail)
        return
    drift = _state_changes(baseline, current)
    if drift:
        result.block_check(
            stage,
            "baseline repository state changed before child launch",
        )
        return
    try:
        child = _invoke_child(
            child_runner,
            argv,
            root=root,
            environment=environment,
            timeout=timeout,
        )
    except InfrastructureError as error:
        result.block_check(
            stage,
            f"child process unavailable ({_safe_infrastructure_code(error)})",
        )
        return
    if child.returncode == 0:
        result.pass_check(stage, "command passed")
    else:
        result.fail_check(stage, f"command returned exit {child.returncode}")


def _state_changes(before: RepositoryState, after: RepositoryState) -> tuple[str, ...]:
    changed: set[str] = set(before.paths) ^ set(after.paths)
    before_digests = dict(before.digests)
    after_digests = dict(after.digests)
    for relative in set(before_digests) & set(after_digests):
        if before_digests[relative] != after_digests[relative]:
            changed.add(relative)
    if before.status != after.status and not changed:
        changed.add("<git-status>")
    if before.head_commit != after.head_commit:
        changed.add("<HEAD>")
    if before.symbolic_head != after.symbolic_head:
        changed.add("<symbolic-ref>")
    if before.refs_digest != after.refs_digest:
        changed.add("<refs>")
    if before.index_digest != after.index_digest:
        changed.add("<index>")
    if before.repository_config_digest != after.repository_config_digest:
        changed.add("<repository-config>")
    if before.tracked_paths != after.tracked_paths:
        changed.add("<tracked-paths>")
    if before.untracked_paths != after.untracked_paths:
        changed.add("<untracked-paths>")
    return tuple(sorted(changed))


def _run_checks_impl(
    root: Path,
    *,
    child_runner: ChildRunner = run_child,
    timeout: int = CHILD_TIMEOUT_SECONDS,
) -> RunResult:
    """Run the bounded offline checks and return redacted structured output."""

    result = RunResult()
    if timeout <= 0:
        result.block_check("configuration", "child timeout must be positive")
        result.finish()
        return result
    try:
        repository = _prepare_root(Path(root))
        environment = _child_environment()
        _check_temporary_storage(repository)
        before = _capture_state(
            repository,
            child_runner=child_runner,
            environment=environment,
            timeout=timeout,
        )
    except InfrastructureError as error:
        result.block_check(
            "repository",
            f"inspection unavailable ({_safe_infrastructure_code(error)})",
        )
        result.finish()
        return result

    result.counts.repository_files = len(before.paths)
    result.pass_check("repository", f"captured {len(before.paths)} Git-visible path(s)")
    existing_files = [relative for relative, digest in before.digests if digest not in {"missing", "directory"}]
    # Executable eligibility requires both Git visibility and baseline file
    # existence. A tracked file already deleted before the run is not an
    # executable; a file that disappears after this snapshot is a blocked race.
    visible_paths = set(existing_files)
    try:
        invalid_python = _static_checks(
            repository,
            existing_files,
            set(before.tracked_paths),
            result,
        )
    except InfrastructureError as error:
        result.block_check(
            "static-analysis",
            f"inspection unavailable ({_safe_infrastructure_code(error)})",
        )
        invalid_python = set()

    fixed_validators = (
        ("repository-layout", "evals/validate_repository_layout.py"),
        ("eval-manifests", "evals/validate_eval_manifests.py"),
    )
    for stage, script in fixed_validators:
        if script in invalid_python:
            result.block_check(stage, "validator failed Python parsing", infrastructure=False)
            continue
        if not _visible_file(repository, script, visible_paths):
            result.block_check(stage, "validator is unavailable")
            continue
        _fixed_child_check(
            result,
            stage,
            (sys.executable, "-B", script, "--root", str(repository)),
            root=repository,
            child_runner=child_runner,
            environment=environment,
            timeout=timeout,
            baseline=before,
        )

    try:
        execution = discover_execution_surface(repository, visible_paths)
    except (InfrastructureError, ContentValidationError) as error:
        detail = (
            f"inspection unavailable ({_safe_infrastructure_code(error)})"
            if isinstance(error, InfrastructureError)
            else "inspection failed safely"
        )
        result.block_check("execution-discovery", detail)
        execution = ExecutionDiscovery((), (), (), (), ())
    result.counts.eval_suites = len(execution.suites)
    result.counts.materializers = len(execution.materializers)
    result.counts.maintenance_tests = len(execution.maintenance_tests)
    result.counts.distributed_test_suites = len(execution.distributed_test_suites)
    if execution.dual_materializers:
        for suite in execution.dual_materializers:
            result.fail_check(
                "execution-discovery",
                f"evals/{_safe_suite_label(suite)} exposes both materializer aliases",
            )
    else:
        result.pass_check(
            "execution-discovery",
            f"found {len(execution.suites)} suites, "
            f"{len(execution.materializers)} materializers, "
            f"{len(execution.maintenance_tests)} maintenance test modules, and "
            f"{len(execution.distributed_test_suites)} distributed test suites",
        )

    for suite, script in execution.materializers:
        stage = f"materializer-list/{_safe_suite_label(suite)}"
        if script in invalid_python:
            result.block_check(stage, "materializer failed Python parsing", infrastructure=False)
            continue
        _fixed_child_check(
            result,
            stage,
            (sys.executable, "-B", script, "--list"),
            root=repository,
            child_runner=child_runner,
            environment=environment,
            timeout=timeout,
            baseline=before,
        )

    for script in execution.maintenance_tests:
        stage = f"maintenance-test/{safe_diagnostic_path(script)}"
        if script in invalid_python:
            result.block_check(stage, "test failed Python parsing", infrastructure=False)
            continue
        _fixed_child_check(
            result,
            stage,
            (sys.executable, "-B", script),
            root=repository,
            child_runner=child_runner,
            environment=environment,
            timeout=timeout,
            baseline=before,
        )

    for suite, test_files in execution.distributed_tests:
        test_root = f"evals/{suite}/tests"
        invalid_test = any(
            relative == test_root or relative.startswith(test_root + "/")
            for relative in invalid_python
        )
        stage = f"distributed-tests/{_safe_suite_label(suite)}"
        if invalid_test:
            result.block_check(stage, "test suite failed Python parsing", infrastructure=False)
            continue
        _fixed_child_check(
            result,
            stage,
            (
                sys.executable,
                "-B",
                "-m",
                "unittest",
                *test_files,
                "-v",
            ),
            root=repository,
            child_runner=child_runner,
            environment=environment,
            timeout=timeout,
            baseline=before,
        )

    try:
        after = _capture_state(
            repository,
            child_runner=child_runner,
            environment=environment,
            timeout=timeout,
        )
    except InfrastructureError as error:
        result.block_check(
            "repository-state",
            f"final inspection unavailable ({_safe_infrastructure_code(error)})",
        )
    else:
        changed = _state_changes(before, after)
        if changed:
            for relative in changed:
                result.fail_check(
                    "repository-state",
                    f"changed during checks: {safe_diagnostic_path(relative)}",
                )
        else:
            result.pass_check("repository-state", "Git-visible state is unchanged")

    result.lines.append(
        "NOT_RUN: external evidence: see docs/verification.md for strict grouping, "
        "bundled validators, external schemas, model/live/runtime checks, "
        "installation, MCP, and release evidence"
    )
    result.finish()
    return result


def run_checks(
    root: Path,
    *,
    child_runner: ChildRunner = run_child,
    timeout: int = CHILD_TIMEOUT_SECONDS,
) -> RunResult:
    """Run checks with a final redacted boundary around all inspection races."""

    if _METADATA_BOOTSTRAP_FAILED:
        result = RunResult()
        result.block_check("metadata", "shared parser is unavailable")
        result.finish()
        return result

    try:
        return _run_checks_impl(
            root,
            child_runner=child_runner,
            timeout=timeout,
        )
    except (InfrastructureError, ContentValidationError):
        result = RunResult()
        result.block_check("repository", "inspection failed safely")
        result.finish()
        return result
    except Exception:
        # Never let an unexpected filesystem race, injected runner failure, or
        # platform-specific parser error disclose an absolute path or payload.
        result = RunResult()
        result.block_check("repository", "unexpected inspection failure")
        result.finish()
        return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic, dependency-free repository checks."
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
        print("BLOCKED: metadata: shared parser is unavailable")
        print("BLOCKED: offline checks could not complete")
        return 2
    if os.environ.get(RECURSION_GUARD_ENV) == "1":
        print("BLOCKED: recursion: offline checks cannot invoke themselves")
        print("BLOCKED: offline checks could not complete")
        return 2
    try:
        run = run_checks(arguments.root)
    except Exception:
        # Keep the CLI boundary redacted even when an embedding test or future
        # refactor replaces the structured run_checks wrapper unexpectedly.
        print("BLOCKED: repository: unexpected inspection failure")
        print("BLOCKED: offline checks could not complete")
        return 2
    for line in run.lines:
        print(line)
    return run.exit_code


if __name__ == "__main__":
    sys.exit(main())
