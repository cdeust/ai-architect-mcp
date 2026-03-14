"""Python hook system for MCP server runtime enforcement.

Separate from shell hooks (hooks/ directory) which enforce Claude Code
behavior. Python hooks enforce runtime constraints within the MCP server:
session lifecycle, output validation, security classification, state tracking.
"""

from __future__ import annotations

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)
from ai_architect_mcp._hooks.registry import HookRegistry

__all__ = [
    "Hook",
    "HookContext",
    "HookPhase",
    "HookRegistry",
    "HookResult",
    "HookStatus",
]
