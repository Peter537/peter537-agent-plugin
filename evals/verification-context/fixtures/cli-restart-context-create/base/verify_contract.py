"""Verify the maintained Counter CLI contract without retaining test state."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
STATE = RUNTIME / "verification" / "counter.json"


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "counter.py", "--state", str(STATE), *arguments],
        cwd=ROOT,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )


def main() -> int:
    if RUNTIME.exists():
        raise SystemExit("refusing to use a pre-existing .runtime tree")
    created_runtime = False
    try:
        RUNTIME.mkdir()
        created_runtime = True
        written = run("set", "37")
        if written.returncode != 0 or written.stdout or written.stderr:
            return 1
        observed = run("show")
        if observed.returncode != 0 or observed.stdout.strip() != "37" or observed.stderr:
            return 1
        return 0
    finally:
        if created_runtime and RUNTIME.exists():
            shutil.rmtree(RUNTIME)


if __name__ == "__main__":
    raise SystemExit(main())
