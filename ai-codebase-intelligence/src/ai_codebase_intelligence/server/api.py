"""HTTP API server — 1:1 port of gitnexus server/api.js (minimal)."""
from __future__ import annotations

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from ..mcp.local.local_backend import LocalBackend
from ..storage.repo_manager import list_registered_repos

_backend: LocalBackend | None = None


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/repos":
            entries = list_registered_repos(validate=True)
            self._json_response(entries)
        elif self.path.startswith("/repos/") and self.path.endswith("/context"):
            name = self.path.split("/")[2]
            import asyncio
            try:
                result = asyncio.run(_backend.call_tool("list_repos", {}))
                self._json_response(result)
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path == "/health":
            self._json_response({"status": "ok"})
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            params = json.loads(body)
        except json.JSONDecodeError:
            params = {}

        if self.path.startswith("/repos/") and self.path.endswith("/query"):
            import asyncio
            name = self.path.split("/")[2]
            try:
                result = asyncio.run(_backend.call_tool("query", {**params, "repo": name}))
                self._json_response(result)
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path.startswith("/repos/") and self.path.endswith("/analyze"):
            self._json_response({"status": "accepted"}, 202)
        else:
            self._json_response({"error": "Not found"}, 404)

    def _json_response(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress default logging


def create_server(port: int = 4747, host: str = "127.0.0.1") -> None:
    global _backend
    import asyncio

    _backend = LocalBackend()
    asyncio.run(_backend.init())

    server = HTTPServer((host, port), APIHandler)
    repos = list_registered_repos()
    print(f"  HTTP server listening on {host}:{port}")
    print(f"  Serving {len(repos)} indexed repos")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped")
        server.server_close()
