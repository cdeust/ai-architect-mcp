"""Consensus router — maps ConsensusAlgorithm enum to implementations.

Single entry point for all consensus algorithm instantiation.
Replaces inline routing in verification_tools.py.
"""

from __future__ import annotations

from typing import Union

from ai_architect_mcp._models.consensus import ConsensusAlgorithm, TieBreaker
from ai_architect_mcp._verification.algorithms.adaptive_stability import (
    AdaptiveStabilityConsensus,
)
from ai_architect_mcp._verification.algorithms.bayesian_consensus import (
    BayesianConsensus,
)
from ai_architect_mcp._verification.algorithms.majority_voting import (
    MajorityVotingConsensus,
)
from ai_architect_mcp._verification.algorithms.weighted_average import (
    WeightedAverageConsensus,
)

ConsensusInstance = Union[
    WeightedAverageConsensus,
    AdaptiveStabilityConsensus,
    BayesianConsensus,
    MajorityVotingConsensus,
]


def get_consensus_algorithm(
    algorithm: ConsensusAlgorithm,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    voting_threshold: float = 0.5,
    tie_breaker: TieBreaker = TieBreaker.HIGHEST_CONFIDENCE,
) -> ConsensusInstance:
    """Create and return a consensus algorithm instance.

    Args:
        algorithm: Which consensus algorithm to use.
        prior_alpha: Alpha for Bayesian prior (only used with BAYESIAN).
        prior_beta: Beta for Bayesian prior (only used with BAYESIAN).
        voting_threshold: Score threshold for YES vote (only MAJORITY_VOTING).
        tie_breaker: Tie-breaking strategy (only used with MAJORITY_VOTING).

    Returns:
        An instance of the requested consensus algorithm.

    Raises:
        ValueError: If algorithm is not a valid ConsensusAlgorithm.
    """
    if algorithm == ConsensusAlgorithm.WEIGHTED_AVERAGE:
        return WeightedAverageConsensus()
    if algorithm == ConsensusAlgorithm.ADAPTIVE_STABILITY:
        return AdaptiveStabilityConsensus()
    if algorithm == ConsensusAlgorithm.BAYESIAN:
        return BayesianConsensus(
            prior_alpha=prior_alpha,
            prior_beta=prior_beta,
        )
    if algorithm == ConsensusAlgorithm.MAJORITY_VOTING:
        return MajorityVotingConsensus(
            voting_threshold=voting_threshold,
            tie_breaker=tie_breaker,
        )
    msg = f"Unknown consensus algorithm: {algorithm}"
    raise ValueError(msg)
