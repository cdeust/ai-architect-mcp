"""KS Adaptive Stability Consensus — convergence detection via KS test.

Uses Kolmogorov-Smirnov test for distribution convergence.
Research: Kolmogorov (1933), Smirnov (1948); Beta-Binomial per
Gelman et al. (2013).
"""

from __future__ import annotations

import math

from ai_architect_mcp._models.consensus import (
    AgreementLevel,
    ConsensusAlgorithm,
    ConsensusResult,
    DisagreementResolution,
)
from ai_architect_mcp._models.verification import ClaimEvaluation

DEFAULT_STABILITY_THRESHOLD = 0.1
DEFAULT_MIN_SAMPLES = 3
DEFAULT_CONFIDENCE_LEVEL = 0.95
VARIANCE_STABILITY_THRESHOLD = 0.02
CONFIDENCE_BOOST = 1.1
AGREEMENT_HIGH_VAR = 0.05
AGREEMENT_MEDIUM_VAR = 0.15
MAX_SAMPLE_SIZE = 20


class AdaptiveStabilityConsensus:
    """Consensus using Kolmogorov-Smirnov test for convergence.

    Detects when evaluator scores have stabilized by comparing
    the empirical CDF against an expected uniform distribution.
    """

    def __init__(
        self,
        stability_threshold: float = DEFAULT_STABILITY_THRESHOLD,
        min_samples: int = DEFAULT_MIN_SAMPLES,
        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
    ) -> None:
        """Initialize the adaptive stability consensus.

        Args:
            stability_threshold: KS statistic threshold for stability.
            min_samples: Minimum number of samples before convergence.
            confidence_level: Required confidence level.
        """
        self._stability_threshold = stability_threshold
        self._min_samples = min_samples
        self._confidence_level = confidence_level

    def resolve(
        self, evaluations: list[ClaimEvaluation]
    ) -> ConsensusResult:
        """Resolve evaluations using adaptive stability analysis.

        Args:
            evaluations: List of claim evaluations.

        Returns:
            ConsensusResult with stability-based consensus.

        Raises:
            ValueError: If evaluations list is empty.
        """
        if not evaluations:
            msg = "Cannot resolve consensus with zero evaluations"
            raise ValueError(msg)

        scores = [e.score for e in evaluations]
        confidences = [e.confidence for e in evaluations]

        total_conf = sum(confidences)
        if total_conf < 1e-10:
            consensus_score = sum(scores) / len(scores)
        else:
            consensus_score = (
                sum(s * c for s, c in zip(scores, confidences))
                / total_conf
            )

        ks_stat = self._calculate_ks_statistic(scores)
        variance = self._variance(scores)
        is_stable = (
            ks_stat < self._stability_threshold
            or variance < VARIANCE_STABILITY_THRESHOLD
        )

        consensus_confidence = sum(confidences) / len(confidences)
        if is_stable:
            consensus_confidence = min(
                1.0, consensus_confidence * CONFIDENCE_BOOST
            )

        agreement = self._classify_agreement(variance)
        converged = is_stable and len(scores) >= self._min_samples

        resolution = (
            DisagreementResolution.ACCEPT
            if converged
            else DisagreementResolution.RE_EVALUATE
        )

        iterations = (
            self._estimate_sample_size(scores) if not converged else 1
        )

        return ConsensusResult(
            algorithm=ConsensusAlgorithm.ADAPTIVE_STABILITY,
            consensus_score=round(consensus_score, 6),
            consensus_confidence=round(
                min(1.0, consensus_confidence), 6
            ),
            agreement_level=agreement,
            resolution=resolution,
            individual_scores=scores,
            iteration_count=max(1, iterations),
            converged=converged,
        )

    def _calculate_ks_statistic(self, scores: list[float]) -> float:
        """Calculate KS statistic: max |empirical_CDF - expected_CDF|.

        Args:
            scores: List of scores (assumed in [0, 1]).

        Returns:
            Maximum absolute difference between CDFs.
        """
        if len(scores) < 2:
            return 0.0
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        max_diff = 0.0
        for i, score in enumerate(sorted_scores):
            empirical_cdf = (i + 1) / n
            expected_cdf = score
            max_diff = max(max_diff, abs(empirical_cdf - expected_cdf))
        return max_diff

    def _variance(self, values: list[float]) -> float:
        """Calculate population variance.

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
        if variance < AGREEMENT_HIGH_VAR:
            return AgreementLevel.HIGH
        if variance < AGREEMENT_MEDIUM_VAR:
            return AgreementLevel.MEDIUM
        return AgreementLevel.LOW

    def _estimate_sample_size(self, scores: list[float]) -> int:
        """Beta-Binomial sample size estimation.

        Args:
            scores: Current scores to estimate from.

        Returns:
            Estimated number of additional samples needed.
        """
        if not scores:
            return self._min_samples
        mean = sum(scores) / len(scores)
        var = self._variance(scores)
        if var < 1e-10:
            return self._min_samples
        ratio = mean * (1 - mean) / max(var, 1e-10)
        alpha = mean * (ratio - 1)
        beta = (1 - mean) * (ratio - 1)
        alpha = max(0.1, alpha)
        beta = max(0.1, beta)
        n = int(math.ceil((alpha + beta) / self._stability_threshold))
        return max(self._min_samples, min(n, MAX_SAMPLE_SIZE))
