import argparse

from order_sensitive import process


parser = argparse.ArgumentParser()
parser.add_argument("--runs", type=int, required=True)
args = parser.parse_args()
failures = sum(process(["old", "reset", "new"]) != ["new"] for _ in range(args.runs))
if failures:
    raise SystemExit(1)
