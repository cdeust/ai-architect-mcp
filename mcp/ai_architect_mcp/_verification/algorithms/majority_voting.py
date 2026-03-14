"""Majority Voting Consensus — threshold-based majority decision.

Each evaluator score is cast as YES (>= threshold) or NO (< threshold).
Consensus = majority vote. Confidence = margin of victory.
Research: Condorcet (1785) Jury Theorem.
"""

from __future__ import annotations

import hashlib

from ai_architect_mcp._models.consensus import (
    AGREEMENT_HIGH_THRESHOLD,
    AGREEMENT_MEDIUM_THRESHOLD,
    DEFAULT_VOTING_THRESHOLD,
    AgreementLevel,
    ConsensusAlgorithm,
    ConsensusResult,
    DisagreementResolution,
    TieBreaker,
)
from ai_architect_mcp._models.verification import ClaimEvaluation

MARGIN_HIGH = 0.8
MARGIN_LOW = 0.2


class MajorityVotingConsensus:
    """Majority voting consensus with configurable tie-breaking.

    Converts continuous scores into binary votes using a threshold.
    The majority determines the outcome. Confidence is proportional
    to the margin of victory.
    """

    def __init__(
        self,
        voting_threshold: float = DEFAULT_VOTING_THRESHOLD,
        acceptance_ratio: float = DEFAULT_VOTING_THRESHOLD,
        tie_breaker: TieBreaker = TieBreaker.HIGHEST_CONFIDENCE,
    ) -> None:
        """Initialize majority voting consensus.

        Args:
            voting_threshold: Score >= this value counts as YES.
            acceptance_ratio: Fraction of YES votes needed to accept.
            tie_breaker: Strategy for resolving exact ties.

        Raises:
            ValueError: If thresholds are not in (0, 1].
        """
        if not 0 < voting_threshold <= 1:
            msg = f"voting_threshold must be in (0, 1] — got {voting_threshold}"
            raise ValueError(msg)
        if not 0 < acceptance_ratio <= 1:
            msg = f"acceptance_ratio must be in (0, 1] — got {acceptance_ratio}"
            raise ValueError(msg)
        self._voting_threshold = voting_threshold
        self._acceptance_ratio = acceptance_ratio
        self._tie_breaker = tie_breaker

    def resolve(self, evaluations: list[ClaimEvaluation]) -> ConsensusResult:
        """Resolve evaluations using majority voting.

        Args:
            evaluations: List of claim evaluations to aggregate.

        Returns:
            ConsensusResult with majority voting consensus.

        Raises:
            ValueError: If evaluations list is empty.
        """
        if not evaluations:
            msg = "Cannot resolve consensus with zero evaluations"
            raise ValueError(msg)

        scores = [e.score for e in evaluations]
        confidences = [e.confidence for e in evaluations]
        total = len(scores)

        yes_indices = [
            i for i, s in enumerate(scores) if s >= self._voting_threshold
        ]
        no_indices = [
            i for i, s in enumerate(scores) if s < self._voting_threshold
        ]
        yes_count = len(yes_indices)
        no_count = len(no_indices)

        yes_ratio = yes_count / total
        is_tie = yes_count == no_count

        if is_tie:
            accepted = self._break_tie(
                yes_indices, no_indices, confidences, scores
            )
        else:
            accepted = yes_ratio >= self._acceptance_ratio

        consensus_score = yes_ratio if accepted else (1.0 - yes_ratio)
        margin = abs(yes_count - no_count) / total
        consensus_confidence = margin

        variance = self._variance(scores)
        agreement_level = self._classify_agreement(margin)

        resolution = self._determine_resolution(
            accepted, margin, is_tie
        )

        return ConsensusResult(
            algorithm=ConsensusAlgorithm.MAJORITY_VOTING,
            consensus_score=round(consensus_score, 6),
            consensus_confidence=round(
                max(0.0, min(1.0, consensus_confidence)), 6
            ),
            agreement_level=agreement_level,
            resolution=resolution,
            individual_scores=scores,
            iteration_count=1,
            converged=not is_tie or self._tie_breaker != TieBreaker.ESCALATE_TO_DEBATE,
        )

    def _break_tie(
        self,
        yes_indices: list[int],
        no_indices: list[int],
        confidences: list[float],
        scores: list[float],
    ) -> bool:
        """Break a tie using the configured strategy.

        Args:
            yes_indices: Indices of YES voters.
            no_indices: Indices of NO voters.
            confidences: Confidence values for all evaluators.
            scores: Score values for all evaluators.

        Returns:
            True if the tie resolves to ACCEPT, False otherwise.
        """
        if self._tie_breaker == TieBreaker.HIGHEST_CONFIDENCE:
            yes_conf = (
                sum(confidences[i] for i in yes_indices) / len(yes_indices)
                if yes_indices
                else 0.0
            )
            no_conf = (
                sum(confidences[i] for i in no_indices) / len(no_indices)
                if no_indices
                else 0.0
            )
            return yes_conf >= no_conf

        if self._tie_breaker == TieBreaker.RANDOM_SEEDED:
            seed_data = ",".join(f"{s:.6f}" for s in sorted(scores))
            digest = hashlib.sha256(seed_data.encode()).hexdigest()
            return int(digest[0], 16) >= 8

        return False

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

    def _classify_agreement(self, margin: float) -> AgreementLevel:
        """Classify agreement based on margin of victory.

        Args:
            margin: Absolute margin between YES and NO ratios.

        Returns:
            AgreementLevel classification.
        """
        if margin >= MARGIN_HIGH:
            return AgreementLevel.HIGH
        if margin >= MARGIN_LOW:
            return AgreementLevel.MEDIUM
        return AgreementLevel.LOW

    def _determine_resolution(
        self, accepted: bool, margin: float, is_tie: bool
    ) -> DisagreementResolution:
        """Determine resolution based on vote outcome.

        Args:
            accepted: Whether the majority voted to accept.
            margin: Margin of victory.
            is_tie: Whether the vote was a tie.

        Returns:
            Appropriate DisagreementResolution strategy.
        """
        if is_tie and self._tie_breaker == TieBreaker.ESCALATE_TO_DEBATE:
            return DisagreementResolution.RE_EVALUATE
        if accepted and margin >= MARGIN_HIGH:
            return DisagreementResolution.ACCEPT
        if accepted:
            return DisagreementResolution.ACCEPT
        if margin < MARGIN_LOW:
            return DisagreementResolution.FLAG_FOR_REVIEW
        return DisagreementResolution.REJECT
