#!/usr/bin/env python3
"""Discover repository data-exposure candidates without emitting matched values."""

from __future__ import annotations

import argparse
import io
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile


TEXT_EXTENSIONS = {
    ".c", ".cc", ".cfg", ".conf", ".cpp", ".cs", ".csproj", ".css", ".csv",
    ".dart", ".editorconfig", ".env", ".fs", ".fsproj", ".go", ".gradle", ".h",
    ".hpp", ".htm", ".html", ".ini", ".java", ".js", ".json", ".jsx", ".kt",
    ".kts", ".log", ".md", ".mjs", ".php", ".plist", ".properties", ".ps1",
    ".py", ".r", ".rb", ".razor", ".rs", ".scss", ".sh", ".sln", ".sql",
    ".svg", ".swift", ".toml", ".ts", ".tsv", ".tsx", ".txt", ".vb", ".vue",
    ".xml", ".xaml", ".yaml", ".yml",
}
ZIP_EXTENSIONS = {".zip", ".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".bmp", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
DATABASE_EXTENSIONS = {".db", ".db3", ".mdb", ".sqlite", ".sqlite3"}
ARCHIVE_EXTENSIONS = {".7z", ".bz2", ".gz", ".rar", ".tar", ".tgz", ".xz"}
GENERATED_PARTS = {
    ".git", ".gradle", ".idea", ".mypy_cache", ".next", ".nuxt", ".pytest_cache",
    ".tox", ".venv", ".vs", "__pycache__", "bin", "build", "coverage",
    "dist", "node_modules", "obj", "out", "target", "vendor", "venv",
}

PATTERNS = (
    ("email-address", "medium", re.compile(r"(?i)(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+")),
    ("phone-number", "low", re.compile(r"(?<!\w)(?:\+?\d[\d ()\-]{7,}\d)(?!\w)")),
    ("government-identifier", "high", re.compile(r"(?<!\d)(?:\d{3}-\d{2}-\d{4}|\d{6}[- ]?\d{4})(?!\d)")),
    ("payment-card-number", "high", re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)")),
    ("private-key-material", "high", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("credential-assignment", "high", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret)[\w.-]*\s*[:=]\s*['\"]?[^\s'\"${}<>{}]{8,}")),
    ("windows-user-path", "high", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s\"']+\\")),
    ("unix-user-path", "medium", re.compile(r"(?<![\w/])/(?:home|Users)/[^/\s\"']+/")),
    ("precise-coordinate", "medium", re.compile(r"(?<![\d.])-?(?:[0-8]?\d(?:\.\d{4,})|90\.0+)[, ]+\s*-?(?:1[0-7]\d(?:\.\d{4,})|\d?\d(?:\.\d{4,})|180\.0+)(?![\d.])")),
    ("private-endpoint", "medium", re.compile(r"(?i)\b(?:https?://)?(?:[a-z0-9-]+\.)+(?:internal|corp|lan|local)(?::\d+)?\b")),
    ("pseudonymization-map", "medium", re.compile(r"(?i)\b(?:deanonymi[sz]|reidentif|identity[_ -]?map|pseudonym[_ -]?map|token[_ -]?map|original[_ -]?id)\b")),
)

MIGRATION_PATTERN = re.compile(
    r"(?i)\b(?:one[- ]?off|one[- ]?time|run once|delete after|temporary (?:migration|converter|script)|"
    r"manual (?:migration|backfill|repair)|convert (?:my|personal) data|ad[- ]?hoc (?:migration|repair|backfill)|"
    r"disposable (?:migration|converter|script))\b"
)
MIGRATION_PATH_PATTERN = re.compile(
    r"(?i)(?:^|[/_.-])(?:one[-_]?off|run[-_]?once|temp(?:orary)?[-_]?(?:migration|convert|backfill|repair)|"
    r"ad[-_]?hoc[-_]?(?:migration|backfill|repair)|personal[-_]?(?:migration|convert))(?:[/_.-]|$)"
)
LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"
PERSON_RECORD_FIELDS = {
    "address", "birth_date", "customer", "date_of_birth", "dob", "email", "employee",
    "first_name", "full_name", "last_name", "name", "patient", "phone", "postal_code",
    "postcode", "ssn", "user_id",
}
SENSITIVE_RECORD_FIELDS = {
    "account_number", "bank", "diagnosis", "disability", "ethnicity", "health", "income",
    "insurance", "medical", "passport", "religion", "salary", "sexual_orientation", "tax_id",
}


def safe_git_environment() -> dict[str, str]:
    """Return an environment that cannot redirect or instrument Git inspection."""
    environment = {
        name: value for name, value in os.environ.items() if not name.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CREDENTIAL_INTERACTIVE": "never",
            "GIT_LFS_SKIP_SMUDGE": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def safe_git_command(root: Path, *arguments: str) -> list[str]:
    """Build a non-interactive Git command with execution-capable local config disabled."""
    return [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "credential.interactive=false",
        "-c",
        "protocol.allow=never",
        "-C",
        str(root),
        *arguments,
    ]


class Scanner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.root = Path(args.root).resolve()
        self.candidates: list[dict[str, object]] = []
        self.gaps: list[dict[str, str]] = []
        self.exclusions: list[dict[str, str]] = []
        self.seen_units: set[tuple[str, str, str]] = set()
        self.seen_blobs: set[str] = set()
        self.seen_location_units: set[tuple[str, str]] = set()
        self.history_locators: dict[int, tuple[str, str]] = {}
        self.stats = {
            "files_considered": 0,
            "text_units_scanned": 0,
            "archive_members_scanned": 0,
            "history_blobs_scanned": 0,
            "bytes_scanned": 0,
        }

    def git_process(
        self, *arguments: str, input_bytes: bytes | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            safe_git_command(self.root, *arguments),
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=safe_git_environment(),
        )

    def git(self, *arguments: str, input_bytes: bytes | None = None, check: bool = True) -> bytes:
        process = self.git_process(*arguments, input_bytes=input_bytes)
        if check and process.returncode != 0:
            raise RuntimeError(f"git command failed: {arguments[0] if arguments else 'unknown'}")
        return process.stdout

    def git_text(self, *arguments: str, check: bool = True) -> str:
        return self.git(*arguments, check=check).decode("utf-8", errors="replace")

    def add_candidate(
        self,
        category: str,
        confidence: str,
        scope: str,
        path: str,
        line: int | None = None,
        commit: str | None = None,
        member: str | None = None,
    ) -> None:
        item: dict[str, object] = {
            "category": category,
            "confidence": confidence,
            "scope": scope,
            "path": self.redacted_location(path),
        }
        if line is not None:
            item["line"] = line
        if commit is not None:
            item["commit"] = commit
        if member is not None:
            item["member"] = self.redacted_location(member)
        self.candidates.append(item)
        if scope == "history" and commit is not None:
            self.history_locators[id(item)] = (commit, path)

    def add_gap(self, category: str, scope: str, path: str = "") -> None:
        item = {"category": category, "scope": scope}
        if path:
            item["path"] = self.redacted_location(path)
        if item not in self.gaps:
            self.gaps.append(item)

    def add_exclusion(self, category: str, path: str) -> None:
        item = {"category": category, "path": self.redacted_location(path)}
        if item not in self.exclusions:
            self.exclusions.append(item)

    @staticmethod
    def normalized(path: str) -> str:
        normalized = path.replace("\\", "/")
        while normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized

    @classmethod
    def safe_selected_path(cls, value: str) -> str:
        normalized = cls.normalized(value)
        path = PurePosixPath(normalized)
        if (
            not value.strip()
            or "\x00" in value
            or any(ord(character) < 32 for character in value)
            or path.is_absolute()
            or bool(path.anchor)
            or re.match(r"^[A-Za-z]:", normalized) is not None
            or not path.parts
            or any(part in {"", ".", ".."} for part in path.parts)
            or any(part.casefold() == ".git" for part in path.parts)
        ):
            raise ValueError("unsafe repository-relative path")
        return path.as_posix()

    @staticmethod
    def is_link_or_reparse_point(path: Path) -> bool:
        metadata = path.stat(follow_symlinks=False)
        if stat.S_ISLNK(metadata.st_mode):
            return True
        attributes = getattr(metadata, "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))

    @staticmethod
    def location_component_is_sensitive(component: str) -> bool:
        if any(pattern.search(component) for _, _, pattern in PATTERNS):
            return True
        for match in re.finditer(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])", component):
            try:
                if ipaddress.ip_address(match.group(0)).is_global:
                    return True
            except ValueError:
                continue
        return False

    def redacted_location(self, location: str) -> str:
        normalized = location.replace("\\", "/")
        if normalized.startswith("<") and normalized.endswith(">"):
            return "<redacted-location>" if self.location_component_is_sensitive(normalized) else normalized
        return "/".join(
            "<redacted-name>" if self.location_component_is_sensitive(part) else part
            for part in normalized.split("/")
        )

    def scan_location_name(
        self,
        location: str,
        scope: str,
        path: str,
        commit: str | None = None,
        member: str | None = None,
    ) -> None:
        for category, confidence, pattern in PATTERNS:
            if pattern.search(location):
                self.add_candidate(f"path-{category}", confidence, scope, path, commit=commit, member=member)
        for match in re.finditer(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])", location):
            try:
                address = ipaddress.ip_address(match.group(0))
            except ValueError:
                continue
            if address.version == 4 and address.is_global:
                self.add_candidate("path-public-ip-address", "medium", scope, path, commit=commit, member=member)

    def scan_location_once(
        self, location: str, scope: str, path: str, commit: str | None = None
    ) -> None:
        key = (scope, self.normalized(location))
        if key in self.seen_location_units:
            return
        self.seen_location_units.add(key)
        self.scan_location_name(location, scope, path, commit)

    @staticmethod
    def generated(path: str) -> bool:
        parts = {part.lower() for part in PurePosixPath(path.replace("\\", "/")).parts}
        return bool(parts & {part.lower() for part in GENERATED_PARTS})

    def matches_paths(self, path: str, selected: set[str]) -> bool:
        if not selected:
            return True
        normalized = self.normalized(path)
        return any(normalized == item or normalized.startswith(item.rstrip("/") + "/") for item in selected)

    @staticmethod
    def validate_revision_text(value: str) -> None:
        if (
            not value
            or value.startswith("-")
            or any(character.isspace() or ord(character) < 32 for character in value)
            or "\x00" in value
            or ":" in value
            or "\\" in value
        ):
            raise ValueError("unsafe Git revision")

    def resolve_base_revision(self, value: str) -> str:
        self.validate_revision_text(value)
        resolved = self.git_text(
            "rev-parse", "--verify", "--end-of-options", f"{value}^{{commit}}"
        ).strip()
        if re.fullmatch(r"[0-9a-fA-F]{40,64}", resolved) is None:
            raise ValueError("invalid Git base revision")
        return resolved

    def validate_history_revision(self, value: str) -> str:
        self.validate_revision_text(value)
        self.git("rev-list", "--max-count=1", "--end-of-options", value)
        return value

    def scan_text(
        self,
        text: str,
        scope: str,
        path: str,
        commit: str | None = None,
        member: str | None = None,
    ) -> None:
        self.stats["text_units_scanned"] += 1
        for line_number, line in enumerate(text.splitlines(), start=1):
            for category, confidence, pattern in PATTERNS:
                if pattern.search(line):
                    self.add_candidate(category, confidence, scope, path, line_number, commit, member)
            for match in re.finditer(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])", line):
                try:
                    address = ipaddress.ip_address(match.group(0))
                except ValueError:
                    continue
                if address.version == 4 and address.is_global:
                    self.add_candidate("public-ip-address", "medium", scope, path, line_number, commit, member)
            if MIGRATION_PATTERN.search(line):
                self.add_candidate("disposable-migration-signal", "high", scope, path, line_number, commit, member)
            normalized_fields = {
                token.lower().replace("-", "_")
                for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,40}", line)
            }
            person_fields = normalized_fields & PERSON_RECORD_FIELDS
            sensitive_fields = normalized_fields & SENSITIVE_RECORD_FIELDS
            if len(person_fields) >= 2:
                self.add_candidate("structured-person-record-fields", "medium", scope, path, line_number, commit, member)
            if sensitive_fields and person_fields:
                self.add_candidate("sensitive-person-record-fields", "high", scope, path, line_number, commit, member)

        if MIGRATION_PATH_PATTERN.search(path):
            self.add_candidate("disposable-migration-path", "medium", scope, path, commit=commit, member=member)

    def looks_textual(self, data: bytes, path: str) -> bool:
        suffix = Path(path).suffix.lower()
        if suffix in TEXT_EXTENSIONS or Path(path).name.lower() in {"dockerfile", "makefile", "license"}:
            return True
        sample = data[:8192]
        if b"\x00" in sample:
            return False
        if not sample:
            return True
        printable = sum(byte in b"\t\n\r" or 32 <= byte < 127 or byte >= 128 for byte in sample)
        return printable / len(sample) >= 0.85

    def scan_zip(self, data: bytes, scope: str, path: str, commit: str | None) -> None:
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
        except (zipfile.BadZipFile, OSError):
            self.add_gap("unreadable-zip-container", scope, path)
            return
        infos = archive.infolist()
        if len(infos) > self.args.max_archive_members:
            self.add_gap("archive-member-limit", scope, path)
            infos = infos[: self.args.max_archive_members]
        total = 0
        for info in infos:
            if info.is_dir():
                continue
            member = info.filename.replace("\\", "/")
            self.scan_location_name(member, scope, path, commit, member)
            if info.flag_bits & 1:
                self.add_gap("encrypted-archive-member", scope, path)
                continue
            if info.file_size > self.args.max_archive_member_bytes:
                self.add_gap("oversized-archive-member", scope, path)
                continue
            remaining = self.args.max_archive_total_bytes - total
            if remaining <= 0 or info.file_size > remaining:
                self.add_gap("archive-expanded-size-limit", scope, path)
                break
            if info.compress_size and info.file_size / max(info.compress_size, 1) > self.args.max_compression_ratio:
                self.add_gap("archive-compression-ratio-limit", scope, path)
                continue
            suffix = Path(member).suffix.lower()
            if suffix not in TEXT_EXTENSIONS and suffix not in {".rels"}:
                self.add_gap("unsupported-archive-member-format", scope, path)
                continue
            read_limit = min(self.args.max_archive_member_bytes, remaining)
            try:
                with archive.open(info) as member_stream:
                    member_data = member_stream.read(read_limit + 1)
            except (EOFError, NotImplementedError, RuntimeError, OSError, zipfile.BadZipFile):
                self.add_gap("unreadable-archive-member", scope, path)
                continue
            if len(member_data) > self.args.max_archive_member_bytes:
                self.add_gap("oversized-archive-member", scope, path)
                continue
            if len(member_data) > remaining:
                self.add_gap("archive-expanded-size-limit", scope, path)
                break
            total += len(member_data)
            if not self.looks_textual(member_data, member):
                continue
            self.stats["archive_members_scanned"] += 1
            self.stats["bytes_scanned"] += len(member_data)
            self.scan_text(member_data.decode("utf-8", errors="replace"), scope, path, commit, member)

    def scan_bytes(self, data: bytes, scope: str, path: str, commit: str | None = None) -> None:
        unit = (scope, path, commit or "")
        if unit in self.seen_units:
            return
        self.seen_units.add(unit)
        self.stats["files_considered"] += 1
        self.scan_location_once(path, scope, path, commit)
        if len(data) > self.args.max_bytes:
            self.add_gap("oversized-file", scope, path)
            return
        if data.startswith(LFS_HEADER):
            self.add_gap("git-lfs-pointer-not-inspected", scope, path)
            return
        suffix = Path(path).suffix.lower()
        if suffix in ZIP_EXTENSIONS or data.startswith(b"PK\x03\x04"):
            self.scan_zip(data, scope, path, commit)
            return
        if suffix in PDF_EXTENSIONS or data.startswith(b"%PDF"):
            self.add_gap("pdf-content-not-inspected", scope, path)
            return
        if suffix in IMAGE_EXTENSIONS:
            self.add_gap("image-content-and-metadata-not-inspected", scope, path)
            return
        if suffix in DATABASE_EXTENSIONS:
            self.add_gap("database-content-not-inspected", scope, path)
            return
        if suffix in ARCHIVE_EXTENSIONS:
            self.add_gap("unsupported-archive-format", scope, path)
            return
        if not self.looks_textual(data, path):
            self.add_gap("binary-content-not-inspected", scope, path)
            return
        self.stats["bytes_scanned"] += len(data)
        self.scan_text(data.decode("utf-8", errors="replace"), scope, path, commit)

    def read_worktree(self, path: str, scope: str) -> bytes | None:
        try:
            relative = PurePosixPath(self.safe_selected_path(path))
        except ValueError:
            self.add_gap("unsafe-repository-path-not-inspected", scope, path)
            return None
        candidate = self.root.joinpath(*relative.parts)
        current = self.root
        for part in relative.parts:
            current = current / part
            if os.path.lexists(current):
                try:
                    if self.is_link_or_reparse_point(current):
                        self.add_gap("symlink-or-reparse-target-not-inspected", scope, path)
                        return None
                except OSError:
                    self.add_gap("unreadable-worktree-path", scope, path)
                    return None
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.root)
        except ValueError:
            self.add_gap("path-outside-repository-not-inspected", scope, path)
            return None
        if not candidate.is_file():
            return None
        try:
            return candidate.read_bytes()
        except OSError:
            self.add_gap("unreadable-worktree-file", scope, path)
            return None

    def scan_worktree_paths(self, paths: set[str], scope: str) -> None:
        for path in sorted(paths):
            if self.generated(path):
                self.add_exclusion("generated-or-dependency-cache", path)
                continue
            data = self.read_worktree(path, scope)
            if data is not None:
                self.scan_bytes(data, scope, path)

    def index_entries(self) -> dict[str, tuple[str, str]]:
        entries: dict[str, tuple[str, str]] = {}
        output = self.git_text("ls-files", "--stage", "-z")
        for record in output.split("\0"):
            if not record or "\t" not in record:
                continue
            metadata, path = record.split("\t", 1)
            parts = metadata.split()
            if len(parts) >= 3 and parts[2] == "0":
                entries[self.normalized(path)] = (parts[0], parts[1])
        return entries

    def scan_index(self, paths: set[str] | None = None) -> None:
        for path, (mode, object_id) in sorted(self.index_entries().items()):
            if paths is not None and path not in paths:
                continue
            if mode == "160000":
                self.add_gap("submodule-content-not-inspected", "index", path)
                continue
            if mode == "120000":
                self.add_gap("symlink-target-not-inspected", "index", path)
                continue
            if self.generated(path):
                self.add_exclusion("generated-or-dependency-cache", path)
                continue
            data = self.git("cat-file", "blob", object_id)
            self.scan_bytes(data, "index", path)

    def list_current_paths(self) -> tuple[set[str], set[str], set[str]]:
        tracked = {self.normalized(item) for item in self.git_text("ls-files", "-z").split("\0") if item}
        untracked = {
            self.normalized(item)
            for item in self.git_text("ls-files", "--others", "--exclude-standard", "-z").split("\0")
            if item
        }
        ignored = {
            self.normalized(item)
            for item in self.git_text("ls-files", "--others", "--ignored", "--exclude-standard", "-z").split("\0")
            if item
        }
        return tracked, untracked, ignored

    def scan_current_full(self, selected: set[str] | None = None) -> None:
        tracked, untracked, ignored = self.list_current_paths()
        if selected is not None:
            tracked = {path for path in tracked if self.matches_paths(path, selected)}
            untracked = {path for path in untracked if self.matches_paths(path, selected)}
            ignored = {path for path in ignored if self.matches_paths(path, selected)}
        self.scan_worktree_paths(tracked, "worktree")
        self.scan_worktree_paths(untracked, "untracked")
        self.scan_worktree_paths(ignored, "ignored")
        self.scan_index(tracked)

    def scan_ref_file(self, ref: str, path: str, scope: str) -> None:
        process = self.git_process("show", f"{ref}:{path}")
        if process.returncode == 0:
            self.scan_bytes(process.stdout, scope, path, ref if re.fullmatch(r"[0-9a-fA-F]{7,64}", ref) else None)

    def changed_paths(self, arguments: list[str]) -> tuple[set[str], set[str]]:
        output = self.git_text(*arguments, "--name-status", "-z", "--find-renames", "--")
        tokens = [token for token in output.split("\0") if token]
        current_paths: set[str] = set()
        base_paths: set[str] = set()
        index = 0
        while index < len(tokens):
            status = tokens[index].lstrip("\r\n")
            index += 1
            if not status:
                continue
            code = status[0]
            if code in {"R", "C"}:
                if index + 1 >= len(tokens):
                    break
                old_path = self.normalized(tokens[index])
                new_path = self.normalized(tokens[index + 1])
                index += 2
                base_paths.add(old_path)
                current_paths.add(new_path)
                continue
            if index >= len(tokens):
                break
            path = self.normalized(tokens[index])
            index += 1
            if code != "D":
                current_paths.add(path)
            if code != "A":
                base_paths.add(path)
        return current_paths, base_paths

    def scan_changes(self) -> None:
        untracked = {
            self.normalized(item)
            for item in self.git_text("ls-files", "--others", "--exclude-standard", "-z").split("\0")
            if item
        }
        if self.args.base:
            current_paths, base_paths = self.changed_paths(["diff", self.args.base])
            current = current_paths | untracked
            self.scan_worktree_paths(current, "changes-worktree")
            self.scan_index(set(self.index_entries()) & (current_paths | base_paths))
            for path in sorted(base_paths):
                self.scan_ref_file(self.args.base, path, "changes-base")
        else:
            unstaged_current, unstaged_base = self.changed_paths(["diff"])
            staged_current, staged_base = self.changed_paths(["diff", "--cached"])
            current = unstaged_current | staged_current | untracked
            self.scan_worktree_paths(current, "changes-worktree")
            index_paths = set(self.index_entries()) & (
                unstaged_current | unstaged_base | staged_current | staged_base
            )
            self.scan_index(index_paths)
            for path in sorted(staged_base):
                self.scan_ref_file("HEAD", path, "changes-base")

    def expand_paths_via_renames(self, selected: set[str]) -> set[str]:
        expanded = set(selected)
        output = self.git_text("log", "--all", "--format=", "--name-status", "-M", "-z", check=False)
        tokens = [token for token in output.split("\0") if token]
        renames: list[tuple[str, str]] = []
        index = 0
        while index < len(tokens):
            token = tokens[index].lstrip("\r\n")
            if token.startswith("R") and index + 2 < len(tokens):
                renames.append((self.normalized(tokens[index + 1]), self.normalized(tokens[index + 2])))
                index += 3
            else:
                index += 1
        changed = True
        while changed:
            changed = False
            for old, new in renames:
                if self.matches_paths(old, expanded) or self.matches_paths(new, expanded):
                    for value in (old, new):
                        if value not in expanded:
                            expanded.add(value)
                            changed = True
        return expanded

    def object_records(
        self, revision: str, selected: set[str]
    ) -> list[tuple[str, str, str, str]]:
        arguments = [
            "log",
            "--raw",
            "--root",
            "-m",
            "--no-renames",
            "--no-abbrev",
            "-z",
            "--format=",
        ]
        if revision == "--all":
            arguments.append("--all")
        else:
            arguments.extend(["--end-of-options", revision])
        if selected:
            arguments.append("--")
            arguments.extend(sorted(selected))
        tokens = self.git_text(*arguments, check=False).split("\0")
        records: set[tuple[str, str, str, str]] = set()
        zero_id = re.compile(r"0+\Z")
        index = 0
        while index < len(tokens):
            header = tokens[index].lstrip("\r\n")
            index += 1
            if not header.startswith(":"):
                continue
            fields = header[1:].split()
            if len(fields) < 5 or index >= len(tokens):
                continue
            old_mode, new_mode, old_id, new_id, status = fields[:5]
            old_path = self.normalized(tokens[index])
            index += 1
            new_path = old_path
            if status[:1] in {"R", "C"} and index < len(tokens):
                new_path = self.normalized(tokens[index])
                index += 1
            for mode, object_id, path in (
                (old_mode, old_id, old_path),
                (new_mode, new_id, new_path),
            ):
                if (
                    mode == "000000"
                    or zero_id.fullmatch(object_id) is not None
                    or re.fullmatch(r"[0-9a-fA-F]{40,64}", object_id) is None
                    or not self.matches_paths(path, selected)
                ):
                    continue
                object_type = "commit" if mode == "160000" else "blob"
                records.add((object_id, path, mode, object_type))
        return sorted(
            records,
            key=lambda record: (
                record[1].casefold(),
                record[1],
                record[2],
                record[0],
                record[3],
            ),
        )

    def blob_metadata(self, object_ids: list[str]) -> dict[str, tuple[str, int]]:
        if not object_ids:
            return {}
        payload = ("\n".join(object_ids) + "\n").encode()
        output = self.git("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)", input_bytes=payload)
        metadata: dict[str, tuple[str, int]] = {}
        for line in output.decode("utf-8", errors="replace").splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[2].isdigit():
                metadata[parts[0]] = (parts[1], int(parts[2]))
        return metadata

    def scan_commit_messages(self, revision: str, selected: set[str]) -> None:
        args = ["log", "--format=%H%x1f%an%x1f%ae%x1f%B%x1e"]
        if revision == "--all":
            args.append("--all")
        else:
            args.extend(["--end-of-options", revision])
        if selected:
            args.append("--")
            args.extend(sorted(selected))
        output = self.git_text(*args, check=False)
        for record in output.split("\x1e"):
            parts = record.split("\x1f", 3)
            if len(parts) != 4:
                continue
            commit, author_name, author_email, message = parts
            commit = commit.strip()
            if commit:
                self.scan_text(f"{author_name}\n{author_email}", "commit-author", "<commit-author>", commit)
                self.scan_text(message, "commit-message", "<commit-message>", commit)

    def scan_annotated_tags(self) -> None:
        output = self.git_text(
            "for-each-ref",
            "refs/tags",
            "--format=%(objecttype)%00%(objectname)%00%(refname:short)",
            check=False,
        )
        for line in output.splitlines():
            parts = line.split("\0")
            if len(parts) != 3 or parts[0] != "tag":
                continue
            tag_data = self.git("cat-file", "tag", parts[1], check=False).decode("utf-8", errors="replace")
            headers, _, message = tag_data.partition("\n\n")
            tagger = next((line.removeprefix("tagger ") for line in headers.splitlines() if line.startswith("tagger ")), "")
            if tagger:
                self.scan_text(tagger, "tagger", f"<tag:{parts[2]}:tagger>")
            self.scan_text(message, "annotated-tag", f"<tag:{parts[2]}>")

    def scan_history(self, revision: str, selected: set[str]) -> None:
        records = self.object_records(revision, selected)
        regular_records: list[tuple[str, str]] = []
        for object_id, path, mode, object_type in records:
            self.scan_location_once(path, "history", path, object_id)
            if mode == "120000":
                self.add_gap("historical-symlink-target-not-inspected", "history", path)
                continue
            if mode == "160000":
                self.add_gap("historical-submodule-content-not-inspected", "history", path)
                continue
            if object_type == "blob":
                regular_records.append((object_id, path))
        metadata = self.blob_metadata([object_id for object_id, _ in regular_records])
        for object_id, path in regular_records:
            if object_id in self.seen_blobs:
                self.scan_location_once(path, "history", path, object_id)
                continue
            object_type, size = metadata.get(object_id, ("unknown", 0))
            if object_type != "blob":
                continue
            self.seen_blobs.add(object_id)
            if size > self.args.max_bytes:
                self.add_gap("oversized-history-blob", "history", path)
                continue
            data = self.git("cat-file", "blob", object_id)
            self.stats["history_blobs_scanned"] += 1
            self.scan_bytes(data, "history", path, object_id)
        self.scan_commit_messages(revision, selected)
        if revision == "--all" and not selected:
            self.scan_annotated_tags()

    def resolve_history_candidate_commits(self, revision: str) -> None:
        cache: dict[tuple[str, str], str | None] = {}
        for item in self.candidates:
            if item.get("scope") != "history" or "commit" not in item:
                continue
            locator = self.history_locators.get(id(item))
            if locator is None:
                item.pop("commit", None)
                continue
            blob, path = locator
            key = (blob, path)
            if key not in cache:
                arguments = ["log", "--format=%H", f"--find-object={blob}"]
                if revision == "--all":
                    arguments.append("--all")
                else:
                    arguments.extend(["--end-of-options", revision])
                arguments.extend(["--", path])
                commits = self.git_text(*arguments, check=False).splitlines()
                containing_commit: str | None = None
                for commit in commits:
                    commit = commit.strip()
                    if not commit:
                        continue
                    entry = self.git_text("ls-tree", commit, "--", path, check=False)
                    metadata, _, listed_path = entry.partition("\t")
                    fields = metadata.split()
                    if listed_path and len(fields) >= 3 and fields[2] == blob:
                        containing_commit = commit
                        break
                cache[key] = containing_commit
            resolved = cache[key]
            if resolved:
                item["commit"] = resolved
            else:
                item.pop("commit", None)

    def repository_gaps(self) -> None:
        shallow = self.git_text("rev-parse", "--is-shallow-repository", check=False).strip()
        if shallow == "true":
            self.add_gap("shallow-history", "repository")
        index = self.index_entries()
        for path, (mode, _) in index.items():
            if mode == "160000":
                self.add_gap("submodule-content-not-inspected", "repository", path)

    def execute(self) -> dict[str, object]:
        if self.git_text("rev-parse", "--is-inside-work-tree", check=False).strip() != "true":
            raise RuntimeError("root is not a Git working tree")
        if self.args.base:
            self.args.base = self.resolve_base_revision(self.args.base)
        if self.args.git_range:
            self.args.git_range = self.validate_history_revision(self.args.git_range)
        self.repository_gaps()
        selected = {self.safe_selected_path(path) for path in self.args.paths}
        if selected:
            selected = self.expand_paths_via_renames(selected)

        if self.args.scope == "full":
            self.scan_current_full()
            history_revision = "--all"
            self.scan_history(history_revision, set())
            self.resolve_history_candidate_commits(history_revision)
        elif self.args.scope == "changes":
            self.scan_changes()
        elif self.args.scope == "history":
            history_revision = self.args.git_range or "--all"
            self.scan_history(history_revision, selected)
            self.resolve_history_candidate_commits(history_revision)
        elif self.args.scope == "path":
            if not selected:
                raise RuntimeError("path scope requires at least one --path")
            self.scan_current_full(selected)
            history_revision = self.args.git_range or "--all"
            self.scan_history(history_revision, selected)
            self.resolve_history_candidate_commits(history_revision)

        ordered = sorted(
            self.candidates,
            key=lambda item: (
                str(item.get("scope", "")),
                str(item.get("path", "")),
                str(item.get("commit", "")),
                int(item.get("line", 0)),
                str(item.get("category", "")),
            ),
        )
        for number, item in enumerate(ordered, start=1):
            item["id"] = f"CAND-{number:04d}"
        return {
            "schema_version": 1,
            "scope": self.args.scope,
            "candidate_count": len(ordered),
            "candidates": ordered,
            "coverage": self.stats,
            "gaps": sorted(self.gaps, key=lambda item: (item["scope"], item.get("path", ""), item["category"])),
            "exclusions": sorted(self.exclusions, key=lambda item: (item["path"], item["category"])),
            "limitations": [
                "Candidates require local contextual validation.",
                "A clean result does not prove absence of personal or private data.",
                "Matched values and surrounding snippets are intentionally omitted.",
            ],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find redacted repository data-exposure candidates.")
    parser.add_argument("--root", default=".", help="Git working tree to inspect.")
    parser.add_argument("--scope", choices=("full", "changes", "path", "history"), default="full")
    parser.add_argument("--base", help="Base ref for changes scope.")
    parser.add_argument("--range", dest="git_range", help="Explicit revision range for history or path scope.")
    parser.add_argument("--path", dest="paths", action="append", default=[], help="Repository-relative path; repeatable.")
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-archive-members", type=int, default=500)
    parser.add_argument("--max-archive-member-bytes", type=int, default=1_000_000)
    parser.add_argument("--max-archive-total-bytes", type=int, default=10_000_000)
    parser.add_argument("--max-compression-ratio", type=float, default=100.0)
    args = parser.parse_args()
    if args.base and args.scope != "changes":
        parser.error("--base is valid only with --scope changes")
    if args.git_range and args.scope not in {"history", "path"}:
        parser.error("--range is valid only with --scope history or path")
    if args.scope == "path" and not args.paths:
        parser.error("--scope path requires at least one --path")
    return args


def main() -> int:
    args = parse_args()
    try:
        result = Scanner(args).execute()
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        json.dump({"schema_version": 1, "error": type(error).__name__}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2
    json.dump(result, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
