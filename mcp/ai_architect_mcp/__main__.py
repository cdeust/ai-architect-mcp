"""CLI entrypoint for the AI Architect MCP server.

Provides commands: serve, version, health, config-validate.
Uses Click for argument parsing.

Usage:
    python -m ai_architect_mcp serve
    python -m ai_architect_mcp version
    python -m ai_architect_mcp health
    python -m ai_architect_mcp config-validate
    python -m ai_architect_mcp config-validate --config path/to/config.toml
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from ai_architect_mcp._config.loader import load_config
from ai_architect_mcp._config.models import ServerConfig

VERSION = "0.1.0"
PACKAGE_NAME = "ai-architect-mcp"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

logger = logging.getLogger("ai_architect_mcp")


@click.group()
def cli() -> None:
    """AI Architect MCP server — autonomous software engineering pipeline."""


@cli.command()
def version() -> None:
    """Print the package version."""
    click.echo(f"{PACKAGE_NAME} {VERSION}")


@cli.command()
@click.option(
    "--host",
    default=None,
    help="Override server host",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="Override server port",
)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration TOML file",
)
def serve(
    host: str | None,
    port: int | None,
    config_path: Path | None,
) -> None:
    """Start the MCP server."""
    config = load_config(config_path)

    if host is not None:
        config.server.host = host
    if port is not None:
        config.server.port = port

    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, config.server.log_level.upper()),
    )

    logger.info(
        "Starting server on %s:%d",
        config.server.host,
        config.server.port,
    )

    from ai_architect_mcp._app import mcp
    # Import tool modules to trigger registration
    from ai_architect_mcp._tools import verification_tools  # noqa: F401
    from ai_architect_mcp._tools import hor_tools  # noqa: F401
    from ai_architect_mcp._tools import prompting_tools  # noqa: F401
    from ai_architect_mcp._tools import context_tools  # noqa: F401
    from ai_architect_mcp._tools import scoring_tools  # noqa: F401
    from ai_architect_mcp._tools import adapter_tools  # noqa: F401
    from ai_architect_mcp._tools import interview_tools  # noqa: F401
    from ai_architect_mcp._tools import memory_tools  # noqa: F401
    from ai_architect_mcp._tools import xcode_tools  # noqa: F401
    mcp.run()


@cli.command()
def health() -> None:
    """Check server health by validating imports and config."""
    errors: list[str] = []

    try:
        load_config()
    except Exception as exc:
        errors.append(f"Config load failed: {exc}")

    try:
        from ai_architect_mcp._app import mcp  # noqa: F401
    except Exception as exc:
        errors.append(f"Server import failed: {exc}")

    if errors:
        click.echo("UNHEALTHY", err=True)
        for error in errors:
            click.echo(f"  - {error}", err=True)
        sys.exit(1)

    click.echo("HEALTHY")


@cli.command("config-validate")
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration TOML file to validate",
)
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="Output config as JSON",
)
def config_validate(
    config_path: Path | None,
    json_output: bool,
) -> None:
    """Validate configuration and display resolved values."""
    try:
        config = load_config(config_path)
    except Exception as exc:
        click.echo(f"INVALID: {exc}", err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(
            config.model_dump(),
            indent=2,
            default=str,
        ))
    else:
        click.echo("Configuration valid.")
        click.echo(f"  Server: {config.server.host}:{config.server.port}")
        click.echo(f"  Log level: {config.server.log_level}")
        click.echo(
            f"  Consensus: {config.verification.consensus_algorithm}"
        )
        click.echo(f"  Strategy: {config.prompting.default_strategy}")
        click.echo(
            f"  Artifacts: {config.context.artifact_persist_dir}"
        )


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
