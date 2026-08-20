import json
from pathlib import Path


evidence = json.loads(Path("resolution-evidence.json").read_text(encoding="utf-8"))
print(f"resolved graph differs from lock evidence: {evidence['drift']}" )
raise SystemExit(1 if evidence["drift"] else 0)
