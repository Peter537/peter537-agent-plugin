"""Loopback-only review API for the verification-context fixture."""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class ReviewHandler(BaseHTTPRequestHandler):
    runtime: Path
    token: str

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, status: int, document: object) -> None:
        payload = json.dumps(document, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def authorized(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {self.token}"

    def do_GET(self) -> None:
        if self.path == "/ready":
            self.send_json(200, {"ready": True})
            return
        if self.path != "/api/reviews/synthetic-review" or not self.authorized():
            self.send_json(404 if self.authorized() else 401, {"error": "unavailable"})
            return
        stored = self.runtime / "review.json"
        if not stored.is_file():
            self.send_json(404, {"error": "missing"})
            return
        self.send_json(200, json.loads(stored.read_text(encoding="utf-8")))

    def do_POST(self) -> None:
        if self.path != "/api/reviews" or not self.authorized():
            self.send_json(404 if self.authorized() else 401, {"error": "unavailable"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            document = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid"})
            return
        if document != {"id": "synthetic-review", "decision": "hold"}:
            self.send_json(400, {"error": "invalid"})
            return
        self.runtime.mkdir(parents=True, exist_ok=True)
        (self.runtime / "review.json").write_text(
            json.dumps(document, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.send_json(201, document)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--port-file", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("REVIEW_CONSOLE_TEST_TOKEN")
    if not token:
        return 2
    ReviewHandler.runtime = args.runtime
    ReviewHandler.token = token
    server = ThreadingHTTPServer(("127.0.0.1", 0), ReviewHandler)
    args.port_file.write_text(str(server.server_port), encoding="ascii")
    try:
        server.serve_forever(poll_interval=0.05)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
