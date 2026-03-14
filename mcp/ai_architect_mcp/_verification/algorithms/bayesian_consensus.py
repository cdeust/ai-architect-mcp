"""Bayesian Consensus — Beta-Binomial posterior updating.

Prior Beta(alpha, beta) + observed scores -> posterior.
Consensus score = posterior mean = alpha' / (alpha' + beta').
Confidence = 1.0 - credible_interval_width.
Research: Gelman et al. (2013) BDA3, DeGroot (1970).
"""

from __future__ import annotations

from scipy.stats import beta as beta_dist

from ai_architect_mcp._models.consensus import (
    AGREEMENT_HIGH_THRESHOLD,
    AGREEMENT_MEDIUM_THRESHOLD,
    DEFAULT_PRIOR_ALPHA,
    DEFAULT_PRIOR_BETA,
    AgreementLevel,
    ConsensusAlgorithm,
    ConsensusResult,
    DisagreementResolution,
)
from ai_architect_mcp._models.verification import ClaimEvaluation

CREDIBLE_INTERVAL_LEVEL = 0.95
SCORE_SUCCESS_THRESHOLD = 0.5
CONFIDENCE_BOOST_HIGH = 1.1
CONFIDENCE_PENALTY_LOW = 0.85
SCORE_THRESHOLD_REVIEW = 0.6


class BayesianConsensus:
    """Bayesian consensus using Beta-Binomial posterior updating.

    Treats each evaluator score as a Bernoulli trial (success if >= 0.5).
    Updates a Beta prior with observed successes/failures to produce
    a posterior distribution. Consensus score is the posterior mean.
    """

    def __init__(
        self,
        prior_alpha: float = DEFAULT_PRIOR_ALPHA,
        prior_beta: float = DEFAULT_PRIOR_BETA,
        credible_level: float = CREDIBLE_INTERVAL_LEVEL,
    ) -> None:
        """Initialize with Beta prior parameters.

        Args:
            prior_alpha: Alpha parameter of the Beta prior.
            prior_beta: Beta parameter of the Beta prior.
            credible_level: Level for the credible interval (e.g. 0.95).

        Raises:
            ValueError: If prior parameters are not positive.
        """
        if prior_alpha <= 0 or prior_beta <= 0:
            msg = (
                f"Prior parameters must be positive — got "
                f"alpha={prior_alpha}, beta={prior_beta}"
            )
            raise ValueError(msg)
        self._prior_alpha = prior_alpha
        self._prior_beta = prior_beta
        self._credible_level = credible_level

    def resolve(self, evaluations: list[ClaimEvaluation]) -> ConsensusResult:
        """Resolve evaluations using Bayesian posterior updating.

        Args:
            evaluations: List of claim evaluations to aggregate.

        Returns:
            ConsensusResult with Bayesian posterior consensus.

        Raises:
            ValueError: If evaluations list is empty.
        """
        if not evaluations:
            msg = "Cannot resolve consensus with zero evaluations"
            raise ValueError(msg)

        scores = [e.score for e in evaluations]
        successes = sum(1 for s in scores if s >= SCORE_SUCCESS_THRESHOLD)
        failures = len(scores) - successes

        posterior_alpha = self._prior_alpha + successes
        posterior_beta = self._prior_beta + failures

        consensus_score = posterior_alpha / (posterior_alpha + posterior_beta)

        lower = float(
            beta_dist.ppf(
                (1 - self._credible_level) / 2,
                posterior_alpha,
                posterior_beta,
            )
        )
        upper = float(
            beta_dist.ppf(
                1 - (1 - self._credible_level) / 2,
                posterior_alpha,
                posterior_beta,
            )
        )
        interval_width = upper - lower
        consensus_confidence = 1.0 - interval_width

        variance = self._variance(scores)
        agreement_level = self._classify_agreement(variance)

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
            algorithm=ConsensusAlgorithm.BAYESIAN,
            consensus_score=round(consensus_score, 6),
            consensus_confidence=round(
                max(0.0, min(1.0, consensus_confidence)), 6
            ),
            agreement_level=agreement_level,
            resolution=resolution,
            individual_scores=scores,
            iteration_count=1,
            converged=True,
        )

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
        if agreement == AgreementLevel.LOW:
            return DisagreementResolution.RE_EVALUATE
        if score < SCORE_THRESHOLD_REVIEW:
            return DisagreementResolution.FLAG_FOR_REVIEW
        return DisagreementResolution.ACCEPT
