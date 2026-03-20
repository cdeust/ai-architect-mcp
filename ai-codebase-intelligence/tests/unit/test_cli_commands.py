"""Tests for CLI command existence and argument parsing."""

from __future__ import annotations

import importlib

import pytest
from typer.testing import CliRunner

from ai_codebase_intelligence._cli import app


runner = CliRunner()


def test_app_has_wiki_command() -> None:
    """The 'wiki' command is registered on the CLI app."""
    command_names = [cmd.name for cmd in app.registered_commands]
    assert "wiki" in command_names


def test_app_has_serve_command() -> None:
    """The 'serve' command is registered on the CLI app."""
    command_names = [cmd.name for cmd in app.registered_commands]
    assert "serve" in command_names


def test_app_has_augment_command() -> None:
    """The 'augment' command is registered on the CLI app."""
    command_names = [cmd.name for cmd in app.registered_commands]
    assert "augment" in command_names


def test_app_has_analyze_command() -> None:
    """The 'analyze' command is registered on the CLI app."""
    command_names = [
        cmd.name or (cmd.callback.__name__ if cmd.callback else None)
        for cmd in app.registered_commands
    ]
    assert "analyze" in command_names


def test_wiki_cmd_module_imports() -> None:
    """wiki_cmd module is importable without errors."""
    mod = importlib.import_module("ai_codebase_intelligence._cli.wiki_cmd")
    assert hasattr(mod, "wiki")
    assert callable(mod.wiki)


def test_serve_cmd_module_imports() -> None:
    """serve_cmd module is importable without errors."""
    mod = importlib.import_module("ai_codebase_intelligence._cli.serve_cmd")
    assert hasattr(mod, "serve")
    assert callable(mod.serve)


def test_augment_cmd_module_imports() -> None:
    """augment_cmd module is importable without errors."""
    mod = importlib.import_module(
        "ai_codebase_intelligence._cli.augment_cmd"
    )
    assert hasattr(mod, "augment")
    assert callable(mod.augment)


def test_wiki_help_text() -> None:
    """The 'wiki' command shows help text without error."""
    result = runner.invoke(app, ["wiki", "--help"])
    assert result.exit_code == 0
    assert "Generate wiki" in result.output


def test_serve_help_text() -> None:
    """The 'serve' command shows help text without error."""
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0
    assert "HTTP server" in result.output


def test_augment_help_text() -> None:
    """The 'augment' command shows help text without error."""
    result = runner.invoke(app, ["augment", "--help"])
    assert result.exit_code == 0
    assert "augment" in result.output.lower()


def test_no_args_shows_help() -> None:
    """Running with no arguments shows help text."""
    result = runner.invoke(app, [])
    assert result.exit_code in (0, 2)  # typer may use 0 or 2 for help
    assert "usage" in result.output.lower() or "commands" in result.output.lower()


def test_wiki_requires_no_mandatory_args() -> None:
    """Wiki command can be invoked with defaults (may fail at runtime but not parsing)."""
    result = runner.invoke(app, ["wiki", "--help"])
    assert "--output" in result.output
    assert "--name" in result.output


def test_augment_requires_pattern() -> None:
    """Augment command requires a pattern argument."""
    result = runner.invoke(app, ["augment"])
    assert result.exit_code != 0


def test_serve_default_options() -> None:
    """Serve command has --port and --host options."""
    result = runner.invoke(app, ["serve", "--help"])
    assert "--port" in result.output
    assert "--host" in result.output
