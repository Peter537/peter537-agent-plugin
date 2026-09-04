"""Transform the fixture's version-one records into version two."""

from __future__ import annotations

import json
from pathlib import Path


def migrate(source: Path, destination: Path) -> None:
    document = json.loads(source.read_text(encoding="utf-8"))
    if document.get("format") != 1 or not isinstance(document.get("records"), list):
        raise ValueError("unsupported source format")
    records = []
    for record in document["records"]:
        if set(record) != {"id", "enabled"}:
            raise ValueError("unsupported record shape")
        identifier = record["id"]
        enabled = record["enabled"]
        if not isinstance(identifier, str) or not identifier or not isinstance(enabled, bool):
            raise ValueError("invalid record")
        records.append({"record_id": identifier, "state": "active" if enabled else "paused"})
    destination.write_text(
        json.dumps({"format": 2, "records": records}, indent=2) + "\n",
        encoding="utf-8",
    )
