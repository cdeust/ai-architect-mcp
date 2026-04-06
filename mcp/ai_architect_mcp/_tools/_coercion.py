"""Argument coercion helpers for MCP tool boundaries.

MCP clients may serialize object arguments as JSON strings when
crossing the protocol boundary. These helpers accept both forms
without requiring clients to manage the difference.
"""

from __future__ import annotations

import json
from typing import Any


def coerce_dict(value: Any) -> dict[str, Any]:
    """Coerce a value into a dict.

    Accepts:
        * dict — returned as-is
        * str — parsed as JSON and validated to be a JSON object

    Raises:
        TypeError: If the value is neither a dict nor a valid JSON string
            representing an object.
        ValueError: If the string is malformed JSON.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise TypeError(
                f"Expected JSON object, got {type(parsed).__name__}"
            )
        return parsed
    raise TypeError(
        f"Expected dict or JSON string, got {type(value).__name__}"
    )
