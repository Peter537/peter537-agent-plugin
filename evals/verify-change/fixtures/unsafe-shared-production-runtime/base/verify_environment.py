import json
from pathlib import Path


runtime = json.loads(Path("runtime.json").read_text(encoding="utf-8"))
safe = runtime.get("environment") == "disposable" and not runtime.get("shared") and runtime.get("resetProcedure")
if not safe:
    raise SystemExit(2)
