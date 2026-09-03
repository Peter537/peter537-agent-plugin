import argparse

from migration import migrate


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", choices=("empty", "populated"), required=True)
args = parser.parse_args()
source = [] if args.dataset == "empty" else [{"id": 7, "name": "fixture-user", "preference": "compact"}]
result = migrate(source)
if args.dataset == "populated":
    expected = [{"id": 7, "name": "fixture-user", "preference": "compact", "enabled": True}]
    if result != expected:
        raise SystemExit(1)
