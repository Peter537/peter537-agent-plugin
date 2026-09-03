import json
from pathlib import Path


artifact = json.loads(Path("build-info.json").read_text(encoding="utf-8"))
requested = Path("requested-revision.txt").read_text(encoding="utf-8").strip()
if artifact.get("revision") != requested:
    raise SystemExit(2)
