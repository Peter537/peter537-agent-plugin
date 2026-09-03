from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, required=True)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be greater than zero")
    return args


def main() -> int:
    args = parse_args()
    failures = 0
    test_name = (
        "tests.test_export_job.ExportJobTests."
        "test_cancellation_propagates_and_cleans_owned_state"
    )
    for _ in range(args.runs):
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", test_name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        failures += result.returncode != 0
    print(f"failures={failures}/{args.runs}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
