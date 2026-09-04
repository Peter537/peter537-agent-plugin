import json
from pathlib import Path


record = json.loads(
    Path("fixtures/synthetic-review.json").read_text(encoding="utf-8")
)
assert record == {
    "id": "synthetic-review-42",
    "state": "pending",
    "owner": "fixture",
}

