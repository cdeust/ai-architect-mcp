"""Progressive disclosure — render data at different detail levels.

Three rendering levels control how much context is exposed:
- L1 (config): Key names and types only — minimal footprint.
- L2 (summary): Key-value pairs with truncated values.
- L3 (full): Complete JSON dump with all details.
"""

from __future__ import annotations

import json
from typing import Any

from ai_architect_mcp._models.disclosure import DisclosureLevel

MAX_L2_VALUE_LENGTH: int = 120
L2_TRUNCATION_SUFFIX: str = "..."


def render_l1(data: dict[str, Any]) -> str:
    """Render config-only summary: key names with value types.

    Args:
        data: Dictionary to render.

    Returns:
        Compact string listing each key and its value type.
    """
    lines: list[str] = []
    for key, value in data.items():
        type_name = type(value).__name__
        lines.append(f"{key}: <{type_name}>")
    return "\n".join(lines)


def render_l2(data: dict[str, Any]) -> str:
    """Render summary: key-value pairs with long values truncated.

    Args:
        data: Dictionary to render.

    Returns:
        String with each key-value pair, values capped at 120 chars.
    """
    lines: list[str] = []
    for key, value in data.items():
        text = str(value)
        if len(text) > MAX_L2_VALUE_LENGTH:
            text = text[: MAX_L2_VALUE_LENGTH] + L2_TRUNCATION_SUFFIX
        lines.append(f"{key}: {text}")
    return "\n".join(lines)


def render_l3(data: dict[str, Any]) -> str:
    """Render full content: complete JSON dump.

    Args:
        data: Dictionary to render.

    Returns:
        Pretty-printed JSON string.
    """
    return json.dumps(data, indent=2, default=str)


def render(data: dict[str, Any], level: DisclosureLevel) -> str:
    """Dispatch to the appropriate rendering function.

    Args:
        data: Dictionary to render.
        level: Disclosure level controlling detail.

    Returns:
        Rendered string at the requested detail level.

    Raises:
        ValueError: If level is not a recognized DisclosureLevel.
    """
    dispatch = {
        DisclosureLevel.L1_CONFIG: render_l1,
        DisclosureLevel.L2_SUMMARY: render_l2,
        DisclosureLevel.L3_FULL: render_l3,
    }
    handler = dispatch.get(level)
    if handler is None:
        msg = f"Unknown disclosure level '{level}' — expected one of {list(dispatch.keys())}"
        raise ValueError(msg)
    return handler(data)
