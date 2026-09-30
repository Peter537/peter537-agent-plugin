"""File-backed Counter CLI adapted from the verification-context fixture."""

import argparse
import json
from pathlib import Path


def write_value(path, value):
    if value < 0:
        raise ValueError("the counter must be non-negative")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"value": value}) + "\n", encoding="utf-8")


def read_value(path):
    value = json.loads(path.read_text(encoding="utf-8")).get("value")
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("the counter state is invalid")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("set").add_argument("value", type=int)
    commands.add_parser("show")
    args = parser.parse_args()
    if args.command == "set":
        write_value(args.state, args.value)
        return 0
    print(read_value(args.state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
