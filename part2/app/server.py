"""Standard-library HTTP API for the lab queue."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .queue import join, take


def serve(host: str, port: int, data_dir: str) -> None:
    path = Path(data_dir) / "queue.txt"

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def reply(self, status, text):
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self.reply(200, "ok")
            else:
                self.reply(404, "not found")

        def do_POST(self):
            try:
                if self.path == "/join":
                    try:
                        if self.headers.get("Transfer-Encoding"):
                            raise ValueError("Unsupported body framing")
                        length = int(self.headers.get("Content-Length", "0"))
                        if not 0 < length <= 65536:
                            raise ValueError("Invalid body length")
                        body = self.rfile.read(length)
                        if len(body) != length:
                            raise ValueError("Incomplete body")
                        payload = json.loads(body)
                        if not isinstance(payload, dict):
                            raise ValueError("Expected an object")
                        ticket = join(path, payload.get("name"))
                    except (ValueError, UnicodeError):
                        self.reply(400, "invalid name or JSON")
                        return
                    self.reply(200, str(ticket))
                elif self.path == "/next":
                    try:
                        name = take(path)
                    except LookupError:
                        self.reply(404, "empty")
                        return
                    self.reply(200, name)
                else:
                    self.reply(404, "not found")
            except OSError:
                self.reply(500, "queue unavailable")

    with HTTPServer((host, port), Handler) as server:
        server.serve_forever()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR", "/data")
    serve("0.0.0.0", port, data_dir)


if __name__ == "__main__":
    main()
# Section 5.2: comment-only change to demonstrate a Compose rebuild.
