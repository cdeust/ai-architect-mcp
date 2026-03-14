"""Tests for Plan Interview gate logic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_architect_mcp._interview.gate import (
    ADVISORY_DIMENSIONS,
    CRITICAL_DIMENSIONS,
    evaluate_gate,
    run_full_interview,
)
from ai_architect_mcp._interview.models import (
    DimensionScore,
    DimensionType,
    GateDecision,
    InterviewConfig,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _make_score(
    dim: DimensionType,
    score: float,
    passed: bool,
) -> DimensionScore:
    """Helper to create a DimensionScore."""
    return DimensionScore(
        dimension_type=dim,
        dimension_name=dim.value,
        score=score,
        passed=passed,
    )


@pytest.fixture
def complete_artifact() -> dict[str, Any]:
    with open(FIXTURES / "interview_prd_complete.json") as f:
        return json.load(f)


@pytest.fixture
def partial_artifact() -> dict[str, Any]:
    with open(FIXTURES / "interview_prd_partial.json") as f:
        return json.load(f)


class TestEvaluateGate:
    """Tests for the evaluate_gate function."""

    def test_all_pass_returns_approved(self) -> None:
        scores = [
            _make_score(dim, 0.9, True) for dim in DimensionType
        ]
        assert evaluate_gate(scores) == GateDecision.APPROVED

    def test_critical_fail_returns_rejected(self) -> None:
        scores = [
            _make_score(dim, 0.9, True) for dim in DimensionType
        ]
        scores[0] = _make_score(DimensionType.D1_SECTIONS_PRESENT, 0.5, False)
        assert evaluate_gate(scores) == GateDecision.REJECTED

    def test_advisory_fail_returns_provisional(self) -> None:
        scores = []
        for dim in DimensionType:
            if dim in ADVISORY_DIMENSIONS:
                scores.append(_make_score(dim, 0.4, False))
            else:
                scores.append(_make_score(dim, 0.9, True))
        assert evaluate_gate(scores) == GateDecision.PROVISIONAL

    def test_custom_thresholds(self) -> None:
        config = InterviewConfig(critical_threshold=0.9, advisory_threshold=0.8)
        scores = [
            _make_score(dim, 0.85, True) for dim in DimensionType
        ]
        assert evaluate_gate(scores, config) == GateDecision.REJECTED

    def test_critical_dimensions_count(self) -> None:
        assert len(CRITICAL_DIMENSIONS) == 7

    def test_advisory_dimensions_count(self) -> None:
        assert len(ADVISORY_DIMENSIONS) == 3

    def test_no_overlap_between_critical_and_advisory(self) -> None:
        assert CRITICAL_DIMENSIONS.isdisjoint(ADVISORY_DIMENSIONS)

    def test_all_dimensions_classified(self) -> None:
        all_classified = CRITICAL_DIMENSIONS | ADVISORY_DIMENSIONS
        assert all_classified == set(DimensionType)


class TestRunFullInterview:
    """Tests for the run_full_interview function."""

    def test_complete_prd_approved(self, complete_artifact: dict[str, Any]) -> None:
        result = run_full_interview(complete_artifact, finding_id="TEST-FULL")
        assert result.finding_id == "TEST-FULL"
        assert result.stage_id == 45
        assert len(result.dimension_scores) == 10
        assert result.gate_decision == GateDecision.APPROVED

    def test_partial_prd_rejected(self, partial_artifact: dict[str, Any]) -> None:
        result = run_full_interview(partial_artifact, finding_id="TEST-PARTIAL")
        assert result.gate_decision == GateDecision.REJECTED

    def test_auto_generated_finding_id(self, complete_artifact: dict[str, Any]) -> None:
        result = run_full_interview(complete_artifact)
        assert result.finding_id.startswith("INTERVIEW-")

    def test_result_serialization(self, complete_artifact: dict[str, Any]) -> None:
        result = run_full_interview(complete_artifact, finding_id="TEST-SER")
        data = result.model_dump(mode="json")
        assert "dimension_scores" in data
        assert "gate_decision" in data
        assert data["stage_id"] == 45
