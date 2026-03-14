"""Tests for configuration loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect_mcp._config.loader import (
    DEFAULTS_PATH,
    _coerce_value,
    _merge_configs,
    load_config,
)
from ai_architect_mcp._config.models import ServerConfig


class TestCoerceValue:
    """Tests for _coerce_value helper."""

    def test_bool_true(self) -> None:
        assert _coerce_value("true") is True

    def test_bool_false(self) -> None:
        assert _coerce_value("false") is False

    def test_int(self) -> None:
        result = _coerce_value("42")
        assert result == 42
        assert isinstance(result, int)

    def test_float(self) -> None:
        result = _coerce_value("3.14")
        assert result == pytest.approx(3.14)
        assert isinstance(result, float)

    def test_string(self) -> None:
        result = _coerce_value("hello")
        assert result == "hello"
        assert isinstance(result, str)


class TestMergeConfigs:
    """Tests for _merge_configs helper."""

    def test_flat_merge(self) -> None:
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _merge_configs(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge(self) -> None:
        base = {"server": {"host": "localhost", "port": 8080}}
        override = {"server": {"port": 9090}}
        result = _merge_configs(base, override)
        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 9090


class TestLoadConfig:
    """Tests for load_config function."""

    def test_defaults_exist(self) -> None:
        assert DEFAULTS_PATH.exists()

    def test_load_defaults(self) -> None:
        config = load_config()
        assert isinstance(config, ServerConfig)
        assert config.server.port == 8080

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_ARCHITECT_SERVER_PORT", "9090")
        config = load_config()
        assert config.server.port == 9090

    def test_user_config_file(self, tmp_path: Path) -> None:
        user_config = tmp_path / "user.toml"
        user_config.write_text(
            '[server]\nport = 7777\n',
            encoding="utf-8",
        )
        config = load_config(config_path=user_config)
        assert config.server.port == 7777

    def test_env_overrides_user_config(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        user_config = tmp_path / "user.toml"
        user_config.write_text(
            '[server]\nport = 7777\n',
            encoding="utf-8",
        )
        monkeypatch.setenv("AI_ARCHITECT_SERVER_PORT", "5555")
        config = load_config(config_path=user_config)
        assert config.server.port == 5555

    def test_missing_config_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config(config_path=Path("/nonexistent/config.toml"))
