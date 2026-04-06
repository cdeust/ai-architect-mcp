"""MCP tools for the Plan Interview stage (4.5).

Exposes three tools: single-dimension scoring, full interview gate,
and result querying.
"""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._interview.gate import run_full_interview
from ai_architect_mcp._interview.models import (
    DimensionType,
    InterviewConfig,
    InterviewResult,
)
from ai_architect_mcp._interview.scorers import score_dimension
from ai_architect_mcp._app import mcp
from ai_architect_mcp._observability.instrumentation import observe_tool_call
from ai_architect_mcp._tools._coercion import coerce_dict

# Module-level cache for recent interview results keyed by finding_id.
_result_cache: dict[str, InterviewResult] = {}

MAX_CACHE_SIZE = 100


def _store_result(result: InterviewResult) -> None:
    """Store an interview result in the module cache.

    Args:
        result: The interview result to cache.
    """
    if len(_result_cache) >= MAX_CACHE_SIZE:
        oldest_key = next(iter(_result_cache))
        del _result_cache[oldest_key]
    _result_cache[result.finding_id] = result


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_score_dimension(
    dimension: str,
    artifact: dict[str, Any] | str,
) -> dict[str, Any]:
    """Score a single PRD dimension.

    Args:
        dimension: Dimension enum value (e.g. 'D1_SECTIONS_PRESENT').
        artifact: PRD artifact dictionary with a 'content' string field.

    Returns:
        Serialised DimensionScore as a dictionary.

    Raises:
        ValueError: If the dimension string is not a valid DimensionType.
        KeyError: If no scorer is registered for the dimension.
    """
    try:
        dim_type = DimensionType(dimension)
    except ValueError:
        valid = [d.value for d in DimensionType]
        msg = f"Invalid dimension '{dimension}' — valid values: {valid}"
        raise ValueError(msg) from None

    result = score_dimension(dim_type, coerce_dict(artifact))
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_run_interview_gate(
    artifact: dict[str, Any] | str,
    finding_id: str = "UNKNOWN",
) -> dict[str, Any]:
    """Run the full Plan Interview gate on a PRD artifact.

    Evaluates all 10 dimensions and produces an APPROVED, PROVISIONAL,
    or REJECTED decision.

    Args:
        artifact: PRD artifact dictionary with a 'content' string field.
        finding_id: Identifier linking this result to a pipeline finding.

    Returns:
        Serialised InterviewResult as a dictionary.
    """
    config = InterviewConfig()
    result = run_full_interview(coerce_dict(artifact), config, finding_id)
    _store_result(result)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_query_interview_results(
    finding_id: str,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """Query cached interview results by finding ID.

    Args:
        finding_id: The finding ID to look up.
        min_score: Optional minimum score filter for dimension scores.

    Returns:
        Dictionary with the interview result or an error message.
    """
    result = _result_cache.get(finding_id)
    if result is None:
        return {
            "found": False,
            "error": f"No interview result cached for finding_id='{finding_id}'",
        }

    data = result.model_dump(mode="json")

    if min_score > 0.0:
        data["dimension_scores"] = [
            s for s in data["dimension_scores"]
            if s["score"] >= min_score
        ]

    data["found"] = True
    return data
