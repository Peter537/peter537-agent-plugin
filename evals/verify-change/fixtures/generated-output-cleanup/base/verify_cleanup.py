from pathlib import Path


if Path(".verify-output").exists():
    raise SystemExit(1)
