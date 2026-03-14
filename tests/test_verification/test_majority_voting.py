"""Tests for Majority Voting consensus algorithm (ALG-012)."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ai_architect_mcp._models.consensus import (
    AgreementLevel,
    ConsensusAlgorithm,
    DisagreementResolution,
    TieBreaker,
)
from ai_architect_mcp._models.verification import ClaimEvaluation, Verdict
from ai_architect_mcp._verification.algorithms.majority_voting import (
    MajorityVotingConsensus,
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


class TestMajorityVotingConsensus:
    """Tests for MajorityVotingConsensus.resolve."""

    def test_clear_majority_yes(self) -> None:
        """Clear YES majority produces ACCEPT."""
        evals = _make_evals([0.8, 0.7, 0.6, 0.9, 0.75])
        result = MajorityVotingConsensus().resolve(evals)
        assert result.algorithm == ConsensusAlgorithm.MAJORITY_VOTING
        assert result.consensus_score == 1.0
        assert result.converged is True

    def test_clear_majority_no(self) -> None:
        """Clear NO majority produces REJECT."""
        evals = _make_evals([0.1, 0.2, 0.15, 0.3, 0.05])
        result = MajorityVotingConsensus().resolve(evals)
        assert result.consensus_score == 1.0
        assert result.resolution in (
            DisagreementResolution.REJECT,
            DisagreementResolution.ACCEPT,
        )

    def test_narrow_majority(self) -> None:
        """3 YES vs 2 NO produces narrow margin."""
        evals = _make_evals([0.8, 0.7, 0.6, 0.3, 0.2])
        result = MajorityVotingConsensus().resolve(evals)
        assert result.consensus_score == 0.6
        assert result.consensus_confidence == pytest.approx(0.2)

    def test_empty_raises(self) -> None:
        """Empty evaluations raise ValueError."""
        with pytest.raises(ValueError, match="zero evaluations"):
            MajorityVotingConsensus().resolve([])

    def test_single_evaluation_yes(self) -> None:
        """Single YES vote produces accept."""
        evals = _make_evals([0.8])
        result = MajorityVotingConsensus().resolve(evals)
        assert result.consensus_score == 1.0

    def test_single_evaluation_no(self) -> None:
        """Single NO vote produces reject."""
        evals = _make_evals([0.3])
        result = MajorityVotingConsensus().resolve(evals)
        assert result.consensus_score == 1.0

    def test_tie_highest_confidence(self) -> None:
        """Tie broken by highest confidence."""
        evals = _make_evals(
            scores=[0.8, 0.3],
            confidences=[0.95, 0.5],
        )
        result = MajorityVotingConsensus(
            tie_breaker=TieBreaker.HIGHEST_CONFIDENCE
        ).resolve(evals)
        assert result.consensus_score == 0.5

    def test_tie_random_seeded_deterministic(self) -> None:
        """Seeded random tie-breaking is deterministic."""
        evals = _make_evals(
            scores=[0.8, 0.3],
            confidences=[0.9, 0.9],
        )
        results = [
            MajorityVotingConsensus(
                tie_breaker=TieBreaker.RANDOM_SEEDED
            ).resolve(evals)
            for _ in range(5)
        ]
        first = results[0].consensus_score
        assert all(r.consensus_score == first for r in results)

    def test_tie_escalate_to_debate(self) -> None:
        """Escalate tie produces RE_EVALUATE and not converged."""
        evals = _make_evals(
            scores=[0.8, 0.3],
            confidences=[0.9, 0.9],
        )
        result = MajorityVotingConsensus(
            tie_breaker=TieBreaker.ESCALATE_TO_DEBATE
        ).resolve(evals)
        assert result.resolution == DisagreementResolution.RE_EVALUATE
        assert result.converged is False

    def test_custom_voting_threshold(self) -> None:
        """Custom threshold changes vote classification."""
        evals = _make_evals([0.6, 0.65, 0.7])
        strict = MajorityVotingConsensus(voting_threshold=0.8).resolve(evals)
        lenient = MajorityVotingConsensus(voting_threshold=0.5).resolve(evals)
        assert strict.resolution != lenient.resolution

    def test_invalid_voting_threshold(self) -> None:
        """Invalid threshold raises ValueError."""
        with pytest.raises(ValueError, match="voting_threshold"):
            MajorityVotingConsensus(voting_threshold=0.0)

    def test_invalid_acceptance_ratio(self) -> None:
        """Invalid acceptance ratio raises ValueError."""
        with pytest.raises(ValueError, match="acceptance_ratio"):
            MajorityVotingConsensus(acceptance_ratio=0.0)

    def test_fixture_round_trip(self) -> None:
        """Fixture data produces expected results."""
        fixture_path = FIXTURES_DIR / "consensus_majority_voting.json"
        data = json.loads(fixture_path.read_text())
        evals = _make_evals(data["scores"], data["confidences"])
        result = MajorityVotingConsensus(
            voting_threshold=data["voting_threshold"],
        ).resolve(evals)
        assert abs(result.consensus_score - data["expected_consensus_score"]) < 1e-4
        assert result.agreement_level.value == data["expected_agreement"]

    def test_serialization_round_trip(self) -> None:
        """Result survives model_dump/model_validate."""
        evals = _make_evals([0.7, 0.8, 0.3])
        result = MajorityVotingConsensus().resolve(evals)
        from ai_architect_mcp._models.consensus import ConsensusResult
        restored = ConsensusResult.model_validate(result.model_dump(mode="json"))
        assert restored.algorithm == ConsensusAlgorithm.MAJORITY_VOTING

    def test_agreement_high_unanimous(self) -> None:
        """Unanimous vote produces HIGH agreement."""
        evals = _make_evals([0.8, 0.9, 0.7, 0.85, 0.95])
        result = MajorityVotingConsensus().resolve(evals)
        assert result.agreement_level == AgreementLevel.HIGH
