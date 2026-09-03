import argparse

from reconcile import reconcile


parser = argparse.ArgumentParser()
parser.add_argument("--samples", type=int, required=True)
args = parser.parse_args()
records = list(range(40))
measurements = [reconcile(records) for _ in range(args.samples)]
if any(output != records or comparisons > 100 for output, comparisons in measurements):
    raise SystemExit(1)
