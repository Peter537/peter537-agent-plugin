import json
from pathlib import Path


config = json.loads(Path("app_config.json").read_text(encoding="utf-8"))
contract = json.loads(Path("integration_contract.json").read_text(encoding="utf-8"))
key = contract["required_key"]
if config.get(key) != contract["endpoint"]:
    print(f"configuration does not satisfy required key: {key}")
    raise SystemExit(1)
print("integration contract satisfied")
