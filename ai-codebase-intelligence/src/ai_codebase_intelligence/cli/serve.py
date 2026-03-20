from __future__ import annotations


def serve_command(port: int = 4747, host: str = "127.0.0.1") -> None:
    from ..server.api import create_server
    create_server(port, host)
