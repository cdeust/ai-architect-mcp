"""Tests for consensus router — algorithm dispatch."""

from __future__ import annotations

import pytest

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
from ai_architect_mcp._verification.consensus_router import (
    get_consensus_algorithm,
)


class TestConsensusRouter:
    """Tests for get_consensus_algorithm dispatch."""

    def test_weighted_average(self) -> None:
        """Routes to WeightedAverageConsensus."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.WEIGHTED_AVERAGE)
        assert isinstance(algo, WeightedAverageConsensus)

    def test_adaptive_stability(self) -> None:
        """Routes to AdaptiveStabilityConsensus."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.ADAPTIVE_STABILITY)
        assert isinstance(algo, AdaptiveStabilityConsensus)

    def test_bayesian(self) -> None:
        """Routes to BayesianConsensus."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.BAYESIAN)
        assert isinstance(algo, BayesianConsensus)

    def test_majority_voting(self) -> None:
        """Routes to MajorityVotingConsensus."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.MAJORITY_VOTING)
        assert isinstance(algo, MajorityVotingConsensus)

    def test_bayesian_custom_prior(self) -> None:
        """Passes prior parameters to BayesianConsensus."""
        algo = get_consensus_algorithm(
            ConsensusAlgorithm.BAYESIAN,
            prior_alpha=5.0,
            prior_beta=2.0,
        )
        assert isinstance(algo, BayesianConsensus)
        assert algo._prior_alpha == 5.0
        assert algo._prior_beta == 2.0

    def test_majority_voting_custom_tie_breaker(self) -> None:
        """Passes tie-breaker to MajorityVotingConsensus."""
        algo = get_consensus_algorithm(
            ConsensusAlgorithm.MAJORITY_VOTING,
            tie_breaker=TieBreaker.ESCALATE_TO_DEBATE,
        )
        assert isinstance(algo, MajorityVotingConsensus)
        assert algo._tie_breaker == TieBreaker.ESCALATE_TO_DEBATE

    def test_all_algorithms_have_resolve(self) -> None:
        """Every routed algorithm has a resolve method."""
        for algo_enum in ConsensusAlgorithm:
            algo = get_consensus_algorithm(algo_enum)
            assert hasattr(algo, "resolve")
            assert callable(algo.resolve)
