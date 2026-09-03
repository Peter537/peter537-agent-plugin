import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
from threading import Thread
from urllib.parse import parse_qs, urlencode
from urllib.request import Request
from urllib.request import urlopen


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        state_path = self.server.state_path
        value = ""
        if state_path.exists():
            value = str(json.loads(state_path.read_text(encoding="utf-8"))["value"])
        escaped = html.escape(value, quote=True)
        body = (
            "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<title>Verification fixture</title></head><body>"
            "<main><h1>Verification fixture</h1>"
            "<form method=\"post\" action=\"/save\">"
            f"<label>Value <input name=\"value\" value=\"{escaped}\"></label>"
            "<button type=\"submit\">Save</button></form>"
            f"<output id=\"saved-value\">{escaped}</output>"
            "</main></body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/save":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400)
            return
        if length < 0 or length > 4096:
            self.send_error(413)
            return
        values = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        value = values.get("value", [""])[0]
        self.server.state_path.write_text(json.dumps({"value": value}), encoding="utf-8")
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def log_message(self, _format: str, *args: object) -> None:
        return


class FixtureServer(ThreadingHTTPServer):
    def __init__(self, state_path: Path) -> None:
        super().__init__(("127.0.0.1", 0), Handler)
        self.state_path = state_path


def create_runtime() -> tuple[Path, Path]:
    runtime = Path(".verify-runtime")
    runtime.mkdir(exist_ok=False)
    return runtime, runtime / "state.json"


def self_test() -> None:
    runtime, state_path = create_runtime()
    server = None
    thread = None
    try:
        server = FixtureServer(state_path)
        thread = Thread(target=server.serve_forever)
        thread.start()
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/", timeout=2) as response:
            assert response.status == 200
            assert b'id="saved-value"></output>' in response.read()
        request = Request(
            f"http://{host}:{port}/save",
            data=urlencode({"value": "verified"}).encode("ascii"),
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            assert response.status == 200
            assert b'id="saved-value">verified</output>' in response.read()
        with urlopen(f"http://{host}:{port}/", timeout=2) as response:
            assert b'value="verified"' in response.read()
        assert json.loads(state_path.read_text(encoding="utf-8")) == {"value": "verified"}
    finally:
        if server is not None:
            if thread is not None and thread.is_alive():
                server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=2)
        shutil.rmtree(runtime)
    assert thread is not None and not thread.is_alive() and not runtime.exists()


def serve() -> None:
    runtime, state_path = create_runtime()
    server = None
    try:
        server = FixtureServer(state_path)
        host, port = server.server_address
        print(f"LISTENING http://{host}:{port}/", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if server is not None:
            server.server_close()
        shutil.rmtree(runtime)


parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--self-test", action="store_true")
mode.add_argument("--serve", action="store_true")
args = parser.parse_args()
if args.self_test:
    self_test()
else:
    serve()
