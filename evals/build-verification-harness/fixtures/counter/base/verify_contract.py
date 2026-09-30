"""Existing complete Counter contract check using owned disposable state."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import Mock

from counter import read_value

ROOT = Path(__file__).resolve().parent


def run(state, *arguments):
    return subprocess.run([sys.executable, "-B", str(ROOT / "counter.py"),
                           "--state", str(state), *arguments], cwd=ROOT,
                          stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=10)


def main():
    # A controlled file seam supplies malformed state; persistence uses real files below.
    for value in (-1, True, "37"):
        file_seam = Mock()
        file_seam.read_text.return_value = json.dumps({"value": value})
        try:
            read_value(file_seam)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid stored value accepted")
    with tempfile.TemporaryDirectory(prefix="counter proof ") as folder:
        state = Path(folder) / "counter.json"
        for value in (0, 37, 82):
            written = run(state, "set", str(value))
            assert written.returncode == 0, "write command failed"
            observed = run(state, "show")
            assert observed.returncode == 0, "persisted state unavailable"
            assert observed.stdout.strip() == str(value), "persisted value mismatch"
            assert json.loads(state.read_text(encoding="utf-8")) == {"value": value}
        before = state.read_bytes()
        assert run(state, "set", "-1").returncode != 0
        assert state.read_bytes() == before, "rejection changed persisted state"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
