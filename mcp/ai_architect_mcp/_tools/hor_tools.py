"""HOR tools — run all 64 rules, by category, or single rule."""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._verification.hor_rules.engine import HORRuleEngine
from ai_architect_mcp._app import mcp
from ai_architect_mcp._observability.instrumentation import observe_tool_call

_engine: HORRuleEngine | None = None


def _get_engine() -> HORRuleEngine:
    """Get or create the singleton HOR rule engine."""
    global _engine
    if _engine is None:
        _engine = HORRuleEngine()
    return _engine


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_run_hor_rules(
    artifact: dict[str, Any],
    base_score: float = 1.0,
) -> dict[str, Any]:
    """Run all 64 HOR rules against an artifact.

    Args:
        artifact: The artifact to verify (PRD content as dict).
        base_score: Starting score before penalties.

    Returns:
        Dict with results list, adjusted_score, and summary.
    """
    engine = _get_engine()
    results = await engine.run_all(artifact)
    adjusted = engine.calculate_adjusted_score(base_score, results)
    return {
        "results": [r.model_dump(mode="json") for r in results],
        "total_rules": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "adjusted_score": adjusted,
    }


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_run_hor_category(
    category: str,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    """Run HOR rules in a specific category.

    Args:
        category: Category name (structural, architecture, security, etc).
        artifact: The artifact to verify.

    Returns:
        Dict with category results.
    """
    engine = _get_engine()
    results = await engine.run_by_category(category, artifact)
    return {
        "category": category,
        "results": [r.model_dump(mode="json") for r in results],
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
    }


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_run_hor_single(
    rule_id: int,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    """Run a single HOR rule by ID.

    Args:
        rule_id: Rule number (1-64).
        artifact: The artifact to verify.

    Returns:
        HORRuleResult as a dictionary.
    """
    engine = _get_engine()
    result = await engine.run_single(rule_id, artifact)
    return result.model_dump(mode="json")
