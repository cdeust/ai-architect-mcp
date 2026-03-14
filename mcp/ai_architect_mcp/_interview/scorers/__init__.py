"""Scorer registry and dispatcher for Plan Interview dimensions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

from ai_architect_mcp._interview.scorers.artifact_coherence import score_artifact_coherence
from ai_architect_mcp._interview.scorers.assumption_validation import score_assumption_validation
from ai_architect_mcp._interview.scorers.clarity_level import score_clarity_level
from ai_architect_mcp._interview.scorers.header_format import score_header_format
from ai_architect_mcp._interview.scorers.id_consistency import score_id_consistency
from ai_architect_mcp._interview.scorers.outline_flow import score_outline_flow
from ai_architect_mcp._interview.scorers.requirement_precision import score_requirement_precision
from ai_architect_mcp._interview.scorers.sections_present import score_sections_present
from ai_architect_mcp._interview.scorers.stakeholder_alignment import score_stakeholder_alignment
from ai_architect_mcp._interview.scorers.success_metrics import score_success_metrics

ScorerFunction = Callable[[dict[str, Any]], DimensionScore]

SCORER_REGISTRY: dict[DimensionType, ScorerFunction] = {
    DimensionType.D1_SECTIONS_PRESENT: score_sections_present,
    DimensionType.D2_HEADER_FORMAT: score_header_format,
    DimensionType.D3_ID_CONSISTENCY: score_id_consistency,
    DimensionType.D4_OUTLINE_FLOW: score_outline_flow,
    DimensionType.D5_ARTIFACT_COHERENCE: score_artifact_coherence,
    DimensionType.D6_CLARITY_LEVEL: score_clarity_level,
    DimensionType.D7_STAKEHOLDER_ALIGNMENT: score_stakeholder_alignment,
    DimensionType.D8_REQUIREMENT_PRECISION: score_requirement_precision,
    DimensionType.D9_ASSUMPTION_VALIDATION: score_assumption_validation,
    DimensionType.D10_SUCCESS_METRICS: score_success_metrics,
}


def score_dimension(dimension: DimensionType, artifact: dict[str, Any]) -> DimensionScore:
    """Dispatch scoring to the appropriate dimension scorer.

    Args:
        dimension: Which dimension to evaluate.
        artifact: The PRD artifact dictionary.

    Returns:
        The computed DimensionScore for the requested dimension.

    Raises:
        KeyError: If the dimension has no registered scorer.
    """
    scorer = SCORER_REGISTRY.get(dimension)
    if scorer is None:
        msg = f"No scorer registered for dimension {dimension.value}"
        raise KeyError(msg)
    return scorer(artifact)
