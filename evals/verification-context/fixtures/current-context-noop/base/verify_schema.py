"""Validate the fixture's bounded static schema contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    schema = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
    sample = json.loads((ROOT / "sample.json").read_text(encoding="utf-8"))
    if schema != {
        "required": ["format", "id"],
        "format": 3,
        "idType": "non-empty-string",
    }:
        return 1
    if set(sample) != set(schema["required"]):
        return 1
    if sample["format"] != schema["format"]:
        return 1
    if not isinstance(sample["id"], str) or not sample["id"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
