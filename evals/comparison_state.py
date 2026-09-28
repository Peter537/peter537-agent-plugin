"""Private fixture snapshots and conservative ownership checks for comparisons.

These helpers do not sandbox concurrent processes. Callers must stop owned
processes before capturing final state or deleting a bundle, and retain the
ownership token outside agent-controlled files. Markers prevent accidental
cleanup; they are not cryptographic proof of authorization.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import secrets
import shutil
import stat
import subprocess


_CODES = {
    "path-invalid", "path-unavailable", "path-linked", "entry-unsupported",
    "source-overlap", "destination-not-empty", "copy-failed", "copy-drift",
    "git-unavailable", "git-command", "git-output", "git-layout", "git-executable-configuration",
    "workspace-unavailable", "snapshot-invalid", "scope-invalid",
    "owner-invalid", "cleanup-failed",
}
OWNER_MARKER = ".comparison-owner.json"


class StateError(Exception):
    """A safe code without fixture paths, content, or subprocess output."""

    def __init__(self, code: str) -> None:
        self.code = code if code in _CODES else "workspace-unavailable"
        super().__init__("Comparison state operation could not be completed.")


def checked_path(path: Path, must_exist: bool = True) -> Path:
    """Return an absolute path after checking every existing ancestor."""
    try:
        supplied = Path(path)
        if (".." in supplied.parts or "\0" in str(supplied)
                or any(":" in part for part in supplied.parts if part != supplied.anchor)):
            raise StateError("path-invalid")
        # UNC/device paths can leave local storage or bypass ordinary semantics.
        if str(supplied).startswith("\\\\"):
            raise StateError("path-invalid")
        absolute = Path(os.path.abspath(supplied))
        for candidate in (*reversed(absolute.parents), absolute):
            try:
                info = candidate.lstat()
            except FileNotFoundError:
                if candidate == absolute and must_exist:
                    raise StateError("path-unavailable") from None
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                raise StateError("path-linked")
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise StateError("entry-unsupported")
        return absolute.resolve(strict=must_exist)
    except (OSError, ValueError, TypeError):
        raise StateError("path-unavailable") from None


def _within(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def require_external(output: Path, source: Path) -> Path:
    """Require a separate, nonexistent or empty destination; create nothing."""
    destination = checked_path(output, must_exist=False)
    origin = checked_path(source)
    if _within(destination, origin) or _within(origin, destination):
        raise StateError("source-overlap")
    try:
        if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
            raise StateError("destination-not-empty")
    except OSError:
        raise StateError("path-unavailable") from None
    return destination


def _digest_file(path: Path) -> str:
    try:
        with checked_path(path).open("rb") as stream:
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        raise StateError("workspace-unavailable") from None


def tree_identity(root: Path) -> dict[str, dict[str, object]]:
    """Identify every file and empty directory, including ignored and Git data."""
    origin = checked_path(root)
    if not origin.is_dir():
        raise StateError("path-invalid")
    result: dict[str, dict[str, object]] = {}
    pending = [origin]
    try:
        while pending:
            parent = pending.pop()
            for entry in sorted(parent.iterdir()):
                item = checked_path(entry)
                info = item.lstat()
                relative = item.relative_to(origin).as_posix()
                if stat.S_ISDIR(info.st_mode):
                    result[relative] = {"kind": "directory"}
                    pending.append(item)
                elif stat.S_ISREG(info.st_mode):
                    result[relative] = {
                        "kind": "file", "sha256": _digest_file(item),
                        "size": info.st_size, "mode": stat.S_IMODE(info.st_mode),
                    }
                else:
                    raise StateError("entry-unsupported")
    except OSError:
        raise StateError("workspace-unavailable") from None
    return dict(sorted(result.items()))


def copy_tree(source: Path, dest: Path) -> None:
    """Copy complete bytes and metadata with no hardlinks or skipped files."""
    origin = checked_path(source)
    destination = require_external(dest, origin)
    baseline = tree_identity(origin)
    try:
        destination.mkdir(parents=True, exist_ok=True)
        for relative, identity in baseline.items():
            incoming = checked_path(origin / relative)
            outgoing = checked_path(destination / relative, must_exist=False)
            if identity["kind"] == "directory":
                outgoing.mkdir(exist_ok=True)
            else:
                outgoing.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(incoming, outgoing, follow_symlinks=False)
    except OSError:
        raise StateError("copy-failed") from None
    if baseline != tree_identity(origin) or baseline != tree_identity(destination):
        raise StateError("copy-drift")


def _git_environment() -> dict[str, str]:
    permitted = {"comspec", "lang", "lc_all", "path", "pathext", "systemroot", "temp", "tmp", "tmpdir", "windir"}
    environment = {key: value for key, value in os.environ.items() if key.casefold() in permitted}
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1", "LC_ALL": "C",
    })
    return environment


def _git(root: Path, *arguments: str, optional: bool = False) -> str | None:
    command = [
        "git", "--no-optional-locks", "--git-dir", str(root / ".git"),
        "--work-tree", str(root), "-c", "core.fsmonitor=false",
        "-c", "core.hooksPath=" + os.devnull, "-c", "core.untrackedCache=false",
        "-c", "status.renames=false", "-c", "submodule.recurse=false",
        *arguments,
    ]
    try:
        completed = subprocess.run(command, cwd=root, env=_git_environment(),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=30, check=False)
    except FileNotFoundError:
        raise StateError("git-unavailable") from None
    except (OSError, subprocess.SubprocessError):
        raise StateError("git-command") from None
    if completed.returncode != 0:
        if optional and completed.returncode == 1:
            return None
        raise StateError("git-command")
    return completed.stdout.decode("utf-8", errors="surrogateescape")


def _status_entries(value: str) -> list[dict[str, str]]:
    result = []
    for entry in value.split("\0"):
        if not entry:
            continue
        if len(entry) < 4 or entry[2] != " ":
            raise StateError("git-output")
        result.append({"path": entry[3:], "index": entry[0], "worktree": entry[1]})
    return sorted(result, key=lambda item: item["path"])


def _reject_executable_config(value: str) -> None:
    """Bound snapshotting to configuration that cannot install filter commands.

    Git status can invoke clean/process filters while comparing dirty files.
    Includes can supply those commands outside the captured repository, so the
    initial local reads explicitly disable includes and reject their presence.
    """
    for entry in value.split("\0"):
        if not entry:
            continue
        key = entry.partition("\n")[0].casefold()
        if (key == "include.path" or (key.startswith("includeif.") and key.endswith(".path"))
                or (key.startswith("filter.") and key.rsplit(".", 1)[-1] in {"clean", "smudge", "process"})):
            raise StateError("git-executable-configuration")


def capture_workspace(root: Path) -> dict[str, object]:
    """Capture standalone Git fixtures or plain packets without refreshing Git."""
    origin = checked_path(root)
    all_files = tree_identity(origin)
    files = {path: value for path, value in all_files.items() if path != ".git" and not path.startswith(".git/")}
    git_dir = origin / ".git"
    if not git_dir.exists():
        return {"schemaVersion": 1, "files": files, "git": None, "rawIndexHash": None}
    if not git_dir.is_dir() or (git_dir / "commondir").exists() or (git_dir / "objects/info/alternates").exists():
        raise StateError("git-layout")
    config = _git(origin, "config", "--local", "--no-includes", "--null", "--list")
    _reject_executable_config(config or "")
    # A standalone repository can still enable Git's per-worktree config.
    # Inspect its file without includes before any worktree comparison command.
    worktree_config = git_dir / "config.worktree"
    if worktree_config.exists():
        _reject_executable_config(_git(origin, "config", "--file", str(worktree_config),
                                      "--no-includes", "--null", "--list") or "")
    staged = _git(origin, "ls-files", "--stage", "-z")
    flags = _git(origin, "ls-files", "-v", "-z")
    status = _status_entries(_git(origin, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=all") or "")
    head = _git(origin, "rev-parse", "--verify", "--quiet", "HEAD", optional=True)
    branch = _git(origin, "symbolic-ref", "--quiet", "HEAD", optional=True)
    refs = _git(origin, "for-each-ref", "--sort=refname", "--format=%(refname)%00%(objectname)%00")
    # Capture again after reads: Git optional locks are disabled, so even a
    # metadata-only refresh would mean our purported snapshot was not read-only.
    final_files = tree_identity(origin)
    if all_files != final_files:
        raise StateError("copy-drift")
    metadata = {path[5:]: value for path, value in all_files.items()
                if path.startswith(".git/") and path != ".git/index"}
    return {
        "schemaVersion": 1, "files": files,
        "git": {"head": head, "branch": branch, "refs": refs, "config": config,
                "staged": staged, "flags": flags, "status": status, "metadata": metadata},
        "rawIndexHash": all_files.get(".git/index", {}).get("sha256"),
    }


def _scope(paths: list[str]) -> list[tuple[str, bool]]:
    if not isinstance(paths, list):
        raise StateError("scope-invalid")
    normalized = []
    for value in paths:
        if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
            raise StateError("scope-invalid")
        plain = value[:-1] if value.endswith("/") else value
        parsed = PurePosixPath(plain)
        if (not plain or ":" in plain or parsed.is_absolute() or PureWindowsPath(plain).drive
                or any(part in {".", "..", ""} for part in plain.split("/"))
                or any(part.casefold() == ".git" for part in parsed.parts)):
            raise StateError("scope-invalid")
        normalized.append((plain, value.endswith("/")))
    return normalized


def compare_workspace(before: dict, after: dict, allowed_paths: list[str]) -> list[str]:
    """Return fixed invariant codes, never paths or content from private inputs."""
    scope = _scope(allowed_paths)
    def allowed(path: str) -> bool:
        return any(path == item or (directory and path.startswith(item + "/")) for item, directory in scope)
    for snapshot in (before, after):
        if (not isinstance(snapshot, dict) or type(snapshot.get("schemaVersion")) is not int
                or snapshot["schemaVersion"] != 1 or not isinstance(snapshot.get("files"), dict)
                or "git" not in snapshot or "rawIndexHash" not in snapshot):
            raise StateError("snapshot-invalid")
        if any(not isinstance(path, str) or not isinstance(identity, dict)
               or identity.get("kind") not in {"file", "directory"}
               for path, identity in snapshot["files"].items()):
            raise StateError("snapshot-invalid")
    findings = []
    changed = {path for path in before["files"].keys() | after["files"].keys()
               if before["files"].get(path) != after["files"].get(path)}
    # Creation/removal of otherwise-empty parents is inherent to an allowed
    # file edit. Other files under those parents remain independently checked.
    def allowed_parent(path: str) -> bool:
        values = (before["files"].get(path), after["files"].get(path))
        return (all(value is None or value.get("kind") == "directory" for value in values)
                and any(item.startswith(path + "/") for item, _ in scope))
    if any(not allowed(path) and not allowed_parent(path) for path in changed):
        findings.append("unauthorized-file-change")
    old_git, new_git = before["git"], after["git"]
    if old_git is None or new_git is None:
        if old_git != new_git:
            findings.append("git-layout-change")
        return findings
    if not isinstance(old_git, dict) or not isinstance(new_git, dict):
        raise StateError("snapshot-invalid")
    for field in ("head", "branch", "refs", "config", "staged", "flags", "metadata"):
        if field not in old_git or field not in new_git:
            raise StateError("snapshot-invalid")
        if old_git[field] != new_git[field]:
            findings.append("git-" + field + "-change")
    try:
        for snapshot in (old_git, new_git):
            if not isinstance(snapshot["status"], list) or any(
                not isinstance(entry, dict) or set(entry) != {"path", "index", "worktree"}
                or any(not isinstance(value, str) for value in entry.values())
                for entry in snapshot["status"]
            ):
                raise StateError("snapshot-invalid")
        old_status = [entry for entry in old_git["status"] if not allowed(entry["path"])]
        new_status = [entry for entry in new_git["status"] if not allowed(entry["path"])]
    except (KeyError, TypeError):
        raise StateError("snapshot-invalid") from None
    if old_status != new_status:
        findings.append("unrelated-git-status-change")
    return findings


def cleanup_owned(root: Path, token: str, source: Path) -> None:
    """Delete only the checked exact bundle matching an externally kept token."""
    destination = checked_path(root)
    origin = checked_path(source)
    if destination.parent == destination or _within(destination, origin) or _within(origin, destination):
        raise StateError("source-overlap")
    marker = checked_path(destination / OWNER_MARKER)
    def unique_pairs(pairs):
        record = {}
        for key, value in pairs:
            if key in record:
                raise StateError("owner-invalid")
            record[key] = value
        return record
    try:
        if marker.stat().st_size > 16_384:
            raise StateError("owner-invalid")
        owner = json.loads(marker.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
        expected = {"schemaVersion", "token", "root", "source"}
        if (not isinstance(owner, dict) or set(owner) != expected
                or type(owner["schemaVersion"]) is not int or owner["schemaVersion"] != 1
                or not isinstance(token, str) or not token or not isinstance(owner["token"], str)
                or not secrets.compare_digest(owner["token"].encode(), token.encode())
                or not isinstance(owner["root"], str) or not Path(owner["root"]).is_absolute()
                or not isinstance(owner["source"], str) or not Path(owner["source"]).is_absolute()
                or checked_path(Path(owner["root"])) != destination
                or checked_path(Path(owner["source"])) != origin):
            raise StateError("owner-invalid")
    except (OSError, ValueError, TypeError):
        raise StateError("owner-invalid") from None
    # Reject every link before removal; rmtree cannot be used to discover trust.
    tree_identity(destination)
    def retry_readonly(function, path, _error):
        target = checked_path(Path(path))
        if not _within(target, destination):
            raise StateError("cleanup-failed")
        target.chmod(target.stat().st_mode | stat.S_IWRITE)
        function(target)
    try:
        shutil.rmtree(destination, onerror=retry_readonly)
    except (OSError, StateError):
        raise StateError("cleanup-failed") from None
