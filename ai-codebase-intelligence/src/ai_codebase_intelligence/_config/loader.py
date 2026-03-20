"""Configuration loader — TOML defaults + environment overrides.

Follows ai-architect pattern: load defaults.toml, then override
with CI_ prefixed environment variables.

OBSERVATION: ai-architect uses AI_ARCHITECT_ prefix for env vars.
SOLUTION: CI_ prefix for codebase intelligence (shorter, clearer).
  CI_INDEXING_MAX_FILE_SIZE_BYTES=1048576 overrides [indexing] max_file_size_bytes.
"""

from __future__ import annotations

import os
from pathlib import Path

from .models import CodeIntelligenceConfig

_config: CodeIntelligenceConfig | None = None

DEFAULTS_PATH = Path(__file__).parent / "defaults.toml"


def load_config() -> CodeIntelligenceConfig:
    """Load configuration from defaults.toml + environment overrides.

    Returns:
        Validated CodeIntelligenceConfig instance.
    """
    global _config
    if _config is not None:
        return _config

    # Load TOML defaults
    raw: dict[str, object] = {}
    if DEFAULTS_PATH.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(DEFAULTS_PATH, "rb") as f:
            raw = tomllib.load(f)

    # Apply environment overrides (CI_ prefix)
    _apply_env_overrides(raw)

    _config = CodeIntelligenceConfig.model_validate(raw)
    return _config


def get_config() -> CodeIntelligenceConfig:
    """Get the current config, loading if needed.

    Returns:
        The singleton CodeIntelligenceConfig.
    """
    if _config is None:
        return load_config()
    return _config


def _apply_env_overrides(raw: dict[str, object]) -> None:
    """Apply CI_ prefixed environment variables to raw config dict.

    Mapping: CI_SECTION_KEY=value -> raw[section][key] = value
    Example: CI_INDEXING_MAX_FILE_SIZE_BYTES=1048576
    """
    prefix = "CI_"
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix):].lower().split("_", 1)
        if len(parts) != 2:
            continue
        section, field = parts[0], parts[1]
        if section not in raw:
            raw[section] = {}
        section_dict = raw[section]
        if not isinstance(section_dict, dict):
            continue
        # Type coercion — try int, then float, then string
        try:
            section_dict[field] = int(value)
        except ValueError:
            try:
                section_dict[field] = float(value)
            except ValueError:
                section_dict[field] = value
