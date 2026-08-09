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


def read_text(path: Path, limit: int = 5_000_000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
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
        item["locator"] = locator
    items[key] = item


def classify_file(path: Path, root: Path) -> tuple[str, str] | None:
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
            try:
                payload = json.loads(read_text(path))
                if isinstance(payload, dict) and "workspaces" in payload:
                    return ("workspace-manifest", "javascript")
            except (json.JSONDecodeError, TypeError):
                pass
        if name_lower in {"cargo.toml", "pyproject.toml"}:
            text = read_text(path)
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
        contents = read_text(path)
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
) -> None:
    kind, _ = classification
    if kind not in {"ci-workflow", "ci-action", "container-definition"}:
        return

    source_path = relative_posix(path, root)
    contents = read_text(path)
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
) -> None:
    parser = configparser.RawConfigParser()
    try:
        parser.read(gitmodules, encoding="utf-8")
    except (configparser.Error, OSError):
        return

    for section in sorted(parser.sections()):
        if not section.startswith("submodule ") or not parser.has_option(section, "path"):
            continue
        submodule_path = parser.get(section, "path").strip().replace("\\", "/")
        if not submodule_path:
            continue
        base = gitmodules.parent
        try:
            resolved = (base / submodule_path).resolve()
            relative = relative_posix(resolved, root)
        except (OSError, ValueError):
            relative = (Path(relative_posix(base, root)) / submodule_path).as_posix()
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
) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage", "-z"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, ValueError):
        return
    if result.returncode != 0:
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
    root = root.resolve()
    items: dict[tuple[str, str, str, str], dict[str, str]] = {}

    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for directory_name in sorted(directory_names, key=str.lower):
            lowered = directory_name.lower()
            directory_path = current_path / directory_name
            if lowered in EXCLUDED_DIRECTORY_NAMES:
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
            classification = classify_file(path, root)
            if not classification:
                continue
            kind, ecosystem = classification
            add_item(
                items,
                path=relative_posix(path, root),
                kind=kind,
                ecosystem=ecosystem,
            )
            extract_referenced_inputs(path, root, classification, items)
            if path.name.lower() == ".gitmodules":
                add_gitmodules_entries(path, root, items)

    add_gitlink_commits(root, items)

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

    return {
        "root": str(root),
        "items": sorted_items,
        "summary": {
            "total": len(sorted_items),
            "by_kind": dict(sorted(by_kind.items())),
            "by_ecosystem": dict(sorted(by_ecosystem.items())),
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
        "KIND\tECOSYSTEM\tPATH\tLOCATOR",
    ]
    for item in result["items"]:
        lines.append(
            "\t".join(
                (
                    item["kind"],
                    item["ecosystem"],
                    item["path"],
                    item.get("locator", ""),
                )
            )
        )
    lines.extend(("", "Counts by kind:"))
    for kind, count in result["summary"]["by_kind"].items():
        lines.append(f"  {kind}: {count}")
    lines.append("Counts by ecosystem:")
    for ecosystem, count in result["summary"]["by_ecosystem"].items():
        lines.append(f"  {ecosystem}: {count}")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.expanduser()
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2

    result = inventory(root)
    if args.output_format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
