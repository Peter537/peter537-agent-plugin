#!/usr/bin/env python3
"""Inventory dependency-bearing files and software supply-chain inputs.

The script is deliberately read-only, deterministic, and standard-library only.
It discovers evidence; it does not resolve packages or claim complete coverage.
"""

from __future__ import annotations

import argparse
import configparser
import fnmatch
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Iterable


EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".cache",
        ".gradle",
        ".mypy_cache",
        ".next",
        ".nox",
        ".nuxt",
        ".parcel-cache",
        ".pytest_cache",
        ".ruff_cache",
        ".terraform",
        ".tox",
        ".turbo",
        ".venv",
        "__pycache__",
        "bin",
        "build",
        "coverage",
        "dist",
        "env",
        "node_modules",
        "obj",
        "out",
        "target",
        "venv",
    }
)

VENDORED_DIRECTORY_NAMES = frozenset(
    {
        "deps",
        "extern",
        "external",
        "third-party",
        "third_party",
        "vendor",
        "vendored",
    }
)

EXACT_FILE_RULES: dict[str, tuple[str, str]] = {
    # JavaScript and TypeScript
    "package.json": ("manifest", "javascript"),
    "package-lock.json": ("lockfile", "javascript"),
    "npm-shrinkwrap.json": ("lockfile", "javascript"),
    "pnpm-lock.yaml": ("lockfile", "javascript"),
    "pnpm-workspace.yaml": ("workspace", "javascript"),
    "yarn.lock": ("lockfile", "javascript"),
    "bun.lock": ("lockfile", "javascript"),
    "bun.lockb": ("lockfile", "javascript"),
    ".yarnrc.yml": ("dependency-config", "javascript"),
    ".npmrc": ("registry-config", "javascript"),
    # Python
    "pyproject.toml": ("manifest", "python"),
    "setup.py": ("manifest", "python"),
    "setup.cfg": ("manifest", "python"),
    "pipfile": ("manifest", "python"),
    "pipfile.lock": ("lockfile", "python"),
    "poetry.lock": ("lockfile", "python"),
    "pdm.lock": ("lockfile", "python"),
    "uv.lock": ("lockfile", "python"),
    "pylock.toml": ("lockfile", "python"),
    # .NET
    "directory.packages.props": ("central-versions", "dotnet"),
    "directory.build.props": ("build-definition", "dotnet"),
    "directory.build.targets": ("build-definition", "dotnet"),
    "packages.config": ("manifest", "dotnet"),
    "packages.lock.json": ("lockfile", "dotnet"),
    "nuget.config": ("registry-config", "dotnet"),
    # Go
    "go.mod": ("manifest", "go"),
    "go.sum": ("integrity-file", "go"),
    "go.work": ("workspace", "go"),
    "go.work.sum": ("integrity-file", "go"),
    # Rust
    "cargo.toml": ("manifest", "rust"),
    "cargo.lock": ("lockfile", "rust"),
    ".cargo/config.toml": ("registry-config", "rust"),
    # JVM
    "pom.xml": ("manifest", "jvm"),
    "build.gradle": ("build-definition", "jvm"),
    "build.gradle.kts": ("build-definition", "jvm"),
    "settings.gradle": ("workspace", "jvm"),
    "settings.gradle.kts": ("workspace", "jvm"),
    "gradle.lockfile": ("lockfile", "jvm"),
    "libs.versions.toml": ("central-versions", "jvm"),
    "verification-metadata.xml": ("integrity-file", "jvm"),
    "gradle-wrapper.properties": ("toolchain-pin", "jvm"),
    # PHP
    "composer.json": ("manifest", "php"),
    "composer.lock": ("lockfile", "php"),
    # Ruby
    "gemfile": ("manifest", "ruby"),
    "gemfile.lock": ("lockfile", "ruby"),
    "gems.locked": ("lockfile", "ruby"),
    # Dart / Flutter
    "pubspec.yaml": ("manifest", "dart"),
    "pubspec.lock": ("lockfile", "dart"),
    # Elixir / Erlang
    "mix.exs": ("manifest", "elixir"),
    "mix.lock": ("lockfile", "elixir"),
    "rebar.config": ("manifest", "erlang"),
    "rebar.lock": ("lockfile", "erlang"),
    # Haskell
    "cabal.project": ("workspace", "haskell"),
    "cabal.project.freeze": ("lockfile", "haskell"),
    "stack.yaml": ("manifest", "haskell"),
    "stack.yaml.lock": ("lockfile", "haskell"),
    # R
    "description": ("manifest", "r"),
    "renv.lock": ("lockfile", "r"),
    "pak.lock": ("lockfile", "r"),
    # C and C++
    "conanfile.py": ("manifest", "cpp"),
    "conanfile.txt": ("manifest", "cpp"),
    "conan.lock": ("lockfile", "cpp"),
    "vcpkg.json": ("manifest", "cpp"),
    "vcpkg-configuration.json": ("registry-config", "cpp"),
    "cmakelists.txt": ("build-definition", "cpp"),
    "meson.build": ("build-definition", "cpp"),
    "module.bazel": ("manifest", "bazel"),
    "module.bazel.lock": ("lockfile", "bazel"),
    "workspace": ("workspace", "bazel"),
    "workspace.bazel": ("workspace", "bazel"),
    # Swift and Apple
    "package.swift": ("manifest", "swift"),
    "package.resolved": ("lockfile", "swift"),
    "podfile": ("manifest", "cocoapods"),
    "podfile.lock": ("lockfile", "cocoapods"),
    "cartfile": ("manifest", "carthage"),
    "cartfile.resolved": ("lockfile", "carthage"),
    # Infrastructure and tools
    ".terraform.lock.hcl": ("lockfile", "terraform"),
    "flake.nix": ("manifest", "nix"),
    "flake.lock": ("lockfile", "nix"),
    "chart.yaml": ("manifest", "helm"),
    "chart.lock": ("lockfile", "helm"),
    ".pre-commit-config.yaml": ("tool-dependencies", "pre-commit"),
    ".pre-commit-config.yml": ("tool-dependencies", "pre-commit"),
    # Repository and runtime extension inputs
    ".gitmodules": ("submodule-config", "git"),
    ".mcp.json": ("runtime-extensions", "mcp"),
    "mcp.json": ("runtime-extensions", "mcp"),
    "plugin.json": ("runtime-extensions", "plugin"),
    "plugins.json": ("runtime-extensions", "plugin"),
    "extensions.json": ("runtime-extensions", "extensions"),
    "dependabot.yml": ("dependency-config", "automation"),
    "dependabot.yaml": ("dependency-config", "automation"),
}

ACTION_USE_RE = re.compile(r"^\s*(?:-\s*)?uses\s*:\s*[\"']?([^\s#\"']+)", re.MULTILINE)
DOCKER_FROM_RE = re.compile(
    r"^\s*FROM\s+(?:--platform=\S+\s+)?([^\s#]+)", re.IGNORECASE | re.MULTILINE
)
IMAGE_RE = re.compile(r"^\s*(?:-\s*)?image\s*:\s*[\"']?([^\s#\"']+)", re.MULTILINE)
MAX_TEXT_BYTES = 5_000_000


class InventoryError(RuntimeError):
    """Raised when a repository root cannot be inspected safely."""


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


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only inventory of dependency and software supply-chain inputs."
    )
    parser.add_argument("root", type=Path, help="Repository or project root to inspect")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    return parser.parse_args(argv)


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def is_link_or_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def safe_root(path: Path) -> Path:
    absolute = Path(os.path.abspath(path.expanduser()))
    if not absolute.is_dir():
        raise InventoryError("root is not a directory")
    for candidate in reversed([absolute, *absolute.parents]):
        if candidate.exists() and is_link_or_reparse_point(candidate):
            raise InventoryError("root traverses a link or reparse point")
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise InventoryError("root cannot be resolved safely") from exc
    if os.path.normcase(str(absolute)) != os.path.normcase(str(resolved)):
        raise InventoryError("root traverses a link or reparse point")
    return resolved


def add_gap(
    gaps: dict[tuple[str, str, str], dict[str, str]],
    *,
    path: str,
    category: str,
    reason: str,
) -> None:
    normalized_path = path.replace("\\", "/") or "."
    key = (normalized_path, category, reason)
    gaps[key] = {
        "path": normalized_path,
        "category": category,
        "reason": reason,
    }


def add_exclusion(
    exclusions: dict[tuple[str, str, str], dict[str, str]],
    *,
    path: str,
    category: str,
    reason: str,
) -> None:
    normalized_path = path.replace("\\", "/") or "."
    key = (normalized_path, category, reason)
    exclusions[key] = {
        "path": normalized_path,
        "category": category,
        "reason": reason,
    }


def read_text(
    path: Path,
    root: Path,
    gaps: dict[tuple[str, str, str], dict[str, str]],
    limit: int = MAX_TEXT_BYTES,
) -> str:
    relative = relative_posix(path, root)
    try:
        size = path.stat(follow_symlinks=False).st_size
        if size > limit:
            add_gap(
                gaps,
                path=relative,
                category="oversized-input",
                reason="Only the bounded text prefix was inspected.",
            )
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        add_gap(
            gaps,
            path=relative,
            category="unreadable-input",
            reason="The file could not be read safely.",
        )
        return ""


def add_item(
    items: dict[tuple[str, str, str, str], dict[str, str]],
    *,
    path: str,
    kind: str,
    ecosystem: str,
    locator: str = "",
) -> None:
    normalized_path = path.replace("\\", "/")
    key = (normalized_path, kind, ecosystem, locator)
    item = {"path": normalized_path, "kind": kind, "ecosystem": ecosystem}
    if locator:
        if kind == "submodule-commit" and re.fullmatch(r"[0-9a-fA-F]{40,64}", locator):
            item["locator"] = locator.lower()
            item["locator_status"] = "immutable-commit"
        else:
            item["locator_status"] = "present-redacted"
    items[key] = item


def classify_file(
    path: Path,
    root: Path,
    gaps: dict[tuple[str, str, str], dict[str, str]],
) -> tuple[str, str] | None:
    relative = relative_posix(path, root)
    relative_lower = relative.lower()
    name_lower = path.name.lower()
    parts_lower = [part.lower() for part in path.relative_to(root).parts]

    if any(
        parts_lower[index : index + 2] == [".github", "workflows"]
        for index in range(max(0, len(parts_lower) - 1))
    ):
        if path.suffix.lower() in {".yml", ".yaml"}:
            return ("ci-workflow", "github-actions")
    if ".github" in parts_lower and "actions" in parts_lower:
        if name_lower in {"action.yml", "action.yaml"}:
            return ("ci-action", "github-actions")
    if relative_lower in {
        ".gitlab-ci.yml",
        ".gitlab-ci.yaml",
        ".travis.yml",
        "bitbucket-pipelines.yml",
        "bitbucket-pipelines.yaml",
        ".circleci/config.yml",
        ".circleci/config.yaml",
    } or name_lower == "jenkinsfile":
        return ("ci-workflow", "ci")
    if fnmatch.fnmatch(name_lower, "azure-pipelines*.yml") or fnmatch.fnmatch(
        name_lower, "azure-pipelines*.yaml"
    ):
        return ("ci-workflow", "azure-pipelines")

    if name_lower == "dockerfile" or name_lower.startswith("dockerfile."):
        return ("container-definition", "container")
    if name_lower.endswith(".dockerfile"):
        return ("container-definition", "container")
    if fnmatch.fnmatch(name_lower, "docker-compose*.yml") or fnmatch.fnmatch(
        name_lower, "docker-compose*.yaml"
    ):
        return ("container-definition", "container")
    if fnmatch.fnmatch(name_lower, "compose*.yml") or fnmatch.fnmatch(
        name_lower, "compose*.yaml"
    ):
        return ("container-definition", "container")
    if name_lower == "devcontainer.json" and ".devcontainer" in parts_lower:
        return ("container-definition", "devcontainer")
    if relative_lower.endswith(".cargo/config.toml") or relative_lower.endswith(
        ".cargo/config"
    ):
        return ("registry-config", "rust")
    if relative_lower.endswith(".vscode/extensions.json"):
        return ("runtime-extensions", "editor")

    exact = EXACT_FILE_RULES.get(name_lower)
    if exact:
        if name_lower == "package.json":
            contents = read_text(path, root, gaps)
            try:
                payload = json.loads(contents)
                if isinstance(payload, dict) and "workspaces" in payload:
                    return ("workspace-manifest", "javascript")
            except (json.JSONDecodeError, TypeError):
                add_gap(
                    gaps,
                    path=relative,
                    category="malformed-input",
                    reason="The JSON manifest could not be parsed.",
                )
        if name_lower in {"cargo.toml", "pyproject.toml"}:
            text = read_text(path, root, gaps)
            workspace_pattern = (
                r"(?m)^\s*\[workspace(?:\.|\])"
                if name_lower == "cargo.toml"
                else r"(?m)^\s*\[tool\.(?:uv|pdm)\.workspace\]"
            )
            if re.search(workspace_pattern, text):
                return ("workspace-manifest", exact[1])
        return exact

    if fnmatch.fnmatch(name_lower, "requirements*.txt") or fnmatch.fnmatch(
        name_lower, "constraints*.txt"
    ):
        return ("manifest", "python")
    if path.suffix.lower() in {".csproj", ".fsproj", ".vbproj"}:
        return ("manifest", "dotnet")
    if path.suffix.lower() in {".sln", ".slnx"}:
        return ("workspace", "dotnet")
    if path.suffix.lower() == ".gemspec":
        return ("manifest", "ruby")
    if path.suffix.lower() == ".cabal":
        return ("manifest", "haskell")
    if path.suffix.lower() == ".tf":
        return ("manifest", "terraform")
    if name_lower.endswith(".gradle") or name_lower.endswith(".gradle.kts"):
        return ("build-definition", "jvm")
    if name_lower.endswith(".spdx") or ".spdx." in name_lower:
        return ("sbom", "spdx")
    if name_lower in {"bom.json", "bom.xml"} or ".cdx." in name_lower:
        return ("sbom", "cyclonedx")
    if path.suffix.lower() in {".yml", ".yaml"}:
        contents = read_text(path, root, gaps)
        if re.search(r"(?m)^\s*apiVersion\s*:", contents) and re.search(
            r"(?m)^\s*(?:-\s*)?image\s*:", contents
        ):
            return ("container-definition", "orchestration")

    return None


def extract_referenced_inputs(
    path: Path,
    root: Path,
    classification: tuple[str, str],
    items: dict[tuple[str, str, str, str], dict[str, str]],
    gaps: dict[tuple[str, str, str], dict[str, str]],
) -> None:
    kind, _ = classification
    if kind not in {"ci-workflow", "ci-action", "container-definition"}:
        return

    source_path = relative_posix(path, root)
    contents = read_text(path, root, gaps)
    if kind in {"ci-workflow", "ci-action"}:
        for locator in ACTION_USE_RE.findall(contents):
            add_item(
                items,
                path=source_path,
                kind="ci-action-reference",
                ecosystem="github-actions",
                locator=locator,
            )
    for locator in DOCKER_FROM_RE.findall(contents):
        add_item(
            items,
            path=source_path,
            kind="container-image",
            ecosystem="oci",
            locator=locator,
        )
    for locator in IMAGE_RE.findall(contents):
        add_item(
            items,
            path=source_path,
            kind="container-image",
            ecosystem="oci",
            locator=locator,
        )


def add_gitmodules_entries(
    gitmodules: Path,
    root: Path,
    items: dict[tuple[str, str, str, str], dict[str, str]],
    gaps: dict[tuple[str, str, str], dict[str, str]],
) -> None:
    parser = configparser.RawConfigParser()
    try:
        parser.read(gitmodules, encoding="utf-8")
    except (configparser.Error, OSError):
        add_gap(
            gaps,
            path=relative_posix(gitmodules, root),
            category="malformed-input",
            reason="The submodule configuration could not be parsed.",
        )
        return

    for section in sorted(parser.sections()):
        if not section.startswith("submodule ") or not parser.has_option(section, "path"):
            continue
        submodule_path = parser.get(section, "path").strip().replace("\\", "/")
        if not submodule_path:
            continue
        base = gitmodules.parent
        requested = Path(submodule_path)
        lexical = Path(os.path.abspath(base / requested))
        if (
            requested.is_absolute()
            or requested.anchor
            or requested.drive
            or ".." in requested.parts
            or not path_is_within(lexical, root)
        ):
            add_gap(
                gaps,
                path=relative_posix(gitmodules, root),
                category="unsafe-repository-path",
                reason="A declared submodule path leaves the inspected root.",
            )
            continue
        relative = relative_posix(lexical, root)
        locator = parser.get(section, "url", fallback="").strip()
        add_item(
            items,
            path=relative,
            kind="submodule",
            ecosystem="git",
            locator=locator,
        )


def add_gitlink_commits(
    root: Path,
    items: dict[tuple[str, str, str, str], dict[str, str]],
    gaps: dict[tuple[str, str, str], dict[str, str]],
) -> None:
    try:
        result = subprocess.run(
            safe_git_command(root, "ls-files", "--stage", "-z", "--", "."),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=safe_git_environment(),
        )
    except (OSError, ValueError):
        add_gap(
            gaps,
            path=".",
            category="git-metadata-unavailable",
            reason="Gitlink metadata could not be inspected.",
        )
        return
    if result.returncode != 0:
        add_gap(
            gaps,
            path=".",
            category="git-metadata-unavailable",
            reason="Gitlink metadata could not be inspected.",
        )
        return

    for entry in result.stdout.split("\0"):
        if not entry or "\t" not in entry:
            continue
        metadata, path = entry.split("\t", 1)
        fields = metadata.split()
        if len(fields) >= 2 and fields[0] == "160000":
            add_item(
                items,
                path=path,
                kind="submodule-commit",
                ecosystem="git",
                locator=fields[1],
            )


def inventory(root: Path) -> dict[str, Any]:
    root = safe_root(root)
    items: dict[tuple[str, str, str, str], dict[str, str]] = {}
    gaps: dict[tuple[str, str, str], dict[str, str]] = {}
    exclusions: dict[tuple[str, str, str], dict[str, str]] = {}

    def record_walk_error(error: OSError) -> None:
        candidate = Path(error.filename) if error.filename else root
        try:
            relative = relative_posix(Path(os.path.abspath(candidate)), root)
        except ValueError:
            relative = "."
        add_gap(
            gaps,
            path=relative,
            category="unreadable-directory",
            reason="A directory could not be enumerated.",
        )

    for current, directory_names, file_names in os.walk(
        root, followlinks=False, onerror=record_walk_error
    ):
        current_path = Path(current)
        kept_directories: list[str] = []
        for directory_name in sorted(directory_names, key=str.lower):
            lowered = directory_name.lower()
            directory_path = current_path / directory_name
            if is_link_or_reparse_point(directory_path):
                add_gap(
                    gaps,
                    path=relative_posix(directory_path, root),
                    category="link-or-reparse-not-followed",
                    reason="A linked directory was not traversed.",
                )
                continue
            if lowered in EXCLUDED_DIRECTORY_NAMES:
                add_exclusion(
                    exclusions,
                    path=relative_posix(directory_path, root),
                    category="generated-or-cache-name-policy",
                    reason=(
                        "The directory was not traversed; confirm it is generated or cached "
                        "before claiming coverage."
                    ),
                )
                continue
            if lowered in VENDORED_DIRECTORY_NAMES:
                add_item(
                    items,
                    path=relative_posix(directory_path, root),
                    kind="vendored-tree",
                    ecosystem="vendored",
                )
                modules_file = directory_path / "modules.txt"
                if modules_file.is_file():
                    add_item(
                        items,
                        path=relative_posix(modules_file, root),
                        kind="lockfile",
                        ecosystem="go",
                    )
                continue
            kept_directories.append(directory_name)
        directory_names[:] = kept_directories

        for file_name in sorted(file_names, key=str.lower):
            path = current_path / file_name
            if is_link_or_reparse_point(path):
                add_gap(
                    gaps,
                    path=relative_posix(path, root),
                    category="link-or-reparse-not-followed",
                    reason="A linked file was not read.",
                )
                continue
            classification = classify_file(path, root, gaps)
            if not classification:
                continue
            kind, ecosystem = classification
            add_item(
                items,
                path=relative_posix(path, root),
                kind=kind,
                ecosystem=ecosystem,
            )
            extract_referenced_inputs(path, root, classification, items, gaps)
            if path.name.lower() == ".gitmodules":
                add_gitmodules_entries(path, root, items, gaps)

    add_gitlink_commits(root, items, gaps)

    sorted_items = sorted(
        items.values(),
        key=lambda item: (
            item["path"].lower(),
            item["kind"],
            item["ecosystem"],
            item.get("locator", ""),
        ),
    )
    by_kind: dict[str, int] = {}
    by_ecosystem: dict[str, int] = {}
    for item in sorted_items:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
        by_ecosystem[item["ecosystem"]] = by_ecosystem.get(item["ecosystem"], 0) + 1

    sorted_gaps = sorted(
        gaps.values(),
        key=lambda gap: (gap["path"].lower(), gap["category"], gap["reason"]),
    )
    by_gap_category: dict[str, int] = {}
    for gap in sorted_gaps:
        by_gap_category[gap["category"]] = by_gap_category.get(gap["category"], 0) + 1

    sorted_exclusions = sorted(
        exclusions.values(),
        key=lambda exclusion: (
            exclusion["path"].lower(),
            exclusion["category"],
            exclusion["reason"],
        ),
    )
    by_exclusion_category: dict[str, int] = {}
    for exclusion in sorted_exclusions:
        category = exclusion["category"]
        by_exclusion_category[category] = by_exclusion_category.get(category, 0) + 1

    return {
        "schemaVersion": 1,
        "root": ".",
        "items": sorted_items,
        "gaps": sorted_gaps,
        "exclusions": sorted_exclusions,
        "summary": {
            "total": len(sorted_items),
            "gap_count": len(sorted_gaps),
            "exclusion_count": len(sorted_exclusions),
            "by_kind": dict(sorted(by_kind.items())),
            "by_ecosystem": dict(sorted(by_ecosystem.items())),
            "by_gap_category": dict(sorted(by_gap_category.items())),
            "by_exclusion_category": dict(sorted(by_exclusion_category.items())),
        },
        "excluded_directory_names": sorted(EXCLUDED_DIRECTORY_NAMES),
        "notes": [
            "Discovery is heuristic and must be supplemented with repository-specific review.",
            "Vendored directory roots are reported but their contents are not traversed.",
            "No package resolution, installation, build, or network request was performed.",
        ],
    }


def render_text(result: dict[str, Any]) -> str:
    lines = [
        f"Root: {result['root']}",
        f"Discovered inputs: {result['summary']['total']}",
        "",
        "KIND\tECOSYSTEM\tPATH\tLOCATOR_STATUS",
    ]
    for item in result["items"]:
        lines.append(
            "\t".join(
                (
                    item["kind"],
                    item["ecosystem"],
                    item["path"],
                    item.get("locator_status", ""),
                )
            )
        )
    lines.extend(("", "Counts by kind:"))
    for kind, count in result["summary"]["by_kind"].items():
        lines.append(f"  {kind}: {count}")
    lines.append("Counts by ecosystem:")
    for ecosystem, count in result["summary"]["by_ecosystem"].items():
        lines.append(f"  {ecosystem}: {count}")
    lines.append("Coverage gaps:")
    if not result["gaps"]:
        lines.append("  none")
    for gap in result["gaps"]:
        lines.append(f"  {gap['category']}\t{gap['path']}\t{gap['reason']}")
    lines.append("Excluded directories requiring confirmation:")
    if not result["exclusions"]:
        lines.append("  none")
    for exclusion in result["exclusions"]:
        lines.append(
            f"  {exclusion['category']}\t{exclusion['path']}\t{exclusion['reason']}"
        )
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = inventory(args.root)
    except InventoryError as exc:
        print(f"error: unsafe or unavailable root ({exc})", file=sys.stderr)
        return 2
    if args.output_format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
