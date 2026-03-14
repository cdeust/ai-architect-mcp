"""Tests for adaptive stability consensus."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai_architect_mcp._models.consensus import ConsensusAlgorithm
from ai_architect_mcp._models.verification import ClaimEvaluation, Verdict
from ai_architect_mcp._verification.algorithms.adaptive_stability import (
    AdaptiveStabilityConsensus,
)


class TestAdaptiveStability:
    """Tests for AdaptiveStabilityConsensus.resolve."""

    def test_stable_input_converges(self) -> None:
        """Identical scores with enough samples converge."""
        evals = [
            ClaimEvaluation(
                claim_id=uuid4(),
                evaluator_id=f"e{i}",
                score=0.85,
                confidence=0.9,
                verdict=Verdict.PASS,
                reasoning="t",
            )
            for i in range(5)
        ]
        result = AdaptiveStabilityConsensus().resolve(evals)
        assert result.algorithm == ConsensusAlgorithm.ADAPTIVE_STABILITY
        assert result.converged is True

    def test_oscillating_input(self) -> None:
        """Highly variable scores do not converge."""
        cid = uuid4()
        scores = [0.2, 0.9, 0.1, 0.95, 0.15]
        evals = [
            ClaimEvaluation(
                claim_id=cid,
                evaluator_id=f"e{i}",
                score=s,
                confidence=0.8,
                verdict=Verdict.PASS,
                reasoning="t",
            )
            for i, s in enumerate(scores)
        ]
        result = AdaptiveStabilityConsensus().resolve(evals)
        assert result.converged is False

    def test_empty_raises(self) -> None:
        """Empty evaluations raise ValueError."""
        with pytest.raises(ValueError, match="zero evaluations"):
            AdaptiveStabilityConsensus().resolve([])
