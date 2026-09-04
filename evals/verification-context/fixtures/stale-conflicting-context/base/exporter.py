"""Create a deterministic local export document."""

from __future__ import annotations

import json
from pathlib import Path


def export(destination: Path) -> None:
    destination.write_text(
        json.dumps(
            {"contract": "export-contract-v2", "records": [{"id": "synthetic-record"}]},
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
