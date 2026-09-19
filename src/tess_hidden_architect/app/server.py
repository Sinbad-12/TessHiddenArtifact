"""Local HTTP server and API handler for the TESS Hidden Architect demo."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any

from tess_hidden_architect.app.demo import DemoSession


class DemoRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for demo UI and JSON API."""

    session: DemoSession = DemoSession()

    def do_GET(self) -> None:
        """Handle GET requests for static files and state."""
        if self.path in ("/", "/index.html"):
            self._serve_index()
        elif self.path == "/api/state":
            self._send_json(self.session.get_state())
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")

    def do_POST(self) -> None:
        """Handle action POST requests."""
        if self.path == "/api/infer":
            state = self.session.run_inference()
            self._send_json(state)
        elif self.path == "/api/reveal":
            try:
                state = self.session.reveal_withheld()
                self._send_json(state)
            except RuntimeError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        elif self.path == "/api/reset":
            state = self.session.reset()
            self._send_json(state)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def _serve_index(self) -> None:
        """Serve the HTML application frontend."""
        html_path = Path(__file__).parent / "static" / "index.html"
        if not html_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Frontend HTML missing")
            return
        content = html_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        """Send a JSON API response."""
        encoded = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy default access logs."""
        pass


def create_demo_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    session: DemoSession | None = None,
) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer instance for the demo."""
    if session is not None:
        DemoRequestHandler.session = session
    else:
        DemoRequestHandler.session = DemoSession()
    server = ThreadingHTTPServer((host, port), DemoRequestHandler)
    return server
