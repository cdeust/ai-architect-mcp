"""Plan Interview gate logic.

Evaluates dimension scores to produce a gate decision:
APPROVED, PROVISIONAL, or REJECTED.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ai_architect_mcp._interview.models import (
    DimensionScore,
    DimensionType,
    GateDecision,
    InterviewConfig,
    InterviewResult,
)
from ai_architect_mcp._interview.scorers import SCORER_REGISTRY

CRITICAL_DIMENSIONS: frozenset[DimensionType] = frozenset({
    DimensionType.D1_SECTIONS_PRESENT,
    DimensionType.D2_HEADER_FORMAT,
    DimensionType.D3_ID_CONSISTENCY,
    DimensionType.D4_OUTLINE_FLOW,
    DimensionType.D6_CLARITY_LEVEL,
    DimensionType.D8_REQUIREMENT_PRECISION,
    DimensionType.D10_SUCCESS_METRICS,
})

ADVISORY_DIMENSIONS: frozenset[DimensionType] = frozenset({
    DimensionType.D5_ARTIFACT_COHERENCE,
    DimensionType.D7_STAKEHOLDER_ALIGNMENT,
    DimensionType.D9_ASSUMPTION_VALIDATION,
})


def evaluate_gate(
    scores: list[DimensionScore],
    config: InterviewConfig | None = None,
) -> GateDecision:
    """Determine the gate decision from a set of dimension scores.

    Args:
        scores: List of scored dimensions.
        config: Optional thresholds; defaults are used if omitted.

    Returns:
        REJECTED if any critical dimension fails, PROVISIONAL if all
        critical pass but any advisory fails, APPROVED otherwise.
    """
    if config is None:
        config = InterviewConfig()

    score_map = {s.dimension_type: s for s in scores}

    # Check critical dimensions
    for dim in CRITICAL_DIMENSIONS:
        dim_score = score_map.get(dim)
        if dim_score is not None and dim_score.score < config.critical_threshold:
            return GateDecision.REJECTED

    # Check advisory dimensions
    for dim in ADVISORY_DIMENSIONS:
        dim_score = score_map.get(dim)
        if dim_score is not None and dim_score.score < config.advisory_threshold:
            return GateDecision.PROVISIONAL

    return GateDecision.APPROVED


def run_full_interview(
    artifact: dict[str, Any],
    config: InterviewConfig | None = None,
    finding_id: str | None = None,
) -> InterviewResult:
    """Run all 10 dimension scorers and evaluate the gate.

    Args:
        artifact: The PRD artifact dictionary.
        config: Optional thresholds; defaults are used if omitted.
        finding_id: Optional finding identifier; auto-generated if omitted.

    Returns:
        Complete InterviewResult with all scores and gate decision.
    """
    if config is None:
        config = InterviewConfig()

    if finding_id is None:
        finding_id = f"INTERVIEW-{uuid4().hex[:8].upper()}"

    scores: list[DimensionScore] = []
    for dimension_type, scorer in SCORER_REGISTRY.items():
        scores.append(scorer(artifact))

    decision = evaluate_gate(scores, config)

    return InterviewResult(
        finding_id=finding_id,
        dimension_scores=scores,
        gate_decision=decision,
    )
