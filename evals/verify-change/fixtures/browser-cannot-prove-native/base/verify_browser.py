import json
from pathlib import Path


evidence = json.loads(Path("evidence.json").read_text(encoding="utf-8"))
assert all(value == "passed" for value in evidence["browser"].values())
