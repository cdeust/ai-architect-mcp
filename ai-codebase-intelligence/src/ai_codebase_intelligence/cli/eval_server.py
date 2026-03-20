"""Eval server — 1:1 port of gitnexus cli/eval-server.js.

Lightweight HTTP server for SWE-bench evaluation. Exposes tool
calls via POST /tool/:name with JSON body.
"""
from __future__ import annotations

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from ..mcp.local.local_backend import LocalBackend

_backend: LocalBackend | None = None
_last_activity: float = 0.0
_idle_timeout: float = 0.0


class EvalHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            import asyncio
            repos = asyncio.run(_backend.list_repos()) if _backend else []
            self._json({"status": "ok", "repos": [r["name"] for r in repos]})
        else:
            self._json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        global _last_activity
        _last_activity = time.time()

        if self.path == "/shutdown":
            self._json({"status": "shutting_down"})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return

        if self.path.startswith("/tool/"):
            tool_name = self.path[6:]
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            try:
                params = json.loads(body)
            except json.JSONDecodeError:
                params = {}

            import asyncio
            try:
                result = asyncio.run(_backend.call_tool(tool_name, params))
                text = result if isinstance(result, str) else json.dumps(result, indent=2)
                self._text(text)
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "Not found"}, 404)

    def _json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, text: str, status: int = 200) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass


def eval_server_command(port: int = 4848, idle_timeout: int = 0) -> None:
    global _backend, _last_activity, _idle_timeout
    import asyncio

    _backend = LocalBackend()
    asyncio.run(_backend.init())
    _last_activity = time.time()
    _idle_timeout = float(idle_timeout)

    server = HTTPServer(("127.0.0.1", port), EvalHandler)
    print(f"Eval server listening on 127.0.0.1:{port}")

    if _idle_timeout > 0:
        def check_idle() -> None:
            while True:
                time.sleep(60)
                if time.time() - _last_activity > _idle_timeout:
                    print("Idle timeout reached, shutting down")
                    server.shutdown()
                    break
        t = threading.Thread(target=check_idle, daemon=True)
        t.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEval server stopped")
        server.server_close()
