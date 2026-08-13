#!/usr/bin/env python3
"""Compare high-signal protected literals without printing their values."""

from __future__ import annotations

import argparse
import bisect
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


MAX_INPUT_BYTES = 20 * 1024 * 1024
MAX_REPORTED_LINES = 20

MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdx", ".mdown"}
HTML_SUFFIXES = {".htm", ".html", ".xhtml"}
SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".dart", ".ex", ".exs", ".fs",
    ".go", ".h", ".hpp", ".java", ".js", ".jsx", ".kt", ".kts", ".php",
    ".py", ".rb", ".rs", ".scala", ".sh", ".sql", ".swift", ".ts", ".tsx",
    ".vue", ".xml", ".yaml", ".yml",
}


@dataclass(frozen=True)
class Occurrence:
    category: str
    value: str
    line: int


class InspectionError(Exception):
    """A safe, user-facing inspection failure."""


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def decode_text(data: bytes) -> str:
    if len(data) > MAX_INPUT_BYTES:
        raise InspectionError("Input exceeds the 20 MiB safety limit.")
    if b"\x00" in data:
        raise InspectionError("Input appears to be binary.")
    try:
        return normalize_newlines(data.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise InspectionError("Input is not valid UTF-8 text.") from exc


def read_text_file(path: Path) -> str:
    try:
        return decode_text(path.read_bytes())
    except OSError as exc:
        raise InspectionError("A requested input file could not be read.") from exc


def line_starts(text: str) -> list[int]:
    starts = [0]
    starts.extend(match.end() for match in re.finditer("\n", text))
    return starts


def line_number(starts: Sequence[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def overlaps(span: tuple[int, int], blocked: Sequence[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < blocked_end and end > blocked_start for blocked_start, blocked_end in blocked)


def add_occurrence(
    occurrences: list[Occurrence],
    blocked: list[tuple[int, int]],
    starts: Sequence[int],
    category: str,
    value: str,
    span: tuple[int, int],
    *,
    reserve: bool = True,
) -> bool:
    if not value or overlaps(span, blocked):
        return False
    occurrences.append(Occurrence(category, value, line_number(starts, span[0])))
    if reserve:
        blocked.append(span)
    return True


def extract_frontmatter(
    text: str,
    occurrences: list[Occurrence],
    blocked: list[tuple[int, int]],
    starts: Sequence[int],
) -> None:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return
    offset = len(lines[0])
    for line in lines[1:]:
        offset += len(line)
        if line.strip() in {"---", "..."}:
            add_occurrence(occurrences, blocked, starts, "frontmatter", text[:offset], (0, offset))
            return


def extract_fenced_code(
    text: str,
    occurrences: list[Occurrence],
    blocked: list[tuple[int, int]],
    starts: Sequence[int],
) -> None:
    lines = text.splitlines(keepends=True)
    offsets: list[int] = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)

    index = 0
    opening_pattern = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})")
    while index < len(lines):
        start = offsets[index]
        match = opening_pattern.match(lines[index])
        if not match or overlaps((start, start + len(lines[index])), blocked):
            index += 1
            continue

        fence = match.group("fence")
        closing_pattern = re.compile(rf"^[ \t]*{re.escape(fence[0])}{{{len(fence)},}}[ \t]*(?:\n)?$")
        end_index = index + 1
        while end_index < len(lines) and not closing_pattern.match(lines[end_index]):
            end_index += 1
        if end_index < len(lines):
            end = offsets[end_index] + len(lines[end_index])
            next_index = end_index + 1
        else:
            end = len(text)
            next_index = len(lines)
        add_occurrence(occurrences, blocked, starts, "fenced-code", text[start:end], (start, end))
        index = next_index


def extract_inline_code(
    text: str,
    occurrences: list[Occurrence],
    blocked: list[tuple[int, int]],
    starts: Sequence[int],
) -> None:
    pattern = re.compile(r"(?P<ticks>`{1,2})(?P<body>[^\n]*?)(?P=ticks)")
    for match in pattern.finditer(text):
        add_occurrence(
            occurrences,
            blocked,
            starts,
            "inline-code",
            match.group(0),
            match.span(0),
        )


def extract_markdown_links(
    text: str,
    occurrences: list[Occurrence],
    blocked: list[tuple[int, int]],
    starts: Sequence[int],
) -> None:
    inline = re.compile(r"!?\[[^\]\n]*\]\(\s*(?P<target><[^>\n]+>|[^\s)\n]+)")
    reference = re.compile(r"(?m)^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(?P<target><[^>\n]+>|\S+)")
    for pattern in (inline, reference):
        for match in pattern.finditer(text):
            add_occurrence(
                occurrences,
                blocked,
                starts,
                "markdown-link-target",
                match.group("target"),
                match.span("target"),
            )


def extract_html(
    text: str,
    occurrences: list[Occurrence],
    blocked: list[tuple[int, int]],
    starts: Sequence[int],
) -> None:
    tag_pattern = re.compile(r"<!--[\s\S]*?-->|<![^>]*>|</?[A-Za-z][^>]*>")
    attribute_pattern = re.compile(
        r"(?P<name>[A-Za-z_:][A-Za-z0-9_.:-]*)\s*=\s*(?P<value>\"[^\"]*\"|'[^']*'|[^\s>]+)"
    )
    for tag in tag_pattern.finditer(text):
        if overlaps(tag.span(0), blocked):
            continue
        tag_text = tag.group(0)
        for attribute in attribute_pattern.finditer(tag_text):
            start = tag.start() + attribute.start()
            end = tag.start() + attribute.end()
            occurrences.append(
                Occurrence(
                    "html-attribute",
                    attribute.group(0),
                    line_number(starts, start),
                )
            )
        add_occurrence(
            occurrences,
            blocked,
            starts,
            "html-tag",
            tag_text,
            tag.span(0),
        )


def extract_pattern(
    text: str,
    pattern: re.Pattern[str],
    category: str,
    occurrences: list[Occurrence],
    blocked: list[tuple[int, int]],
    starts: Sequence[int],
    group: int | str = 0,
) -> None:
    for match in pattern.finditer(text):
        add_occurrence(
            occurrences,
            blocked,
            starts,
            category,
            match.group(group),
            match.span(group),
        )


def extract_protected(text: str, format_name: str) -> list[Occurrence]:
    occurrences: list[Occurrence] = []
    blocked: list[tuple[int, int]] = []
    starts = line_starts(text)

    if format_name == "markdown":
        extract_frontmatter(text, occurrences, blocked, starts)
        extract_fenced_code(text, occurrences, blocked, starts)
        extract_inline_code(text, occurrences, blocked, starts)
        extract_markdown_links(text, occurrences, blocked, starts)
    elif format_name == "html":
        extract_html(text, occurrences, blocked, starts)

    placeholder_patterns = (
        re.compile(r"\{\{[^{}\n]+\}\}"),
        re.compile(r"\$\{[^{}\n]+\}"),
        re.compile(r"<%[=#-]?[\s\S]*?%>"),
        re.compile(r"%\([A-Za-z_][A-Za-z0-9_]*\)[#0 +\-]?(?:\d+)?(?:\.\d+)?[A-Za-z]"),
        re.compile(r"%(?:\d+\$)?[#0 +\-]?(?:\d+)?(?:\.\d+)?[A-Za-z]"),
        re.compile(r"\{(?:\d+|[A-Za-z_][A-Za-z0-9_.-]*)(?:\s*,[^{}\n]+|:[^{}\n]+)?\}"),
    )
    for pattern in placeholder_patterns:
        extract_pattern(text, pattern, "placeholder", occurrences, blocked, starts)

    patterns: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("url", re.compile(r"(?:https?|ftp)://[^\s<>\"'`)\]]+")),
        ("path", re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*")),
        ("path", re.compile(r"(?<![A-Za-z0-9_])(?:\.\.?/|/)(?:[A-Za-z0-9_.~@%+,=-]+/)*[A-Za-z0-9_.~@%+,=-]+/?")),
        ("path", re.compile(r"(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,12}(?![A-Za-z0-9_.-])")),
        ("cli-flag", re.compile(r"(?<![A-Za-z0-9_-])--?[A-Za-z][A-Za-z0-9-]*(?:=[^\s]+)?")),
        ("date", re.compile(r"(?<!\d)(?:19|20)\d{2}-\d{2}-\d{2}(?!\d)")),
        ("date", re.compile(r"(?<!\d)\d{1,2}[/.]\d{1,2}[/.]\d{2,4}(?!\d)")),
        ("version", re.compile(r"(?<![A-Za-z0-9_])v?\d+\.\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.-]+)?(?![A-Za-z0-9_])")),
        ("number-with-unit", re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:[.,]\d+)?\s?(?:%|ms|s|min|h|B|KB|MB|GB|TB|KiB|MiB|GiB|Hz|kHz|MHz|GHz|px|em|rem|pt|kg|g|mg|km|m|cm|mm|°C|°F)(?![A-Za-z0-9_])", re.IGNORECASE)),
        ("number", re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:[.,]\d+)*(?![A-Za-z0-9_])")),
    )
    for category, pattern in patterns:
        extract_pattern(text, pattern, category, occurrences, blocked, starts)

    return occurrences


def detect_format(requested: str, path_hint: str) -> str:
    if requested != "auto":
        return requested
    suffix = Path(path_hint).suffix.lower()
    if suffix in MARKDOWN_SUFFIXES:
        return "markdown"
    if suffix in HTML_SUFFIXES:
        return "html"
    if suffix in SOURCE_SUFFIXES:
        return "source"
    return "text"


def occurrence_index(occurrences: Iterable[Occurrence]) -> dict[str, dict[str, list[int]]]:
    index: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for occurrence in occurrences:
        index[occurrence.category][occurrence.value].append(occurrence.line)
    return index


def compact_lines(lines: Sequence[int]) -> tuple[list[int], bool]:
    ordered = sorted(lines)
    return ordered[:MAX_REPORTED_LINES], len(ordered) > MAX_REPORTED_LINES


def compare_occurrences(before: list[Occurrence], after: list[Occurrence]) -> list[dict[str, object]]:
    before_index = occurrence_index(before)
    after_index = occurrence_index(after)
    internal: list[tuple[str, int, int, str, list[int], list[int]]] = []

    categories = sorted(set(before_index) | set(after_index))
    for category in categories:
        values = set(before_index.get(category, {})) | set(after_index.get(category, {}))
        for value in values:
            before_lines = before_index.get(category, {}).get(value, [])
            after_lines = after_index.get(category, {}).get(value, [])
            if len(before_lines) == len(after_lines):
                continue
            first_before = min(before_lines) if before_lines else sys.maxsize
            first_after = min(after_lines) if after_lines else sys.maxsize
            internal.append((category, first_before, first_after, value, before_lines, after_lines))

    internal.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    findings: list[dict[str, object]] = []
    for index, (category, _first_before, _first_after, _value, before_lines, after_lines) in enumerate(internal, start=1):
        if before_lines and not after_lines:
            change = "removed"
        elif after_lines and not before_lines:
            change = "added"
        else:
            change = "count-changed"
        before_reported, before_truncated = compact_lines(before_lines)
        after_reported, after_truncated = compact_lines(after_lines)
        findings.append(
            {
                "id": f"F{index:03d}",
                "category": category,
                "change": change,
                "before_count": len(before_lines),
                "after_count": len(after_lines),
                "before_lines": before_reported,
                "after_lines": after_reported,
                "before_lines_truncated": before_truncated,
                "after_lines_truncated": after_truncated,
            }
        )
    return findings


def category_counts(occurrences: Iterable[Occurrence]) -> dict[str, int]:
    return dict(sorted(Counter(item.category for item in occurrences).items()))


def run_git(root: Path, args: Sequence[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise InspectionError("Git is unavailable.") from exc
    if result.returncode != 0:
        raise InspectionError("Git inspection failed.")
    return result.stdout


def load_git_pair(base: str, repository_path: str) -> tuple[str, str, str]:
    if not base or base.startswith("-") or "\x00" in base:
        raise InspectionError("The Git base is invalid.")
    normalized = repository_path.replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    if pure_path.is_absolute() or not pure_path.parts or ".." in pure_path.parts:
        raise InspectionError("The repository path must be a safe relative path.")

    try:
        root_output = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise InspectionError("Git is unavailable.") from exc
    if root_output.returncode != 0:
        raise InspectionError("The current directory is not inside a Git repository.")
    try:
        root = Path(root_output.stdout.decode("utf-8").strip()).resolve()
    except UnicodeDecodeError as exc:
        raise InspectionError("The Git repository path is not valid UTF-8.") from exc

    current = (root / Path(*pure_path.parts)).resolve()
    try:
        current.relative_to(root)
    except ValueError as exc:
        raise InspectionError("The repository path escapes the repository root.") from exc

    before = decode_text(run_git(root, ["cat-file", "-p", f"{base}:{pure_path.as_posix()}"]))
    after = read_text_file(current)
    return before, after, pure_path.as_posix()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare protected prose literals without printing their values."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--before", help="Original UTF-8 text file.")
    mode.add_argument("--git-base", help="Git revision containing the original file.")
    parser.add_argument("--after", help="Rewritten UTF-8 text file for --before mode.")
    parser.add_argument("--path", help="Repository-relative path for --git-base mode.")
    parser.add_argument(
        "--format",
        choices=("auto", "markdown", "html", "text", "source"),
        default="auto",
        help="Input format. The default infers it from the path suffix.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def load_inputs(args: argparse.Namespace, parser: argparse.ArgumentParser) -> tuple[str, str, str]:
    if args.before:
        if not args.after or args.path:
            parser.error("--before requires --after and cannot be combined with --path")
        return read_text_file(Path(args.before)), read_text_file(Path(args.after)), args.after
    if not args.path or args.after:
        parser.error("--git-base requires --path and cannot be combined with --after")
    return load_git_pair(args.git_base, args.path)


def print_human(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    finding_count = summary["finding_count"]
    if finding_count == 0:
        print(f"PASS: no protected-content differences ({payload['format']}).")
        return
    print(f"REVIEW: {finding_count} protected-content difference(s) ({payload['format']}).")
    findings = payload["findings"]
    assert isinstance(findings, list)
    for finding in findings:
        assert isinstance(finding, dict)
        before_lines = ",".join(str(line) for line in finding["before_lines"]) or "-"
        after_lines = ",".join(str(line) for line in finding["after_lines"]) or "-"
        if finding["before_lines_truncated"]:
            before_lines += ",..."
        if finding["after_lines_truncated"]:
            after_lines += ",..."
        print(
            f"{finding['id']} category={finding['category']} change={finding['change']} "
            f"before_count={finding['before_count']} after_count={finding['after_count']} "
            f"before_lines={before_lines} after_lines={after_lines}"
        )
    print("Values are intentionally redacted; inspect the reported locations locally.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        before_text, after_text, path_hint = load_inputs(args, parser)
        format_name = detect_format(args.format, path_hint)
        before_occurrences = extract_protected(before_text, format_name)
        after_occurrences = extract_protected(after_text, format_name)
        findings = compare_occurrences(before_occurrences, after_occurrences)
        payload: dict[str, object] = {
            "status": "pass" if not findings else "review",
            "format": format_name,
            "summary": {
                "finding_count": len(findings),
                "before_occurrence_count": len(before_occurrences),
                "after_occurrence_count": len(after_occurrences),
            },
            "coverage": {
                "before_categories": category_counts(before_occurrences),
                "after_categories": category_counts(after_occurrences),
            },
            "findings": findings,
        }
    except InspectionError as exc:
        if args.json:
            print(json.dumps({"status": "error", "message": str(exc)}, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(payload)
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
