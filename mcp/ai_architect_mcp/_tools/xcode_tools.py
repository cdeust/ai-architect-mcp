"""Xcode tools — build and test via port interfaces.

Exposes 2 MCP tools: ai_architect_run_build, ai_architect_run_tests.
"""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp.server import mcp

_root: CompositionRoot | None = None


def _get_root() -> CompositionRoot:
    """Get or create the composition root."""
    global _root
    if _root is None:
        _root = CompositionRoot()
    return _root


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_run_build(
    scheme: str,
    configuration: str = "Debug",
) -> dict[str, Any]:
    """Build an Xcode scheme.

    Args:
        scheme: Xcode scheme name.
        configuration: Build configuration.

    Returns:
        Build result dict.
    """
    xcode = _get_root().create_xcode()
    return await xcode.build(scheme, configuration)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_run_tests(
    scheme: str,
    test_plan: str | None = None,
) -> dict[str, Any]:
    """Run tests for an Xcode scheme.

    Args:
        scheme: Xcode scheme name.
        test_plan: Optional test plan.

    Returns:
        Test result dict.
    """
    xcode = _get_root().create_xcode()
    return await xcode.run_tests(scheme, test_plan)
