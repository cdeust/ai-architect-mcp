"""Compound scoring — multi-signal score aggregation.

Combines relevance, uniqueness, impact, and confidence signals into
a single compound score using weighted aggregation. Weights are
configurable per stage but the aggregation logic is deterministic.
"""

from __future__ import annotations

from ai_architect_mcp._models.scoring import CompoundScore

DEFAULT_WEIGHTS: dict[str, float] = {
    "relevance": 0.3,
    "uniqueness": 0.2,
    "impact": 0.3,
    "confidence": 0.2,
}


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Normalize weights so they sum to 1.0.

    Args:
        weights: Raw weight values keyed by signal name.

    Returns:
        Normalized weights summing to 1.0.

    Raises:
        ValueError: If all weight values are zero.
    """
    total = sum(weights.values())
    if abs(total) < 1e-10:
        msg = "Cannot normalize weights — all values are zero"
        raise ValueError(msg)
    return {k: v / total for k, v in weights.items()}


def calculate_compound_score(
    relevance: float,
    uniqueness: float,
    impact: float,
    confidence: float,
    weights: dict[str, float] | None = None,
) -> CompoundScore:
    """Calculate a compound score from individual signal scores.

    Args:
        relevance: Relevance score (0.0-1.0).
        uniqueness: Uniqueness score (0.0-1.0).
        impact: Impact score (0.0-1.0).
        confidence: Confidence score (0.0-1.0).
        weights: Optional custom weights. Uses DEFAULT_WEIGHTS if None.

    Returns:
        CompoundScore with weighted total and normalized weights.
    """
    raw_weights = weights if weights is not None else dict(DEFAULT_WEIGHTS)
    normalized = normalize_weights(raw_weights)

    weighted_total = (
        relevance * normalized["relevance"]
        + uniqueness * normalized["uniqueness"]
        + impact * normalized["impact"]
        + confidence * normalized["confidence"]
    )

    return CompoundScore(
        relevance=relevance,
        uniqueness=uniqueness,
        impact=impact,
        confidence=confidence,
        weighted_total=round(weighted_total, 10),
        weights=normalized,
    )
