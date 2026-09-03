import json
from pathlib import Path


evidence = json.loads(Path("ci-evidence.json").read_text(encoding="utf-8"))
assert evidence["jobs"] == {"unit": "passed", "lint": "passed"}
