#!/usr/bin/env python3
"""Compare high-signal protected literals without printing their values."""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


MAX_INPUT_BYTES = 20 * 1024 * 1024
MAX_REPORTED_LINES = 20
MAX_MARKDOWN_LINK_SCAN = 64 * 1024
MAX_MARKDOWN_PAREN_DEPTH = 32
MAX_MARKDOWN_BRACKET_DEPTH = 1024
MAX_MARKDOWN_SCAN_WORK = 2 * MAX_INPUT_BYTES
MAX_MARKDOWN_BACKTICK_RUNS = 100_000
MAX_PROTECTED_OCCURRENCES = 50_000
MAX_TEXT_LINES = 250_000

MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdx", ".mdown"}
HTML_SUFFIXES = {".htm", ".html", ".xhtml"}
TEMPLATE_SUFFIXES = {
    ".ejs", ".erb", ".hbs", ".handlebars", ".j2", ".jinja", ".jinja2",
    ".liquid", ".mustache", ".njk", ".nunjucks", ".twig",
}
SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".dart", ".ex", ".exs", ".fs",
    ".go", ".h", ".hpp", ".java", ".js", ".jsx", ".kt", ".kts", ".php",
    ".py", ".rb", ".rs", ".scala", ".sh", ".sql", ".swift", ".ts", ".tsx",
    ".vue", ".xml", ".yaml", ".yml",
}

COMPLEX_LOCALIZATION_PATTERNS = (
    re.compile(r"\{[^{}\n,]{1,128},\s*(?:plural|selectordinal|select)\s*,", re.IGNORECASE),
    re.compile(r"\{\s*\$[A-Za-z][A-Za-z0-9_-]*\s*->"),
    re.compile(r"(?m)^\s*(?:msgid_plural|nplurals\s*=)"),
)
HTML_AUTOLINK_SCHEMES = ("http:", "https:", "ftp:", "mailto:")


@dataclass(frozen=True)
class Occurrence:
    category: str
    value: str
    line: int


class InspectionError(Exception):
    """A safe, user-facing inspection failure."""


@dataclass
class ScanBudget:
    remaining: int

    def consume(self, amount: int) -> None:
        self.remaining -= amount
        if self.remaining < 0:
            raise InspectionError("Markdown structure exceeds the safe scan-work limit.")


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
        path_metadata = path.lstat()
        if stat.S_ISLNK(path_metadata.st_mode):
            raise InspectionError("A requested input is a symbolic link.")
        if not stat.S_ISREG(path_metadata.st_mode):
            raise InspectionError("A requested input is not a regular file.")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise InspectionError("A requested input is not a regular file.")
            if metadata.st_size > MAX_INPUT_BYTES:
                raise InspectionError("Input exceeds the 20 MiB safety limit.")
            data = stream.read(MAX_INPUT_BYTES + 1)
        return decode_text(data)
    except InspectionError:
        raise
    except OSError as exc:
        raise InspectionError("A requested input file could not be read.") from exc


def line_starts(text: str) -> list[int]:
    starts = [0]
    starts.extend(match.end() for match in re.finditer("\n", text))
    return starts


def line_number(starts: Sequence[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def overlaps(span: tuple[int, int], blocked: bytearray) -> bool:
    start, end = span
    return blocked.find(1, start, end) >= 0


def add_occurrence(
    occurrences: list[Occurrence],
    blocked: bytearray,
    starts: Sequence[int],
    category: str,
    value: str,
    span: tuple[int, int],
    *,
    reserve: bool = True,
) -> bool:
    if not value or overlaps(span, blocked):
        return False
    if len(occurrences) >= MAX_PROTECTED_OCCURRENCES:
        raise InspectionError("Protected-content occurrence count exceeds the safety limit.")
    occurrences.append(Occurrence(category, value, line_number(starts, span[0])))
    if reserve:
        start, end = span
        blocked[start:end] = b"\x01" * (end - start)
    return True


def extract_frontmatter(
    text: str,
    occurrences: list[Occurrence],
    blocked: bytearray,
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
    blocked: bytearray,
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
        info_string = lines[index][match.end():].rstrip("\r\n")
        if fence[0] == "`" and "`" in info_string:
            index += 1
            continue
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
    blocked: bytearray,
    starts: Sequence[int],
) -> None:
    runs: list[tuple[int, int, int, bool]] = []
    closing_runs_by_length: dict[int, list[int]] = defaultdict(list)
    for match in re.finditer(r"`+", text):
        raw_start, end = match.span(0)
        if overlaps((raw_start, end), blocked):
            continue
        if len(runs) >= MAX_MARKDOWN_BACKTICK_RUNS:
            raise InspectionError("Markdown backtick run count exceeds the safety limit.")
        raw_length = end - raw_start
        escaped = is_escaped(text, raw_start)
        run_index = len(runs)
        runs.append((raw_start, end, raw_length, escaped))
        closing_runs_by_length[raw_length].append(run_index)

    run_index = 0
    while run_index < len(runs):
        raw_start, _opening_end, raw_length, escaped = runs[run_index]
        opening = raw_start + 1 if escaped else raw_start
        delimiter_length = raw_length - 1 if escaped else raw_length
        if delimiter_length <= 0:
            run_index += 1
            continue

        candidates = closing_runs_by_length.get(delimiter_length, [])
        candidate_offset = bisect.bisect_right(candidates, run_index)
        if candidate_offset >= len(candidates):
            run_index += 1
            continue
        closing_index = candidates[candidate_offset]
        closing_end = runs[closing_index][1]
        span = (opening, closing_end)
        if add_occurrence(
            occurrences,
            blocked,
            starts,
            "inline-code",
            text[opening:closing_end],
            span,
        ):
            run_index = closing_index + 1
        else:
            run_index += 1


def is_escaped(text: str, offset: int) -> bool:
    backslashes = 0
    cursor = offset - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def scan_angle_destination(
    text: str,
    start: int,
    limit: int,
    budget: ScanBudget,
) -> tuple[int, int] | None:
    cursor = start + 1
    scan_start = cursor
    while cursor < limit and text[cursor] != "\n":
        if text[cursor] == "\\" and cursor + 1 < limit:
            cursor += 2
            continue
        if text[cursor] == ">":
            budget.consume(max(1, cursor - scan_start + 1))
            return start, cursor + 1
        cursor += 1
    budget.consume(max(1, cursor - scan_start))
    if cursor == limit and limit < len(text):
        raise InspectionError("Markdown link structure exceeds the safety limit.")
    return None


def scan_inline_destination(
    text: str,
    opening_parenthesis: int,
    budget: ScanBudget,
) -> tuple[int, int] | None:
    limit = min(len(text), opening_parenthesis + MAX_MARKDOWN_LINK_SCAN)
    cursor = opening_parenthesis + 1
    scan_start = cursor
    while cursor < limit and text[cursor] in " \t\n":
        cursor += 1
    if cursor >= limit:
        budget.consume(max(1, cursor - scan_start))
        if limit < len(text):
            raise InspectionError("Markdown link structure exceeds the safety limit.")
        return None
    if text[cursor] == "<":
        budget.consume(max(1, cursor - scan_start))
        return scan_angle_destination(text, cursor, limit, budget)

    start = cursor
    depth = 0
    while cursor < limit:
        character = text[cursor]
        if character == "\\" and cursor + 1 < limit:
            cursor += 2
            continue
        if character == "(" and not is_escaped(text, cursor):
            depth += 1
            if depth > MAX_MARKDOWN_PAREN_DEPTH:
                budget.consume(max(1, cursor - scan_start + 1))
                raise InspectionError("Markdown link nesting exceeds the safety limit.")
        elif character == ")" and not is_escaped(text, cursor):
            if depth == 0:
                budget.consume(max(1, cursor - scan_start + 1))
                return (start, cursor) if cursor > start else None
            depth -= 1
        elif character in " \t\n" and depth == 0:
            budget.consume(max(1, cursor - scan_start + 1))
            return (start, cursor) if cursor > start else None
        cursor += 1
    budget.consume(max(1, cursor - scan_start))
    if cursor == limit and limit < len(text):
        raise InspectionError("Markdown link structure exceeds the safety limit.")
    return None


def scan_reference_destination(
    text: str,
    start: int,
    line_end: int,
    budget: ScanBudget,
) -> tuple[int, int] | None:
    limit = min(line_end, start + MAX_MARKDOWN_LINK_SCAN)
    cursor = start
    scan_start = cursor
    while cursor < limit and text[cursor] in " \t":
        cursor += 1
    if cursor >= limit:
        budget.consume(max(1, cursor - scan_start))
        if limit < line_end:
            raise InspectionError("Markdown link structure exceeds the safety limit.")
        return None
    if text[cursor] == "<":
        budget.consume(max(1, cursor - scan_start))
        return scan_angle_destination(text, cursor, limit, budget)

    destination_start = cursor
    depth = 0
    while cursor < limit:
        character = text[cursor]
        if character == "\\" and cursor + 1 < limit:
            cursor += 2
            continue
        if character == "(":
            depth += 1
            if depth > MAX_MARKDOWN_PAREN_DEPTH:
                budget.consume(max(1, cursor - scan_start + 1))
                raise InspectionError("Markdown link nesting exceeds the safety limit.")
        elif character == ")":
            if depth == 0:
                break
            depth -= 1
        elif character in " \t" and depth == 0:
            break
        cursor += 1
    budget.consume(max(1, cursor - scan_start))
    if (cursor == limit and limit < line_end) or cursor == destination_start or depth != 0:
        if cursor == limit and limit < line_end:
            raise InspectionError("Markdown link structure exceeds the safety limit.")
        return None
    return destination_start, cursor


def extract_markdown_links(
    text: str,
    occurrences: list[Occurrence],
    blocked: bytearray,
    starts: Sequence[int],
) -> None:
    budget = ScanBudget(MAX_MARKDOWN_SCAN_WORK)
    bracket_stack: list[int] = []
    for cursor, character in enumerate(text):
        if blocked[cursor] or character not in "[]" or is_escaped(text, cursor):
            continue
        if character == "[":
            bracket_stack.append(cursor)
            if len(bracket_stack) > MAX_MARKDOWN_BRACKET_DEPTH:
                raise InspectionError("Markdown bracket nesting exceeds the safety limit.")
            continue
        if not bracket_stack:
            continue
        opening = bracket_stack.pop()
        if cursor + 1 >= len(text) or text[cursor + 1] != "(":
            continue
        if cursor - opening > MAX_MARKDOWN_LINK_SCAN:
            raise InspectionError("Markdown link structure exceeds the safety limit.")
        target = scan_inline_destination(text, cursor + 1, budget)
        if target is not None:
            add_occurrence(
                occurrences,
                blocked,
                starts,
                "markdown-link-target",
                text[target[0]:target[1]],
                target,
            )

    definition = re.compile(r"(?m)^[ \t]{0,3}\[(?:\\.|[^\]\n])+\]:")
    for match in definition.finditer(text):
        line_end = text.find("\n", match.end())
        if line_end < 0:
            line_end = len(text)
        target = scan_reference_destination(text, match.end(), line_end, budget)
        if target is not None:
            add_occurrence(
                occurrences,
                blocked,
                starts,
                "markdown-link-target",
                text[target[0]:target[1]],
                target,
            )


def iter_html_candidates(text: str) -> Iterable[tuple[int, int]]:
    cursor = 0
    while cursor < len(text):
        start = text.find("<", cursor)
        if start < 0:
            return

        if text.startswith("<!--", start):
            closing = text.find("-->", start + 4)
            if closing < 0:
                return
            end = closing + 3
            yield start, end
            cursor = end
            continue

        if text.startswith("<!", start):
            closing = text.find(">", start + 2)
            if closing < 0:
                return
            end = closing + 1
            yield start, end
            cursor = end
            continue

        name_start = start + 1
        if name_start < len(text) and text[name_start] == "/":
            name_start += 1
        if name_start >= len(text) or not text[name_start].isalpha():
            cursor = start + 1
            continue

        name_end = name_start + 1
        while name_end < len(text) and (
            text[name_end].isalnum() or text[name_end] in "_.:-"
        ):
            name_end += 1
        name = text[name_start:name_end].lower()
        if any(name.startswith(scheme) for scheme in HTML_AUTOLINK_SCHEMES):
            cursor = start + 1
            continue
        if name_end >= len(text) or text[name_end] not in " \t\r\n/>":
            cursor = start + 1
            continue

        closing = text.find(">", name_end)
        if closing < 0:
            return
        end = closing + 1
        yield start, end
        cursor = end


def has_probable_html(text: str) -> bool:
    cursor = 0
    while cursor < len(text):
        start = text.find("<", cursor)
        if start < 0:
            return False
        if text.startswith(("<!--", "<!"), start):
            return True

        name_start = start + 1
        if name_start < len(text) and text[name_start] == "/":
            name_start += 1
        if name_start >= len(text) or not text[name_start].isalpha():
            cursor = start + 1
            continue
        name_end = name_start + 1
        while name_end < len(text) and (
            text[name_end].isalnum() or text[name_end] in "_.:-"
        ):
            name_end += 1
        name = text[name_start:name_end].lower()
        if any(name.startswith(scheme) for scheme in HTML_AUTOLINK_SCHEMES):
            cursor = start + 1
            continue
        if name_end >= len(text) or text[name_end] in " \t\r\n/>":
            return True
        cursor = start + 1
    return False


def extract_html(
    text: str,
    occurrences: list[Occurrence],
    blocked: bytearray,
    starts: Sequence[int],
) -> None:
    attribute_pattern = re.compile(
        r"(?P<name>[A-Za-z_:][A-Za-z0-9_.:-]*)\s*=\s*(?P<value>\"[^\"]*\"|'[^']*'|[^\s>]+)"
    )
    for tag_start, tag_end in iter_html_candidates(text):
        tag_span = (tag_start, tag_end)
        if overlaps(tag_span, blocked):
            continue
        tag_text = text[tag_start:tag_end]
        for attribute in attribute_pattern.finditer(tag_text):
            start = tag_start + attribute.start()
            end = tag_start + attribute.end()
            add_occurrence(
                occurrences,
                blocked,
                starts,
                "html-attribute",
                attribute.group(0),
                (start, end),
                reserve=False,
            )
        add_occurrence(
            occurrences,
            blocked,
            starts,
            "html-tag",
            tag_text,
            tag_span,
        )


def extract_pattern(
    text: str,
    pattern: re.Pattern[str],
    category: str,
    occurrences: list[Occurrence],
    blocked: bytearray,
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


def extract_erb_placeholders(
    text: str,
    occurrences: list[Occurrence],
    blocked: bytearray,
    starts: Sequence[int],
) -> None:
    cursor = 0
    while cursor < len(text):
        start = text.find("<%", cursor)
        if start < 0:
            return
        closing = text.find("%>", start + 2)
        if closing < 0:
            return
        end = closing + 2
        add_occurrence(
            occurrences,
            blocked,
            starts,
            "placeholder",
            text[start:end],
            (start, end),
        )
        cursor = end


def extract_protected(text: str, format_name: str) -> list[Occurrence]:
    if text.count("\n") + 1 > MAX_TEXT_LINES:
        raise InspectionError("Input line count exceeds the safety limit.")
    occurrences: list[Occurrence] = []
    blocked = bytearray(len(text))
    starts = line_starts(text)

    if format_name == "markdown":
        extract_frontmatter(text, occurrences, blocked, starts)
        extract_fenced_code(text, occurrences, blocked, starts)
        extract_inline_code(text, occurrences, blocked, starts)
        extract_html(text, occurrences, blocked, starts)
        extract_markdown_links(text, occurrences, blocked, starts)
    elif format_name == "html":
        extract_html(text, occurrences, blocked, starts)

    placeholder_patterns = (
        re.compile(r"\{\{[^{}\n]+\}\}"),
        re.compile(r"\$\{[^{}\n]+\}"),
        re.compile(r"%\([A-Za-z_][A-Za-z0-9_]*\)[#0 +\-]?(?:\d+)?(?:\.\d+)?[A-Za-z]"),
        re.compile(r"%(?:\d+\$)?[#0 +\-]?(?:\d+)?(?:\.\d+)?[A-Za-z]"),
        re.compile(r"\{(?:\d+|[A-Za-z_][A-Za-z0-9_.-]*)(?:\s*,[^{}\n]+|:[^{}\n]+)?\}"),
    )
    extract_erb_placeholders(text, occurrences, blocked, starts)
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


def detect_input_kind(path_hint: str, format_name: str) -> str:
    suffix = Path(path_hint).suffix.lower()
    if suffix == ".mdx":
        return "mdx"
    if suffix in MARKDOWN_SUFFIXES:
        return "markdown"
    if suffix in HTML_SUFFIXES:
        return "html"
    if suffix in TEMPLATE_SUFFIXES:
        return "template"
    if suffix in SOURCE_SUFFIXES:
        return "source"
    return format_name


def has_complex_localization_syntax(text: str) -> bool:
    return any(pattern.search(text) for pattern in COMPLEX_LOCALIZATION_PATTERNS)


def coverage_metadata(
    before_text: str,
    after_text: str,
    before_path_hint: str,
    after_path_hint: str,
    format_name: str,
) -> dict[str, object]:
    before_kind = detect_input_kind(before_path_hint, format_name)
    after_kind = detect_input_kind(after_path_hint, format_name)
    input_kinds = {before_kind, after_kind}
    input_kind = before_kind if before_kind == after_kind else "mixed"
    warnings: list[str] = []
    level = "targeted"

    if len(input_kinds) > 1:
        level = "partial"
        warnings.append("Before and after input kinds differ; coverage combines both inputs.")

    for kind in sorted(input_kinds):
        if kind == "mdx":
            level = "partial"
            warnings.append("MDX JSX, ESM, and expression syntax is not parsed.")
            if format_name != "markdown":
                warnings.append("Markdown and MDX structure is not parsed in the selected format.")
        elif kind == "html":
            level = "partial"
            if format_name == "html":
                warnings.append("HTML is inspected with bounded pattern matching rather than a full parser.")
            else:
                warnings.append("HTML structure is not parsed in the selected format.")
        elif kind == "template":
            level = "partial"
            warnings.append("Template-language structure and expressions are not parsed.")
        elif kind == "source":
            level = "partial"
            warnings.append("Source-language syntax, comments, and docstrings are not parsed.")
        elif kind == "markdown" and format_name != "markdown":
            level = "partial"
            warnings.append("Markdown structure is not parsed in the selected format.")

    if format_name == "source" and input_kinds != {"source"}:
        level = "partial"
        warnings.append("The selected source format does not parse language syntax, comments, or docstrings.")
    elif format_name == "html" and not input_kinds.issubset({"html", "mdx"}):
        level = "partial"
        warnings.append("The selected HTML format uses bounded pattern matching rather than a full parser.")

    if "markdown" in input_kinds and (
        has_probable_html(before_text) or has_probable_html(after_text)
    ):
        level = "partial"
        warnings.append("Embedded HTML is inspected with bounded pattern matching rather than a full parser.")

    if has_complex_localization_syntax(before_text) or has_complex_localization_syntax(after_text):
        level = "partial"
        warnings.append(
            "Complex localization-message syntax may be present; use repository-native localization validation."
        )

    return {
        "input_kind": input_kind,
        "level": level,
        "warnings": list(dict.fromkeys(warnings)),
    }


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


def load_git_pair(base: str, repository_path: str) -> tuple[str, str, str, str]:
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

    current_candidate = root / Path(*pure_path.parts)
    try:
        if stat.S_ISLNK(current_candidate.lstat().st_mode):
            raise InspectionError("Git mode does not inspect symbolic links.")
    except InspectionError:
        raise
    except OSError as exc:
        raise InspectionError("A requested input file could not be read.") from exc

    current = current_candidate.resolve()
    try:
        current.relative_to(root)
    except ValueError as exc:
        raise InspectionError("The repository path escapes the repository root.") from exc

    object_name = f"{base}:{pure_path.as_posix()}"
    resolved_output = run_git(root, ["rev-parse", "--verify", object_name])
    try:
        resolved_oid = resolved_output.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise InspectionError("Git returned an invalid object identifier.") from exc
    if not re.fullmatch(r"[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64}", resolved_oid):
        raise InspectionError("Git returned an invalid object identifier.")

    verified_output = run_git(root, ["rev-parse", "--verify", f"{resolved_oid}^{{blob}}"])
    try:
        blob_oid = verified_output.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise InspectionError("Git returned an invalid object identifier.") from exc
    if blob_oid.lower() != resolved_oid.lower():
        raise InspectionError("Git returned an inconsistent object identifier.")

    size_output = run_git(root, ["cat-file", "-s", blob_oid])
    try:
        blob_size = int(size_output.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise InspectionError("Git returned an invalid object size.") from exc
    if blob_size > MAX_INPUT_BYTES:
        raise InspectionError("Input exceeds the 20 MiB safety limit.")

    before = decode_text(run_git(root, ["cat-file", "-p", blob_oid]))
    after = read_text_file(current)
    path_hint = pure_path.as_posix()
    return before, after, path_hint, path_hint


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


def load_inputs(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> tuple[str, str, str, str]:
    if args.before:
        if not args.after or args.path:
            parser.error("--before requires --after and cannot be combined with --path")
        return (
            read_text_file(Path(args.before)),
            read_text_file(Path(args.after)),
            args.before,
            args.after,
        )
    if not args.path or args.after:
        parser.error("--git-base requires --path and cannot be combined with --after")
    return load_git_pair(args.git_base, args.path)


def print_human(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    finding_count = summary["finding_count"]
    if finding_count == 0:
        print(f"PASS: no protected-content differences ({payload['format']}).")
    else:
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

    coverage = payload["coverage"]
    assert isinstance(coverage, dict)
    warnings = coverage["warnings"]
    assert isinstance(warnings, list)
    for warning in warnings:
        print(f"COVERAGE WARNING: {warning}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        before_text, after_text, before_path_hint, after_path_hint = load_inputs(args, parser)
        format_name = detect_format(args.format, after_path_hint)
        before_occurrences = extract_protected(before_text, format_name)
        after_occurrences = extract_protected(after_text, format_name)
        findings = compare_occurrences(before_occurrences, after_occurrences)
        coverage = coverage_metadata(
            before_text,
            after_text,
            before_path_hint,
            after_path_hint,
            format_name,
        )
        coverage["before_categories"] = category_counts(before_occurrences)
        coverage["after_categories"] = category_counts(after_occurrences)
        payload: dict[str, object] = {
            "status": "pass" if not findings else "review",
            "format": format_name,
            "summary": {
                "finding_count": len(findings),
                "before_occurrence_count": len(before_occurrences),
                "after_occurrence_count": len(after_occurrences),
            },
            "coverage": coverage,
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
