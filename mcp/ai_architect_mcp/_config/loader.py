"""Configuration loader — TOML parsing with environment variable overrides.

Priority order: CLI flag > AI_ARCHITECT_* env var > config file > defaults.
Uses tomllib (stdlib >= 3.11) for TOML parsing.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from ai_architect_mcp._config.models import ServerConfig

DEFAULTS_PATH = Path(__file__).parent / "defaults.toml"
ENV_PREFIX = "AI_ARCHITECT_"
SECTION_SEPARATOR = "_"


def _load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file and return its contents.

    Args:
        path: Path to the TOML file.

    Returns:
        Parsed TOML as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        tomllib.TOMLDecodeError: If the file is not valid TOML.
    """
    with path.open("rb") as f:
        return tomllib.load(f)


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides to config.

    Environment variables follow the pattern:
    AI_ARCHITECT_{SECTION}_{KEY} (all uppercase).

    For example:
    - AI_ARCHITECT_SERVER_PORT=9090 -> config["server"]["port"] = 9090
    - AI_ARCHITECT_VERIFICATION_CONFIDENCE_THRESHOLD=0.8

    Args:
        config: Base configuration dictionary to override.

    Returns:
        Configuration with environment overrides applied.
    """
    for key, value in os.environ.items():
        if not key.startswith(ENV_PREFIX):
            continue

        remainder = key[len(ENV_PREFIX):].lower()
        parts = remainder.split(SECTION_SEPARATOR, 1)

        if len(parts) != 2:
            continue

        section, field = parts
        if section not in config:
            config[section] = {}

        config[section][field] = _coerce_value(value)

    return config


def _coerce_value(value: str) -> str | int | float | bool:
    """Coerce a string environment variable to an appropriate type.

    Args:
        value: The string value to coerce.

    Returns:
        Coerced value as int, float, bool, or str.
    """
    if value.lower() in ("true", "false"):
        return value.lower() == "true"

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def _merge_configs(
    base: dict[str, Any], override: dict[str, Any],
) -> dict[str, Any]:
    """Deep merge two config dictionaries.

    Args:
        base: Base configuration.
        override: Override configuration (takes priority).

    Returns:
        Merged configuration dictionary.
    """
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    config_path: Path | None = None,
) -> ServerConfig:
    """Load server configuration with full priority chain.

    Priority: env vars > config file > defaults.

    Args:
        config_path: Optional path to a user config TOML file.
            If None, only defaults and env vars are used.

    Returns:
        Fully resolved ServerConfig instance.

    Raises:
        FileNotFoundError: If config_path is specified but does not exist.
        ValueError: If configuration values fail validation.
    """
    config = _load_toml(DEFAULTS_PATH)

    if config_path is not None:
        user_config = _load_toml(config_path)
        config = _merge_configs(config, user_config)

    config = _apply_env_overrides(config)

    return ServerConfig.model_validate(config)
