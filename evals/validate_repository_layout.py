#!/usr/bin/env python3
"""Validate the repository's flat skill and evaluation layout.

This maintenance check is intentionally read-only and uses only the Python
standard library. It validates repository structure and focused metadata; the
plugin and skill validators remain responsible for their complete schemas.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Iterable


SKILL_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK = re.compile(r"\[[^\]\n]*\]\((?:<([^>\n]+)>|([^\s)]+))")
FRONTMATTER_NAME = re.compile(r"^name\s*:\s*(.*?)\s*$")
CATALOG_SUPPORT_LINKS = {"../../evals/behavior-first-contract.md"}


@dataclass
class ValidationResult:
    """Collected validation diagnostics and useful coverage counts."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skill_count: int = 0
    eval_count: int = 0
    group_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_link_or_reparse(path: Path) -> bool:
    """Return whether *path* is a symlink or Windows reparse point."""

    try:
        metadata = path.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & reparse_flag)


def _read_utf8(path: Path, label: str, result: ValidationResult) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        result.errors.append(f"cannot read {label} as UTF-8 ({error.__class__.__name__})")
        return None


def _load_json(path: Path, label: str, result: ValidationResult) -> object | None:
    text = _read_utf8(path, label, result)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        result.errors.append(
            f"{label} is invalid JSON at line {error.lineno}, column {error.colno}"
        )
        return None


def _unquote_yaml_scalar(value: str) -> str | None:
    """Parse the small string-scalar subset allowed for a skill name."""

    value = value.strip()
    if not value or value[0] in "|>[{&*!":
        return None
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, str) else None
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            return None
        return value[1:-1].replace("''", "'")
    # A comment begins only when YAML whitespace precedes the hash.
    value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
    if not value or value.lower() in {"null", "~", "true", "false"}:
        return None
    return value


def _frontmatter_name(
    skill_file: Path, slug: str, result: ValidationResult
) -> str | None:
    label = f"skills/{slug}/SKILL.md"
    text = _read_utf8(skill_file, label, result)
    if text is None:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        result.errors.append(f"{label} is missing YAML frontmatter")
        return None
    try:
        closing = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration:
        result.errors.append(f"{label} has unterminated YAML frontmatter")
        return None

    names: list[str | None] = []
    for line in lines[1:closing]:
        if line[:1].isspace():
            continue
        match = FRONTMATTER_NAME.match(line)
        if match:
            names.append(_unquote_yaml_scalar(match.group(1)))
    if not names:
        result.errors.append(f"{label} frontmatter is missing a string name")
        return None
    if len(names) > 1:
        result.errors.append(f"{label} frontmatter has duplicate name fields")
        return None
    if names[0] is None:
        result.errors.append(f"{label} frontmatter name must be a string slug")
        return None
    return names[0]


def _walk_skill_manifests(
    skills_root: Path, result: ValidationResult
) -> Iterable[Path]:
    """Yield SKILL.md files and report linked directories before pruning them."""

    for directory, child_dirs, files in os.walk(skills_root, topdown=True, followlinks=False):
        base = Path(directory)
        traversable: list[str] = []
        for child in sorted(child_dirs):
            child_path = base / child
            if _is_link_or_reparse(child_path):
                relative = child_path.relative_to(skills_root)
                # Direct skill links are already reported by _validate_skills.
                # Nested links must also be visible because pruning them could
                # otherwise conceal an additional SKILL.md package.
                if len(relative.parts) > 1:
                    shown = PurePosixPath(*relative.parts).as_posix()
                    result.errors.append(
                        "nested linked directory is not allowed under skills/: "
                        f"skills/{shown}/"
                    )
                continue
            traversable.append(child)
        child_dirs[:] = traversable
        if "SKILL.md" in files:
            yield base / "SKILL.md"


def _validate_skills(root: Path, result: ValidationResult) -> set[str]:
    skills_root = root / "skills"
    if not skills_root.is_dir() or _is_link_or_reparse(skills_root):
        result.errors.append("skills/ is missing, unreadable, or not a real directory")
        return set()

    slugs: set[str] = set()
    direct_dirs = sorted(
        (item for item in skills_root.iterdir() if item.is_dir()), key=lambda item: item.name
    )
    for directory in direct_dirs:
        slug = directory.name
        if slug.startswith("."):
            result.errors.append(f"hidden skill directory is not allowed: skills/{slug}/")
            continue
        slugs.add(slug)
        if not SKILL_SLUG.fullmatch(slug):
            result.errors.append(f"invalid immediate skill directory slug: skills/{slug}/")
        if _is_link_or_reparse(directory):
            result.errors.append(f"skill directory must not be a link or reparse point: skills/{slug}/")
            continue
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file() or _is_link_or_reparse(skill_file):
            result.errors.append(f"immediate skill directory is missing a real SKILL.md: skills/{slug}/")
            continue
        declared_name = _frontmatter_name(skill_file, slug, result)
        if declared_name is not None and declared_name != slug:
            result.errors.append(
                f"frontmatter name mismatch in skills/{slug}/SKILL.md: expected {slug!r}"
            )

    for manifest in sorted(_walk_skill_manifests(skills_root, result)):
        relative = manifest.relative_to(skills_root)
        parts = relative.parts
        if len(parts) != 2 or parts[1] != "SKILL.md":
            shown = PurePosixPath(*parts).as_posix()
            result.errors.append(
                f"nested skill package is not allowed: skills/{shown}; "
                "SKILL.md must be one directory below skills/"
            )
        elif parts[0].startswith("."):
            result.errors.append(
                f"hidden skill package is not allowed: skills/{PurePosixPath(*parts).as_posix()}"
            )

    result.skill_count = len(slugs)
    return slugs


def _validate_evals(root: Path, skill_slugs: set[str], result: ValidationResult) -> set[str]:
    evals_root = root / "evals"
    if not evals_root.is_dir() or _is_link_or_reparse(evals_root):
        result.errors.append("evals/ is missing, unreadable, or not a real directory")
        return set()

    eval_slugs: set[str] = set()
    direct_dirs = sorted(
        (item for item in evals_root.iterdir() if item.is_dir()), key=lambda item: item.name
    )
    for directory in direct_dirs:
        slug = directory.name
        if slug.startswith("."):
            result.errors.append(f"hidden evaluation directory is not allowed: evals/{slug}/")
            continue
        eval_slugs.add(slug)
        if _is_link_or_reparse(directory):
            result.errors.append(
                f"evaluation directory must not be a link or reparse point: evals/{slug}/"
            )
            continue
        manifest = directory / "cases.json"
        if not manifest.is_file() or _is_link_or_reparse(manifest):
            result.errors.append(f"evaluation suite is missing a real cases.json: evals/{slug}/")

    for slug in sorted(skill_slugs - eval_slugs):
        result.errors.append(f"missing evaluation suite for skill {slug}: evals/{slug}/cases.json")
    for slug in sorted(eval_slugs - skill_slugs):
        result.errors.append(f"unknown evaluation suite has no matching skill: evals/{slug}/")

    result.eval_count = len(eval_slugs)
    return eval_slugs


def _validate_groupings(
    root: Path, skill_slugs: set[str], strict_groups: bool, result: ValidationResult
) -> dict[str, list[str]]:
    configuration = _load_json(root / "skills.sh.json", "skills.sh.json", result)
    if not isinstance(configuration, dict):
        if configuration is not None:
            result.errors.append("skills.sh.json must contain a JSON object")
        return {}

    if configuration.get("notGrouped") != "bottom":
        result.errors.append('skills.sh.json must keep notGrouped set to "bottom"')

    groupings = configuration.get("groupings")
    if not isinstance(groupings, list):
        result.errors.append("skills.sh.json groupings must be an array")
        return {}

    titles: list[str] = []
    configured_slugs: list[str] = []
    assignments: dict[str, list[str]] = {}
    for index, grouping in enumerate(groupings):
        label = f"skills.sh.json groupings[{index}]"
        if not isinstance(grouping, dict):
            result.errors.append(f"{label} must be an object")
            continue
        title = grouping.get("title")
        if not isinstance(title, str) or not title.strip():
            result.errors.append(f"{label}.title must be a non-empty string")
            valid_title: str | None = None
        else:
            titles.append(title)
            valid_title = title
            assignments.setdefault(title, [])
        grouped_skills = grouping.get("skills")
        if not isinstance(grouped_skills, list):
            result.errors.append(f"{label}.skills must be an array")
            continue
        for skill_index, slug in enumerate(grouped_skills):
            if not isinstance(slug, str) or not slug:
                result.errors.append(
                    f"{label}.skills[{skill_index}] must be a non-empty string slug"
                )
                continue
            configured_slugs.append(slug)
            if valid_title is not None:
                assignments[valid_title].append(slug)

    for title, count in sorted(Counter(titles).items()):
        if count > 1:
            result.errors.append(f"duplicate grouping title in skills.sh.json: {title!r}")
    for slug, count in sorted(Counter(configured_slugs).items()):
        if count > 1:
            result.errors.append(f"duplicate grouped skill in skills.sh.json: {slug}")
    for slug in sorted(set(configured_slugs) - skill_slugs):
        result.errors.append(f"unknown grouped skill in skills.sh.json: {slug}")

    ungrouped = sorted(skill_slugs - set(configured_slugs))
    if ungrouped:
        diagnostic = "ungrouped skills in skills.sh.json: " + ", ".join(ungrouped)
        if strict_groups:
            result.errors.append(diagnostic)
        else:
            result.warnings.append(diagnostic)

    result.group_count = len(titles)
    return assignments


def _markdown_targets(markdown: str) -> list[str]:
    targets: list[str] = []
    for match in MARKDOWN_LINK.finditer(markdown):
        raw = match.group(1) or match.group(2)
        targets.append(raw.replace("\\", "/"))
    return targets


def _validate_catalog(
    root: Path,
    skill_slugs: set[str],
    eval_slugs: set[str],
    group_assignments: dict[str, list[str]],
    result: ValidationResult,
) -> None:
    catalog_path = root / "docs" / "skills" / "README.md"
    catalog = _read_utf8(catalog_path, "docs/skills/README.md", result)
    if catalog is None:
        return

    targets = Counter(_markdown_targets(catalog))
    expected_skill_links = {
        f"../../skills/{slug}/SKILL.md" for slug in skill_slugs
    }
    expected_eval_links = {
        f"../../evals/{slug}/cases.json" for slug in eval_slugs
    }
    expected_links = expected_skill_links | expected_eval_links
    catalog_package_links = {
        target
        for target in targets
        if target.startswith("../../skills/") or target.startswith("../../evals/")
    }

    for target in sorted(expected_links):
        count = targets[target]
        if count == 0:
            result.errors.append(f"catalog is missing link: {target}")
        elif count > 1:
            result.errors.append(f"catalog contains duplicate link: {target}")
    for target in sorted(catalog_package_links - expected_links - CATALOG_SUPPORT_LINKS):
        result.errors.append(f"catalog contains unknown skill or eval link: {target}")

    heading_matches = list(
        re.finditer(r"^##\s+(.+?)\s*$", catalog, flags=re.MULTILINE)
    )
    headings = Counter(match.group(1).strip() for match in heading_matches)
    sections: dict[str, str] = {}
    for index, match in enumerate(heading_matches):
        title = match.group(1).strip()
        end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(catalog)
        )
        if headings[title] == 1:
            sections[title] = catalog[match.end():end]

    for title in sorted(group_assignments):
        count = headings[title]
        if count == 0:
            result.errors.append(f"catalog is missing grouping heading: {title}")
        elif count > 1:
            result.errors.append(f"catalog contains duplicate grouping heading: {title}")

    assignment_counts = Counter(
        slug for slugs in group_assignments.values() for slug in slugs
    )
    for title in sorted(group_assignments):
        section = sections.get(title)
        if section is None:
            continue
        section_targets = Counter(_markdown_targets(section))
        for slug in sorted(group_assignments[title]):
            # Duplicate and unknown assignments have their own authoritative
            # grouping diagnostics; section placement is meaningful only for
            # a known skill assigned exactly once.
            if assignment_counts[slug] != 1 or slug not in skill_slugs:
                continue
            expected = (
                f"../../skills/{slug}/SKILL.md",
                f"../../evals/{slug}/cases.json",
            )
            for target in expected:
                if section_targets[target] != 1:
                    result.errors.append(
                        f"catalog link for {slug} must appear in its "
                        f"{title!r} grouping section: {target}"
                    )


def _validate_plugin_manifest(root: Path, result: ValidationResult) -> None:
    manifest = _load_json(
        root / ".codex-plugin" / "plugin.json",
        ".codex-plugin/plugin.json",
        result,
    )
    if not isinstance(manifest, dict):
        if manifest is not None:
            result.errors.append(".codex-plugin/plugin.json must contain a JSON object")
        return
    if manifest.get("skills") != "./skills/":
        result.errors.append(
            '.codex-plugin/plugin.json skills must remain exactly "./skills/"'
        )


def validate_repository(root: Path, *, strict_groups: bool = False) -> ValidationResult:
    """Validate *root* without modifying it and return structured diagnostics."""

    result = ValidationResult()
    skill_slugs = _validate_skills(root, result)
    eval_slugs = _validate_evals(root, skill_slugs, result)
    group_assignments = _validate_groupings(root, skill_slugs, strict_groups, result)
    _validate_catalog(root, skill_slugs, eval_slugs, group_assignments, result)
    _validate_plugin_manifest(root, result)
    return result


def _print_result(result: ValidationResult) -> None:
    for warning in sorted(set(result.warnings)):
        print(f"WARNING: {warning}")
    for error in sorted(set(result.errors)):
        print(f"ERROR: {error}")
    if result.ok:
        print(
            "PASS: repository layout is valid "
            f"({result.skill_count} skills, {result.eval_count} eval suites, "
            f"{result.group_count} groups)"
        )
    else:
        print(
            "FAIL: repository layout has "
            f"{len(set(result.errors))} error(s) "
            f"({result.skill_count} skills, {result.eval_count} eval suites)"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the flat skill, eval, grouping, and catalog layout."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of evals/)",
    )
    parser.add_argument(
        "--strict-groups",
        action="store_true",
        help="treat skills omitted from Skills.sh groups as errors",
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

    result = validate_repository(root, strict_groups=arguments.strict_groups)
    _print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
