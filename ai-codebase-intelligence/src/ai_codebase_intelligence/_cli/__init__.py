"""CLI entry point for ai-codebase-intelligence.

Registers all subcommands on a single Typer app instance.
"""

from __future__ import annotations

import typer

from .augment_cmd import augment
from .serve_cmd import serve
from .wiki_cmd import wiki

app = typer.Typer(
    name="ai-codebase-intelligence",
    help="AI-powered codebase intelligence CLI.",
    add_completion=False,
)

app.command(name="wiki")(wiki)
app.command(name="serve")(serve)
app.command(name="augment")(augment)


@app.command(name="analyze")
def analyze(
    repo_path: str = typer.Argument(".", help="Path to the repository"),
) -> None:
    """Analyze a codebase and build the knowledge graph."""
    typer.echo(f"Analyzing {repo_path}...")
