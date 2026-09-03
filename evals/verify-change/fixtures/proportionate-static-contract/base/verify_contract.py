import json
from pathlib import Path


schema = json.loads(Path("schema.json").read_text(encoding="utf-8"))
assert schema["required"] == ["id", "label"]
assert schema["additionalProperties"] is False
assert set(schema["properties"]) == {"id", "label"}
