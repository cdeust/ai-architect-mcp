"""Tests for the CLI entrypoint."""

from __future__ import annotations

from click.testing import CliRunner

from ai_architect_mcp.__main__ import VERSION, cli


class TestCLI:
    """Tests for the Click CLI commands."""

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert VERSION in result.output

    def test_health(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["health"])
        assert result.exit_code == 0
        assert "HEALTHY" in result.output

    def test_config_validate_defaults(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["config-validate"])
        assert result.exit_code == 0
        assert "Configuration valid" in result.output
        assert "8080" in result.output

    def test_config_validate_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["config-validate", "--json-output"])
        assert result.exit_code == 0
        assert '"port": 8080' in result.output

    def test_config_validate_with_env(
        self,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        import pytest as _pytest  # noqa: F811

        monkeypatch.setenv("AI_ARCHITECT_SERVER_PORT", "9090")
        runner = CliRunner()
        result = runner.invoke(cli, ["config-validate"])
        assert result.exit_code == 0
        assert "9090" in result.output
