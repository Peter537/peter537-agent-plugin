"""Verify the loopback API contract and restore the starting filesystem state."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
PORT_FILE = RUNTIME / "port.txt"
TOKEN = "synthetic-local-verification-token"


def request(url: str, *, method: str = "GET", document: object | None = None) -> object:
    data = None if document is None else json.dumps(document).encode("utf-8")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=headers, method=method),
        timeout=2,
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    if RUNTIME.exists():
        return 2
    RUNTIME.mkdir()
    environment = os.environ.copy()
    environment["REVIEW_CONSOLE_TEST_TOKEN"] = TOKEN
    process = subprocess.Popen(
        [
            sys.executable,
            "-B",
            "server.py",
            "--runtime",
            str(RUNTIME),
            "--port-file",
            str(PORT_FILE),
        ],
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 5
        while not PORT_FILE.is_file() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        if not PORT_FILE.is_file():
            return 1
        port = int(PORT_FILE.read_text(encoding="ascii"))
        origin = f"http://127.0.0.1:{port}"
        if request(origin + "/ready") != {"ready": True}:
            return 1
        review = {"id": "synthetic-review", "decision": "hold"}
        if request(origin + "/api/reviews", method="POST", document=review) != review:
            return 1
        if request(origin + "/api/reviews/synthetic-review") != review:
            return 1
        return 0
    except (OSError, ValueError, json.JSONDecodeError):
        return 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        if RUNTIME.exists():
            shutil.rmtree(RUNTIME)


if __name__ == "__main__":
    raise SystemExit(main())
