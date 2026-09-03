import json
from pathlib import Path


project = json.loads(Path("project.json").read_text(encoding="utf-8"))
if not project.get("entrypoint") or not project.get("existingHarness"):
    raise SystemExit(2)
