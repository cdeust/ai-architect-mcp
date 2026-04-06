"""Augment source files with AI context annotations."""

from __future__ import annotations

import typer


def augment(
    pattern: str = typer.Argument(..., help="Glob pattern for files to augment."),
    repo_path: str = typer.Option(".", "--repo", help="Path to the repository."),
) -> None:
    """Augment source files with codebase intelligence annotations."""
    typer.echo(f"Augmenting files matching '{pattern}' in {repo_path}")
