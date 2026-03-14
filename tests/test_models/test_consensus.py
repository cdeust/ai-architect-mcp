"""Tests for consensus models — agreement level thresholds, resolution logic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._models.consensus import (
    AGREEMENT_HIGH_THRESHOLD,
    AGREEMENT_MEDIUM_THRESHOLD,
    AgreementLevel,
    ConsensusAlgorithm,
    ConsensusResult,
    DisagreementResolution,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestAgreementLevel:
    """Test AgreementLevel enum."""

    def test_all_levels_present(self) -> None:
        assert len(AgreementLevel) == 3

    def test_thresholds(self) -> None:
        assert AGREEMENT_HIGH_THRESHOLD == 0.05
        assert AGREEMENT_MEDIUM_THRESHOLD == 0.15


class TestConsensusAlgorithm:
    """Test ConsensusAlgorithm enum."""

    def test_implemented_algorithms(self) -> None:
        assert ConsensusAlgorithm.WEIGHTED_AVERAGE.value == "weighted_average"
        assert ConsensusAlgorithm.ADAPTIVE_STABILITY.value == "adaptive_stability"

    def test_bayesian_and_majority_voting(self) -> None:
        assert ConsensusAlgorithm.BAYESIAN.value == "bayesian"
        assert ConsensusAlgorithm.MAJORITY_VOTING.value == "majority_voting"

    def test_total_count(self) -> None:
        assert len(ConsensusAlgorithm) == 4


class TestConsensusResult:
    """Test ConsensusResult model."""

    def test_valid_result(self) -> None:
        result = ConsensusResult(
            algorithm=ConsensusAlgorithm.WEIGHTED_AVERAGE,
            consensus_score=0.85,
            consensus_confidence=0.92,
            agreement_level=AgreementLevel.HIGH,
            resolution=DisagreementResolution.ACCEPT,
            individual_scores=[0.83, 0.86, 0.87],
            iteration_count=1,
            converged=True,
        )
        assert result.consensus_score == 0.85
        assert result.converged is True

    def test_score_out_of_range(self) -> None:
        with pytest.raises(ValueError):
            ConsensusResult(
                algorithm=ConsensusAlgorithm.WEIGHTED_AVERAGE,
                consensus_score=1.5,
                consensus_confidence=0.5,
                agreement_level=AgreementLevel.HIGH,
                resolution=DisagreementResolution.ACCEPT,
                individual_scores=[0.5],
                iteration_count=1,
                converged=True,
            )

    def test_serialization_round_trip(self) -> None:
        result = ConsensusResult(
            algorithm=ConsensusAlgorithm.ADAPTIVE_STABILITY,
            consensus_score=0.72,
            consensus_confidence=0.88,
            agreement_level=AgreementLevel.MEDIUM,
            resolution=DisagreementResolution.FLAG_FOR_REVIEW,
            individual_scores=[0.65, 0.78, 0.73],
            iteration_count=3,
            converged=True,
        )
        dumped = result.model_dump(mode="json")
        restored = ConsensusResult.model_validate(dumped)
        assert restored.algorithm == result.algorithm

    def test_fixture(self) -> None:
        fixture_path = FIXTURES_DIR / "consensus_high_agreement.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            result = ConsensusResult.model_validate(data)
            assert result.converged is not None
