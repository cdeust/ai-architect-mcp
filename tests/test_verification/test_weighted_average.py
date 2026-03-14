"""Tests for weighted average consensus."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai_architect_mcp._models.consensus import (
    AgreementLevel,
    ConsensusAlgorithm,
    DisagreementResolution,
)
from ai_architect_mcp._models.verification import ClaimEvaluation, Verdict
from ai_architect_mcp._verification.algorithms.weighted_average import (
    WeightedAverageConsensus,
)


class TestWeightedAverageConsensus:
    """Tests for WeightedAverageConsensus.resolve."""

    def test_high_agreement(self) -> None:
        """Closely grouped scores produce HIGH agreement."""
        evals = [
            ClaimEvaluation(
                claim_id=uuid4(),
                evaluator_id=f"e{i}",
                score=0.85 + i * 0.01,
                confidence=0.9,
                verdict=Verdict.PASS,
                reasoning="test",
            )
            for i in range(3)
        ]
        result = WeightedAverageConsensus().resolve(evals)
        assert result.algorithm == ConsensusAlgorithm.WEIGHTED_AVERAGE
        assert result.agreement_level == AgreementLevel.HIGH
        assert result.converged is True

    def test_low_agreement(self) -> None:
        """Widely spread scores produce LOW agreement."""
        cid = uuid4()
        evals = [
            ClaimEvaluation(
                claim_id=cid,
                evaluator_id="e1",
                score=0.1,
                confidence=0.9,
                verdict=Verdict.FAIL,
                reasoning="t",
            ),
            ClaimEvaluation(
                claim_id=cid,
                evaluator_id="e2",
                score=0.95,
                confidence=0.9,
                verdict=Verdict.PASS,
                reasoning="t",
            ),
        ]
        result = WeightedAverageConsensus().resolve(evals)
        assert result.agreement_level == AgreementLevel.LOW

    def test_empty_raises(self) -> None:
        """Empty evaluations raise ValueError."""
        with pytest.raises(ValueError, match="zero evaluations"):
            WeightedAverageConsensus().resolve([])

    def test_resolution_is_valid(self) -> None:
        """Resolution is always a valid DisagreementResolution."""
        cid = uuid4()
        evals = [
            ClaimEvaluation(
                claim_id=cid,
                evaluator_id="e1",
                score=0.1,
                confidence=0.9,
                verdict=Verdict.FAIL,
                reasoning="t",
            ),
            ClaimEvaluation(
                claim_id=cid,
                evaluator_id="e2",
                score=0.8,
                confidence=0.9,
                verdict=Verdict.PASS,
                reasoning="t",
            ),
        ]
        result = WeightedAverageConsensus().resolve(evals)
        assert result.resolution in (
            DisagreementResolution.REJECT,
            DisagreementResolution.FLAG_FOR_REVIEW,
            DisagreementResolution.ACCEPT,
        )
