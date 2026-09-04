import json
from pathlib import Path


document = json.loads(Path("schema.json").read_text(encoding="utf-8"))
assert document == {"kind": "counter", "schemaVersion": 1}

