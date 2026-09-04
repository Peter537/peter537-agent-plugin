"""Check the fixture's small repository contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.parse_args()
    path = Path(__file__).resolve().with_name("contract.json")
    contract = json.loads(path.read_text(encoding="utf-8"))
    return 0 if contract == {"format": 1, "required_state": "ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
