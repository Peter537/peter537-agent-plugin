import argparse

from reconcile import reconcile


parser = argparse.ArgumentParser()
parser.add_argument("--samples", type=int, required=True)
args = parser.parse_args()
counts = []
for _ in range(args.samples):
    values = [f"item-{index}" for index in range(200)]
    missing, comparisons = reconcile(values, values)
    assert not missing
    counts.append(comparisons)
print(f"samples={len(counts)} max_comparisons={max(counts)}")
raise SystemExit(1 if max(counts) > 1000 else 0)
