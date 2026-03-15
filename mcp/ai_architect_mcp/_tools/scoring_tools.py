"""Scoring tools — compound score calculation and propagation analysis."""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._scoring.compound import calculate_compound_score
from ai_architect_mcp._scoring.propagation import calculate_propagation_impact, trace_propagation
from ai_architect_mcp._app import mcp


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_compound_score(
    relevance: float,
    uniqueness: float,
    impact: float,
    confidence: float,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Calculate a compound score from individual signals.

    Args:
        relevance: Relevance score (0.0-1.0).
        uniqueness: Uniqueness score (0.0-1.0).
        impact: Impact score (0.0-1.0).
        confidence: Confidence score (0.0-1.0).
        weights: Optional custom weights.

    Returns:
        CompoundScore as a dictionary.
    """
    result = calculate_compound_score(relevance, uniqueness, impact, confidence, weights)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_trace_propagation(
    source_module: str,
    dependency_graph: dict[str, list[str]],
    max_depth: int = 5,
) -> dict[str, Any]:
    """Trace impact propagation through a dependency graph.

    Args:
        source_module: Module where change originates.
        dependency_graph: Adjacency list of dependencies.
        max_depth: Maximum propagation depth.

    Returns:
        Dict with propagation paths and impact score.
    """
    paths = trace_propagation(source_module, dependency_graph, max_depth)
    impact = calculate_propagation_impact(paths)
    return {
        "source": source_module,
        "paths": [p.model_dump(mode="json") for p in paths],
        "total_paths": len(paths),
        "impact_score": impact,
    }
