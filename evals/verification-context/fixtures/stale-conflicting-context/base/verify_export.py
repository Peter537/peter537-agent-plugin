"""Validate the current local export contract in disposable storage."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from exporter import export


ROOT = Path(__file__).resolve().parent


def main() -> int:
    revision = (ROOT / "EXPORT_CONTRACT_REVISION").read_text(encoding="utf-8").strip()
    if revision != "export-contract-v2":
        return 1
    runtime = ROOT / ".runtime"
    if runtime.exists():
        return 2
    try:
        runtime.mkdir()
        target = runtime / "export.json"
        export(target)
        document = json.loads(target.read_text(encoding="utf-8"))
        if document != {
            "contract": revision,
            "records": [{"id": "synthetic-record"}],
        }:
            return 1
        return 0
    finally:
        if runtime.exists():
            shutil.rmtree(runtime)


if __name__ == "__main__":
    raise SystemExit(main())
