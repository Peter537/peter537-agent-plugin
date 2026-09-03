import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

runtime = Path(".verify-runtime")
runtime.mkdir(exist_ok=False)
try:
    state = runtime / "counter.json"
    increment = subprocess.run(
        [sys.executable, "-B", "service.py", "increment", str(state)],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=5,
    )
    read_after_restart = subprocess.run(
        [sys.executable, "-B", "service.py", "read", str(state)],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=5,
    )
    first = json.loads(increment.stdout)
    restarted = json.loads(read_after_restart.stdout)
    assert first["operation"] == "increment" and restarted["operation"] == "read"
    assert first["value"] == 1 and restarted["value"] == 1
    assert first["pid"] != os.getpid() and restarted["pid"] != os.getpid()
finally:
    shutil.rmtree(runtime)
