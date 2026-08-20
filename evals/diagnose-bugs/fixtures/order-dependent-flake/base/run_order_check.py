import argparse
import subprocess
import sys


parser = argparse.ArgumentParser()
parser.add_argument("--runs", type=int, required=True)
args = parser.parse_args()
failures = 0
for _ in range(args.runs):
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_ordering.OrderingTests.test_a_first_user", "tests.test_ordering.OrderingTests.test_b_second_user_is_isolated"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    failures += result.returncode != 0
print(f"failures={failures}/{args.runs}")
raise SystemExit(1 if failures else 0)
