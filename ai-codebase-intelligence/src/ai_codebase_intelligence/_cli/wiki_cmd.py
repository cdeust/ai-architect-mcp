"""Generate wiki documentation from the knowledge graph."""

from __future__ import annotations

from pathlib import Path

import typer


def wiki(
    output: Path = typer.Option(
        Path("wiki"),
        "--output",
        "-o",
        help="Output directory for generated wiki.",
    ),
    name: str = typer.Option(
        "",
        "--name",
        "-n",
        help="Repository name for the wiki title.",
    ),
    repo_path: str = typer.Option(
        ".",
        "--repo",
        help="Path to the repository.",
    ),
) -> None:
    """Generate wiki documentation from the indexed knowledge graph."""
    typer.echo(f"Generating wiki for {name or repo_path} -> {output}")
