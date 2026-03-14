"""Weighted Average Consensus — standard ensemble consensus.

Formula: consensus_score = sum(score * confidence) / sum(confidence)
Agreement: variance < 0.05 = high, < 0.15 = medium, else low.
Research: Dietterich (2000) — Ensemble Methods in Machine Learning.
"""

from __future__ import annotations

from ai_architect_mcp._models.consensus import (
    AGREEMENT_HIGH_THRESHOLD,
    AGREEMENT_MEDIUM_THRESHOLD,
    AgreementLevel,
    ConsensusAlgorithm,
    ConsensusResult,
    DisagreementResolution,
)
from ai_architect_mcp._models.verification import ClaimEvaluation

CONFIDENCE_BOOST_HIGH = 1.1
CONFIDENCE_PENALTY_LOW = 0.85
SCORE_THRESHOLD_REVIEW = 0.6
SCORE_THRESHOLD_REJECT = 0.5


class WeightedAverageConsensus:
    """Standard weighted average consensus algorithm.

    Aggregates multiple evaluator scores using confidence-weighted
    averaging. Classifies agreement level by variance thresholds.
    """

    def resolve(self, evaluations: list[ClaimEvaluation]) -> ConsensusResult:
        """Resolve multiple evaluations into a consensus.

        Args:
            evaluations: List of claim evaluations to aggregate.

        Returns:
            ConsensusResult with aggregated score and agreement level.

        Raises:
            ValueError: If evaluations list is empty.
        """
        if not evaluations:
            msg = "Cannot resolve consensus with zero evaluations"
            raise ValueError(msg)

        scores = [e.score for e in evaluations]
        confidences = [e.confidence for e in evaluations]

        total_confidence = sum(confidences)
        if total_confidence < 1e-10:
            consensus_score = sum(scores) / len(scores)
        else:
            consensus_score = (
                sum(s * c for s, c in zip(scores, confidences))
                / total_confidence
            )

        variance = self._variance(scores)
        agreement_level = self._classify_agreement(variance)

        consensus_confidence = sum(confidences) / len(confidences)
        if agreement_level == AgreementLevel.HIGH:
            consensus_confidence = min(
                1.0, consensus_confidence * CONFIDENCE_BOOST_HIGH
            )
        elif agreement_level == AgreementLevel.LOW:
            consensus_confidence *= CONFIDENCE_PENALTY_LOW

        resolution = self._determine_resolution(
            agreement_level, consensus_score
        )

        return ConsensusResult(
            algorithm=ConsensusAlgorithm.WEIGHTED_AVERAGE,
            consensus_score=round(consensus_score, 6),
            consensus_confidence=round(min(1.0, consensus_confidence), 6),
            agreement_level=agreement_level,
            resolution=resolution,
            individual_scores=scores,
            iteration_count=1,
            converged=True,
        )

    def _variance(self, values: list[float]) -> float:
        """Calculate variance of a list of values.

        Args:
            values: Numeric values.

        Returns:
            Population variance.
        """
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    def _classify_agreement(self, variance: float) -> AgreementLevel:
        """Classify agreement level based on variance.

        Args:
            variance: Score variance.

        Returns:
            AgreementLevel classification.
        """
        if variance < AGREEMENT_HIGH_THRESHOLD:
            return AgreementLevel.HIGH
        if variance < AGREEMENT_MEDIUM_THRESHOLD:
            return AgreementLevel.MEDIUM
        return AgreementLevel.LOW

    def _determine_resolution(
        self, agreement: AgreementLevel, score: float
    ) -> DisagreementResolution:
        """Determine resolution based on agreement and score.

        Args:
            agreement: Current agreement level.
            score: Consensus score.

        Returns:
            Appropriate DisagreementResolution strategy.
        """
        if agreement == AgreementLevel.HIGH:
            return DisagreementResolution.ACCEPT
        if agreement == AgreementLevel.MEDIUM and score < SCORE_THRESHOLD_REVIEW:
            return DisagreementResolution.FLAG_FOR_REVIEW
        if agreement == AgreementLevel.LOW and score < SCORE_THRESHOLD_REJECT:
            return DisagreementResolution.REJECT
        return DisagreementResolution.ACCEPT
