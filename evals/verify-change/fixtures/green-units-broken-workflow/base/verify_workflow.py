from pathlib import Path
import shutil

from publisher import publish, reload


runtime = Path(".verify-runtime")
runtime.mkdir(exist_ok=False)
try:
    record = runtime / "record.json"
    publish(record, "Quarterly plan")
    assert reload(record) == {"title": "Quarterly plan", "status": "published"}
finally:
    shutil.rmtree(runtime)
