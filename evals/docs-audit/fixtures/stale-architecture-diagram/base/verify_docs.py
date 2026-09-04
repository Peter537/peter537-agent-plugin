"""Check local Markdown links and the architecture document's stable contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "docs-checks.json"
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
MERMAID_PATTERN = re.compile(
    r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL
)
FENCE_PATTERN = re.compile(r"^```[^\n]*\n.*?^```[ \t]*$", re.MULTILINE | re.DOTALL)


def local_link_errors(markdown_path: Path) -> list[str]:
    text = markdown_path.read_text(encoding="utf-8")
    errors: list[str] = []
    for match in LINK_PATTERN.finditer(text):
        destination = match.group(1).strip().split("#", 1)[0]
        if not destination or "://" in destination or destination.startswith("mailto:"):
            continue
        target = (markdown_path.parent / destination).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append("link escapes the repository fixture")
            continue
        if not target.is_file():
            errors.append("local Markdown link target is missing")
    return errors


def find_ordered_step(lines: list[str], terms: list[str], start: int) -> int | None:
    for index in range(start, len(lines)):
        line = lines[index].casefold()
        if all(term.casefold() in line for term in terms):
            return index
    return None


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    document = ROOT / config["document"]
    linked_from = ROOT / config["linkedFrom"]
    errors = local_link_errors(linked_from)
    if not document.is_file():
        errors.append("architecture document is missing")
    else:
        errors.extend(local_link_errors(document))
        text = document.read_text(encoding="utf-8")
        if config["requiredHeading"] not in text:
            errors.append("required architecture heading is missing")

        diagrams = MERMAID_PATTERN.findall(text)
        if len(diagrams) != 1:
            errors.append("architecture document must contain one Mermaid diagram")
        else:
            diagram = diagrams[0]
            lines = [line.strip() for line in diagram.splitlines() if line.strip()]
            if not lines or lines[0] != config["requiredDiagramType"]:
                errors.append("Mermaid diagram type does not match the documentation contract")
            if re.search(r"(?m)^\s*accTitle\s*:", diagram) is None:
                errors.append("Mermaid accessibility title is missing")
            if re.search(r"(?m)^\s*accDescr(?:\s*\{.*?\}|\s*:)", diagram, re.DOTALL) is None:
                errors.append("Mermaid accessibility description is missing")
            folded_diagram = diagram.casefold()
            for term in config["requiredDiagramTerms"]:
                if term.casefold() not in folded_diagram:
                    errors.append("required workflow component is missing from the diagram")

            arrow_lines = [
                line for line in lines if "->" in line or "-->>" in line or "->>" in line
            ]
            cursor = 0
            for terms in config["orderedDiagramSteps"]:
                found = find_ordered_step(arrow_lines, terms, cursor)
                if found is None:
                    errors.append("required workflow relationship or order is missing")
                else:
                    cursor = found + 1

        prose = FENCE_PATTERN.sub("", text)
        paragraphs = [
            " ".join(part.split()).casefold()
            for part in re.split(r"\n\s*\n", prose)
            if part.strip()
        ]
        for group in config["proseConceptGroups"]:
            if not any(all(term.casefold() in paragraph for term in group) for paragraph in paragraphs):
                errors.append("nearby prose does not convey a required workflow relationship")

    if errors:
        for error in sorted(set(errors)):
            print(f"FAIL: {error}")
        print(f"FAIL: documentation checks found {len(errors)} issue(s)")
        return 1
    print("PASS: local links and architecture documentation contracts")
    if config.get("mermaidRenderer") is None:
        print("NOT_RUN: Mermaid syntax and rendered legibility require an unavailable renderer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
