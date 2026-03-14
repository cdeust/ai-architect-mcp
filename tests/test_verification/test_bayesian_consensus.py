"""Tests for Bayesian consensus algorithm (ALG-011)."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ai_architect_mcp._models.consensus import (
    AgreementLevel,
    ConsensusAlgorithm,
    DisagreementResolution,
)
from ai_architect_mcp._models.verification import ClaimEvaluation, Verdict
from ai_architect_mcp._verification.algorithms.bayesian_consensus import (
    BayesianConsensus,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _make_evals(
    scores: list[float],
    confidences: list[float] | None = None,
) -> list[ClaimEvaluation]:
    """Create ClaimEvaluations from scores and confidences."""
    cid = uuid4()
    if confidences is None:
        confidences = [0.9] * len(scores)
    return [
        ClaimEvaluation(
            claim_id=cid,
            evaluator_id=f"e{i}",
            score=s,
            confidence=c,
            verdict=Verdict.PASS if s >= 0.5 else Verdict.FAIL,
            reasoning=f"Score: {s}",
        )
        for i, (s, c) in enumerate(zip(scores, confidences))
    ]


class TestBayesianConsensus:
    """Tests for BayesianConsensus.resolve."""

    def test_all_high_scores(self) -> None:
        """All high scores produce high agreement and high consensus."""
        evals = _make_evals([0.85, 0.90, 0.88, 0.82])
        result = BayesianConsensus().resolve(evals)
        assert result.algorithm == ConsensusAlgorithm.BAYESIAN
        assert result.agreement_level == AgreementLevel.HIGH
        assert result.consensus_score > 0.7
        assert result.converged is True

    def test_all_low_scores(self) -> None:
        """All low scores produce high agreement but low consensus."""
        evals = _make_evals([0.1, 0.15, 0.12, 0.08])
        result = BayesianConsensus().resolve(evals)
        assert result.agreement_level == AgreementLevel.HIGH
        assert result.consensus_score < 0.4

    def test_mixed_scores_low_agreement(self) -> None:
        """Widely spread scores produce low agreement."""
        evals = _make_evals([0.05, 0.95, 0.05, 0.95])
        result = BayesianConsensus().resolve(evals)
        assert result.agreement_level == AgreementLevel.LOW
        assert result.resolution == DisagreementResolution.RE_EVALUATE

    def test_custom_prior(self) -> None:
        """Strong prior shifts the consensus score."""
        evals = _make_evals([0.6, 0.65, 0.7])
        weak = BayesianConsensus(prior_alpha=1.0, prior_beta=1.0).resolve(evals)
        strong = BayesianConsensus(prior_alpha=10.0, prior_beta=1.0).resolve(evals)
        assert strong.consensus_score > weak.consensus_score

    def test_empty_raises(self) -> None:
        """Empty evaluations raise ValueError."""
        with pytest.raises(ValueError, match="zero evaluations"):
            BayesianConsensus().resolve([])

    def test_single_evaluation(self) -> None:
        """Single evaluation produces valid result."""
        evals = _make_evals([0.8])
        result = BayesianConsensus().resolve(evals)
        assert result.consensus_score > 0.5
        assert result.iteration_count == 1

    def test_invalid_prior_alpha(self) -> None:
        """Non-positive alpha raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            BayesianConsensus(prior_alpha=0.0)

    def test_invalid_prior_beta(self) -> None:
        """Non-positive beta raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            BayesianConsensus(prior_beta=-1.0)

    def test_posterior_mean_formula(self) -> None:
        """Verify posterior mean matches alpha'/(alpha'+beta')."""
        evals = _make_evals([0.8, 0.7, 0.6])
        result = BayesianConsensus(prior_alpha=1.0, prior_beta=1.0).resolve(evals)
        expected = (1.0 + 3) / (1.0 + 3 + 1.0 + 0)
        assert abs(result.consensus_score - expected) < 1e-4

    def test_confidence_bounded(self) -> None:
        """Confidence is always in [0, 1]."""
        evals = _make_evals([0.5, 0.5, 0.5, 0.5, 0.5])
        result = BayesianConsensus().resolve(evals)
        assert 0.0 <= result.consensus_confidence <= 1.0

    def test_fixture_round_trip(self) -> None:
        """Fixture data produces expected results."""
        fixture_path = FIXTURES_DIR / "consensus_bayesian.json"
        data = json.loads(fixture_path.read_text())
        evals = _make_evals(data["scores"], data["confidences"])
        result = BayesianConsensus(
            prior_alpha=data["prior_alpha"],
            prior_beta=data["prior_beta"],
        ).resolve(evals)
        assert abs(result.consensus_score - data["expected_consensus_score"]) < 1e-4
        assert result.agreement_level.value == data["expected_agreement"]

    def test_serialization_round_trip(self) -> None:
        """Result survives model_dump/model_validate."""
        evals = _make_evals([0.7, 0.8, 0.75])
        result = BayesianConsensus().resolve(evals)
        from ai_architect_mcp._models.consensus import ConsensusResult
        restored = ConsensusResult.model_validate(result.model_dump(mode="json"))
        assert restored.algorithm == ConsensusAlgorithm.BAYESIAN

    def test_resolution_accept_high_agreement(self) -> None:
        """High agreement produces ACCEPT resolution."""
        evals = _make_evals([0.85, 0.86, 0.87])
        result = BayesianConsensus().resolve(evals)
        assert result.resolution == DisagreementResolution.ACCEPT
