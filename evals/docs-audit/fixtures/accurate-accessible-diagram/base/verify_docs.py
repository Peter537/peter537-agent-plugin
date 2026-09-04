"""Verify local links and stable architecture-document contracts."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "architecture.md"
README = ROOT / "README.md"
MERMAID_PATTERN = re.compile(
    r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL
)


def main() -> int:
    errors: list[str] = []
    readme = README.read_text(encoding="utf-8")
    document = DOCUMENT.read_text(encoding="utf-8")

    if "(docs/architecture.md)" not in readme:
        errors.append("README architecture link is missing")

    diagrams = MERMAID_PATTERN.findall(document)
    if len(diagrams) != 1:
        errors.append("architecture document must contain one Mermaid diagram")
    else:
        diagram = diagrams[0]
        if not diagram.lstrip().startswith("sequenceDiagram"):
            errors.append("architecture diagram must be a sequence diagram")
        if re.search(r"(?m)^\s*accTitle\s*:\s*\S", diagram) is None:
            errors.append("Mermaid accessibility title is missing")
        if re.search(r"(?m)^\s*accDescr\s*:\s*\S", diagram) is None:
            errors.append("Mermaid accessibility description is missing")
        folded = diagram.casefold()
        for term in (
            "submission api",
            "durable queue",
            "durable store",
            "outbox",
            "validate event",
            "persist event",
            "append notification",
            "attempt delivery",
            "delivery fails",
            "pending outbox entry remain",
        ):
            if term not in folded:
                errors.append("required workflow relationship is missing")

    prose = MERMAID_PATTERN.sub("", document).casefold()
    for terms in (
        ("accepted", "validation", "durable queue"),
        ("persists", "outbox", "queue entry"),
        ("delivery fails", "stored event", "pending outbox entry", "does not roll back"),
        ("rendered layout", "compatible mermaid renderer"),
    ):
        if not all(term in prose for term in terms):
            errors.append("nearby text does not convey a required relationship or limit")

    if errors:
        for error in sorted(set(errors)):
            print(f"FAIL: {error}")
        return 1
    print("PASS: local link and architecture documentation contracts")
    print("NOT_RUN: Mermaid syntax, rendered legibility, and accessibility-tree behavior")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
