"""Start the HTTP server for codebase intelligence."""

from __future__ import annotations

import typer


def serve(
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on."),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to."),
) -> None:
    """Start the HTTP server for codebase intelligence queries."""
    typer.echo(f"Starting server on {host}:{port}")
