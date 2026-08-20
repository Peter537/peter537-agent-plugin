import json
from pathlib import Path


settings = json.loads(Path("settings.json").read_text(encoding="utf-8"))
if settings.get("target") != "web":
    print("E100: target must be 'web' for this build")
    print("E201: generated web entrypoint is unavailable")
    print("E305: packaging cannot find the generated entrypoint")
    raise SystemExit(1)
print("build complete")
