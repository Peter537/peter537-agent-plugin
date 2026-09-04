import json
from pathlib import Path


record = json.loads(Path("fixture.json").read_text(encoding="utf-8"))
assert record == {"id": "synthetic-1", "state": "ready"}

