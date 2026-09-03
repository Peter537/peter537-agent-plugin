import json
from pathlib import Path


contract = json.loads(Path("service-contract.json").read_text(encoding="utf-8"))
state = json.loads(Path(contract["authState"]).read_text(encoding="utf-8"))
if not state.get("credentialAvailable"):
    raise SystemExit(2)
