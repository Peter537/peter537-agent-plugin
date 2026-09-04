"""A small file-backed counter used by the verification-context fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def write_value(path: Path, value: int) -> None:
    if value < 0:
        raise ValueError("the counter must be non-negative")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"value": value}) + "\n", encoding="utf-8")


def read_value(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    value = data.get("value")
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("the counter state is invalid")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    subcommands = parser.add_subparsers(dest="command", required=True)
    set_command = subcommands.add_parser("set")
    set_command.add_argument("value", type=int)
    subcommands.add_parser("show")
    args = parser.parse_args()

    if args.command == "set":
        write_value(args.state, args.value)
        return 0
    print(read_value(args.state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
