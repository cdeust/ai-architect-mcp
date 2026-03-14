"""Confidence Fusion Engine — deterministic multi-source confidence aggregation.

Combines confidence estimates from different enhancement algorithms
into a single fused estimate with bounds. Zero LLM calls.
"""

from __future__ import annotations

from ai_architect_mcp._models.prompting import (
    ConfidenceEstimate,
    EnhancementSource,
    FusedConfidence,
)

SOURCE_BIAS: dict[EnhancementSource, float] = {
    EnhancementSource.THOUGHT_BUFFER: 0.0,
    EnhancementSource.ADAPTIVE_EXPANSION: 0.02,
    EnhancementSource.COLLABORATIVE_INFERENCE: -0.01,
    EnhancementSource.METACOGNITIVE: 0.01,
    EnhancementSource.TRM_REFINEMENT: 0.0,
}

DISAGREEMENT_FACTOR = 0.5
CONSENSUS_THRESHOLD = 0.8
CONFIDENCE_THRESHOLD = 0.7
CONSENSUS_SCALE = 0.2


class ConfidenceFusionEngine:
    """Deterministic confidence fusion from multiple sources."""

    def fuse(
        self,
        estimates: list[ConfidenceEstimate],
        weights: dict[EnhancementSource, float] | None = None,
    ) -> FusedConfidence:
        """Fuse multiple confidence estimates into one.

        Args:
            estimates: Confidence estimates from different sources.
            weights: Optional per-source weights. Equal weights if None.

        Returns:
            FusedConfidence with point estimate and bounds.

        Raises:
            ValueError: If estimates list is empty.
        """
        if not estimates:
            msg = "Cannot fuse zero confidence estimates"
            raise ValueError(msg)

        effective_weights = weights or {e.source: 1.0 for e in estimates}
        total_weight = sum(
            effective_weights.get(e.source, 1.0) for e in estimates
        )

        if total_weight < 1e-10:
            total_weight = float(len(estimates))
            effective_weights = {e.source: 1.0 for e in estimates}

        fused = 0.0
        for estimate in estimates:
            bias = SOURCE_BIAS.get(estimate.source, 0.0)
            corrected = max(0.0, min(1.0, estimate.value - bias))
            w = effective_weights.get(estimate.source, 1.0)
            fused += corrected * w

        fused /= total_weight

        base_uncertainty = sum(e.uncertainty for e in estimates) / len(estimates)
        values = [e.value for e in estimates]
        disagreement = max(values) - min(values) if len(values) > 1 else 0.0
        total_uncertainty = base_uncertainty + disagreement * DISAGREEMENT_FACTOR

        agreement = 1.0 - disagreement
        if agreement > CONSENSUS_THRESHOLD and fused > CONFIDENCE_THRESHOLD:
            bonus = (agreement - CONSENSUS_THRESHOLD) * CONSENSUS_SCALE
            fused = min(1.0, fused + bonus)

        lower = max(0.0, fused - total_uncertainty)
        upper = min(1.0, fused + total_uncertainty)

        return FusedConfidence(
            point=round(fused, 6),
            lower=round(lower, 6),
            upper=round(upper, 6),
            contributing_estimates=estimates,
            fusion_method="weighted_average_with_bias_correction",
        )
