"""Tests for Plan Interview data models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ai_architect_mcp._interview.models import (
    DimensionScore,
    DimensionType,
    GateDecision,
    InterviewConfig,
    InterviewResult,
)


class TestDimensionType:
    """Tests for the DimensionType enum."""

    def test_has_ten_members(self) -> None:
        assert len(DimensionType) == 10

    def test_all_prefixed_with_d(self) -> None:
        for member in DimensionType:
            assert member.value.startswith("D")

    def test_specific_values(self) -> None:
        assert DimensionType.D1_SECTIONS_PRESENT == "D1_SECTIONS_PRESENT"
        assert DimensionType.D10_SUCCESS_METRICS == "D10_SUCCESS_METRICS"


class TestGateDecision:
    """Tests for the GateDecision enum."""

    def test_has_three_members(self) -> None:
        assert len(GateDecision) == 3

    def test_values(self) -> None:
        assert GateDecision.APPROVED == "APPROVED"
        assert GateDecision.PROVISIONAL == "PROVISIONAL"
        assert GateDecision.REJECTED == "REJECTED"


class TestDimensionScore:
    """Tests for the DimensionScore model."""

    def test_valid_creation(self) -> None:
        score = DimensionScore(
            dimension_type=DimensionType.D1_SECTIONS_PRESENT,
            dimension_name="Sections Present",
            score=0.85,
            passed=True,
            findings=[],
        )
        assert score.score == 0.85
        assert score.passed is True

    def test_score_bounds(self) -> None:
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            DimensionScore(
                dimension_type=DimensionType.D1_SECTIONS_PRESENT,
                dimension_name="Test",
                score=-0.1,
                passed=False,
            )

    def test_score_upper_bound(self) -> None:
        with pytest.raises(ValueError, match="less than or equal to 1"):
            DimensionScore(
                dimension_type=DimensionType.D1_SECTIONS_PRESENT,
                dimension_name="Test",
                score=1.1,
                passed=False,
            )

    def test_serialization(self) -> None:
        score = DimensionScore(
            dimension_type=DimensionType.D2_HEADER_FORMAT,
            dimension_name="Header Format",
            score=1.0,
            passed=True,
            findings=["All headers valid"],
        )
        data = score.model_dump(mode="json")
        assert data["dimension_type"] == "D2_HEADER_FORMAT"
        assert data["findings"] == ["All headers valid"]


class TestInterviewConfig:
    """Tests for the InterviewConfig model."""

    def test_defaults(self) -> None:
        config = InterviewConfig()
        assert config.critical_threshold == 0.8
        assert config.advisory_threshold == 0.6
        assert config.timeout_seconds == 60

    def test_custom_values(self) -> None:
        config = InterviewConfig(critical_threshold=0.9, advisory_threshold=0.7)
        assert config.critical_threshold == 0.9
        assert config.advisory_threshold == 0.7


class TestInterviewResult:
    """Tests for the InterviewResult model."""

    def test_valid_creation(self) -> None:
        score = DimensionScore(
            dimension_type=DimensionType.D1_SECTIONS_PRESENT,
            dimension_name="Sections Present",
            score=1.0,
            passed=True,
        )
        result = InterviewResult(
            finding_id="TEST-001",
            dimension_scores=[score],
            gate_decision=GateDecision.APPROVED,
        )
        assert result.stage_id == 45
        assert result.finding_id == "TEST-001"
        assert isinstance(result.created_at, datetime)

    def test_empty_scores_rejected(self) -> None:
        with pytest.raises(ValueError, match="dimension_scores must not be empty"):
            InterviewResult(
                finding_id="TEST-002",
                dimension_scores=[],
                gate_decision=GateDecision.APPROVED,
            )

    def test_created_at_utc(self) -> None:
        score = DimensionScore(
            dimension_type=DimensionType.D1_SECTIONS_PRESENT,
            dimension_name="Test",
            score=0.5,
            passed=False,
        )
        result = InterviewResult(
            finding_id="TEST-003",
            dimension_scores=[score],
            gate_decision=GateDecision.REJECTED,
        )
        assert result.created_at.tzinfo is not None
