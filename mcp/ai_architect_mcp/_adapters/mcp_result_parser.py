"""MCP result parsing utilities.

Extracts structured data from raw MCP tool results. Handles dict,
JSON string, CallToolResult (structured_content or content blocks),
and list of content blocks.
"""

from __future__ import annotations

import json
from typing import Any


def extract_mcp_data(raw: Any) -> dict[str, Any]:
    """Extract dict from raw MCP tool result.

    Handles: dict, JSON string, CallToolResult (structured_content
    or content blocks), and list of content blocks.

    Args:
        raw: Raw result — may be dict, string, or content blocks.

    Returns:
        Parsed dictionary.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"output": raw}
    if hasattr(raw, "structured_content") and isinstance(
        raw.structured_content, dict
    ):
        return raw.structured_content
    if hasattr(raw, "content"):
        content = raw.content
        if isinstance(content, list) and content:
            first = content[0]
            if hasattr(first, "text"):
                try:
                    return json.loads(first.text)
                except (json.JSONDecodeError, TypeError, AttributeError):
                    return {"output": str(first)}
    if isinstance(raw, list) and raw:
        first = raw[0]
        if hasattr(first, "text"):
            try:
                return json.loads(first.text)
            except (json.JSONDecodeError, TypeError, AttributeError):
                return {"output": str(first)}
    return {"output": str(raw)}
