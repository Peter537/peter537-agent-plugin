import argparse
import json
import os
from pathlib import Path


class CounterService:
    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path

    def read(self) -> int:
        if not self.state_path.exists():
            return 0
        return int(json.loads(self.state_path.read_text(encoding="utf-8"))["value"])

    def increment(self) -> int:
        value = self.read() + 1
        self.state_path.write_text(json.dumps({"value": value}), encoding="utf-8")
        return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("increment", "read"))
    parser.add_argument("state", type=Path)
    args = parser.parse_args()
    service = CounterService(args.state)
    value = service.increment() if args.operation == "increment" else service.read()
    print(json.dumps({"operation": args.operation, "pid": os.getpid(), "value": value}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
