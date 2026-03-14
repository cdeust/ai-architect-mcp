"""Configuration system — TOML-based config with environment variable overrides.

Loads configuration from defaults.toml, optional user config file,
and AI_ARCHITECT_* environment variable overrides.
"""

from __future__ import annotations

from ai_architect_mcp._config.loader import load_config
from ai_architect_mcp._config.models import ServerConfig

__all__ = [
    "ServerConfig",
    "load_config",
]
