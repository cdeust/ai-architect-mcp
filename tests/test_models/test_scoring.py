"""Tests for scoring models — weight normalization, score ranges."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._models.scoring import (
    CompoundScore,
    ImpactReport,
    PropagationPath,
    Recommendation,
    RiskLevel,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestCompoundScore:
    """Test CompoundScore model."""

    def test_valid_score(self) -> None:
        score = CompoundScore(
            relevance=0.8,
            uniqueness=0.6,
            impact=0.9,
            confidence=0.7,
            weighted_total=0.78,
            weights={"relevance": 0.3, "uniqueness": 0.2, "impact": 0.3, "confidence": 0.2},
        )
        assert score.weighted_total == 0.78

    def test_weights_not_summing_to_one_rejected(self) -> None:
        with pytest.raises(ValueError, match="sum to 1.0"):
            CompoundScore(
                relevance=0.5,
                uniqueness=0.5,
                impact=0.5,
                confidence=0.5,
                weighted_total=0.5,
                weights={"relevance": 0.5, "uniqueness": 0.5, "impact": 0.3, "confidence": 0.2},
            )

    def test_score_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError):
            CompoundScore(
                relevance=1.5,
                uniqueness=0.5,
                impact=0.5,
                confidence=0.5,
                weighted_total=0.5,
                weights={"relevance": 0.25, "uniqueness": 0.25, "impact": 0.25, "confidence": 0.25},
            )

    def test_serialization_round_trip(self) -> None:
        score = CompoundScore(
            relevance=0.8,
            uniqueness=0.6,
            impact=0.9,
            confidence=0.7,
            weighted_total=0.78,
            weights={"relevance": 0.3, "uniqueness": 0.2, "impact": 0.3, "confidence": 0.2},
        )
        dumped = score.model_dump(mode="json")
        restored = CompoundScore.model_validate(dumped)
        assert restored.weighted_total == score.weighted_total

    def test_fixture(self) -> None:
        fixture_path = FIXTURES_DIR / "compound_score_basic.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            score = CompoundScore.model_validate(data)
            assert score.weighted_total >= 0.0


class TestPropagationPath:
    """Test PropagationPath model."""

    def test_valid_path(self) -> None:
        path = PropagationPath(
            source_module="auth",
            target_modules=["api", "web"],
            propagation_type="direct",
            depth=2,
        )
        assert path.depth == 2

    def test_depth_below_one_rejected(self) -> None:
        with pytest.raises(ValueError):
            PropagationPath(
                source_module="auth",
                target_modules=["api"],
                propagation_type="direct",
                depth=0,
            )


class TestImpactReport:
    """Test ImpactReport model."""

    def test_valid_report(self) -> None:
        report = ImpactReport(
            finding_id="FIND-001",
            compound_score=CompoundScore(
                relevance=0.8, uniqueness=0.6, impact=0.9, confidence=0.7,
                weighted_total=0.78,
                weights={"relevance": 0.3, "uniqueness": 0.2, "impact": 0.3, "confidence": 0.2},
            ),
            risk_level=RiskLevel.HIGH,
            recommendation=Recommendation.REVIEW,
        )
        assert report.risk_level == RiskLevel.HIGH
