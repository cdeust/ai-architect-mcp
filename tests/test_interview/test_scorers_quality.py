"""Tests for quality dimension scorers (D5–D10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_architect_mcp._interview.models import DimensionType
from ai_architect_mcp._interview.scorers.artifact_coherence import score_artifact_coherence
from ai_architect_mcp._interview.scorers.assumption_validation import score_assumption_validation
from ai_architect_mcp._interview.scorers.clarity_level import score_clarity_level
from ai_architect_mcp._interview.scorers.requirement_precision import score_requirement_precision
from ai_architect_mcp._interview.scorers.stakeholder_alignment import score_stakeholder_alignment
from ai_architect_mcp._interview.scorers.success_metrics import score_success_metrics

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def complete_artifact() -> dict[str, Any]:
    """Load the complete PRD fixture."""
    with open(FIXTURES / "interview_prd_complete.json") as f:
        return json.load(f)


@pytest.fixture
def partial_artifact() -> dict[str, Any]:
    """Load the partial PRD fixture."""
    with open(FIXTURES / "interview_prd_partial.json") as f:
        return json.load(f)


class TestArtifactCoherence:
    """D5 scorer tests."""

    def test_coherent_artifact(self, complete_artifact: dict[str, Any]) -> None:
        result = score_artifact_coherence(complete_artifact)
        assert result.dimension_type == DimensionType.D5_ARTIFACT_COHERENCE

    def test_single_section(self) -> None:
        result = score_artifact_coherence({"content": "## Overview\nJust one section."})
        assert result.score == 1.0
        assert result.passed is True

    def test_empty_content(self) -> None:
        result = score_artifact_coherence({"content": ""})
        assert result.score == 1.0

    def test_no_multi_word_terms(self) -> None:
        content = "## Overview\njust lowercase.\n## Requirements\nalso lowercase."
        result = score_artifact_coherence({"content": content})
        assert result.score == 1.0


class TestClarityLevel:
    """D6 scorer tests."""

    def test_clear_language(self, complete_artifact: dict[str, Any]) -> None:
        result = score_clarity_level(complete_artifact)
        assert result.dimension_type == DimensionType.D6_CLARITY_LEVEL
        assert result.passed is True

    def test_vague_language(self, partial_artifact: dict[str, Any]) -> None:
        result = score_clarity_level(partial_artifact)
        assert result.score < 1.0
        assert len(result.findings) > 0

    def test_heavily_vague(self) -> None:
        content = "various things and several items. some stuff etc and so on. TBD"
        result = score_clarity_level({"content": content})
        assert result.score < 0.8
        assert result.passed is False

    def test_no_vague_words(self) -> None:
        result = score_clarity_level({"content": "Precise specification with exact values."})
        assert result.score == 1.0
        assert result.passed is True


class TestStakeholderAlignment:
    """D7 scorer tests."""

    def test_stories_with_stakeholders(self, complete_artifact: dict[str, Any]) -> None:
        result = score_stakeholder_alignment(complete_artifact)
        assert result.dimension_type == DimensionType.D7_STAKEHOLDER_ALIGNMENT
        assert result.passed is True

    def test_stories_without_stakeholders(self, partial_artifact: dict[str, Any]) -> None:
        result = score_stakeholder_alignment(partial_artifact)
        assert result.score < 1.0

    def test_no_stories(self) -> None:
        result = score_stakeholder_alignment({"content": "## Overview\nNo stories."})
        assert result.score == 1.0
        assert result.passed is True

    def test_mixed_stories(self) -> None:
        content = (
            "STORY-001: As a user, I want to log in.\n"
            "STORY-002: The system should work.\n"
        )
        result = score_stakeholder_alignment({"content": content})
        assert result.score == 0.5


class TestRequirementPrecision:
    """D8 scorer tests."""

    def test_precise_requirements(self, complete_artifact: dict[str, Any]) -> None:
        result = score_requirement_precision(complete_artifact)
        assert result.dimension_type == DimensionType.D8_REQUIREMENT_PRECISION
        assert result.passed is True

    def test_imprecise_requirements(self) -> None:
        content = "FR-001: The system should be user-friendly\nFR-002: The system should be reliable"
        result = score_requirement_precision({"content": content})
        assert result.passed is False

    def test_no_requirements(self) -> None:
        result = score_requirement_precision({"content": "No requirements here."})
        assert result.score == 0.0
        assert result.passed is False

    def test_mixed_precision(self) -> None:
        content = "FR-001: Must handle 1000 requests per second\nFR-002: Should be fast"
        result = score_requirement_precision({"content": content})
        assert result.score == 0.5


class TestAssumptionValidation:
    """D9 scorer tests."""

    def test_sufficient_assumptions(self, complete_artifact: dict[str, Any]) -> None:
        result = score_assumption_validation(complete_artifact)
        assert result.dimension_type == DimensionType.D9_ASSUMPTION_VALIDATION
        assert result.score == 1.0
        assert result.passed is True

    def test_no_assumptions_section(self, partial_artifact: dict[str, Any]) -> None:
        result = score_assumption_validation(partial_artifact)
        assert result.score == 0.0
        assert result.passed is False

    def test_few_assumptions(self) -> None:
        content = "## Assumptions\n- Users have internet\n"
        result = score_assumption_validation({"content": content})
        assert result.score == 0.5

    def test_empty_assumptions_section(self) -> None:
        content = "## Assumptions\n\n## Next Section\n"
        result = score_assumption_validation({"content": content})
        assert result.score == 0.0


class TestSuccessMetrics:
    """D10 scorer tests."""

    def test_quantitative_metrics(self, complete_artifact: dict[str, Any]) -> None:
        result = score_success_metrics(complete_artifact)
        assert result.dimension_type == DimensionType.D10_SUCCESS_METRICS
        assert result.passed is True

    def test_no_metrics_section(self, partial_artifact: dict[str, Any]) -> None:
        result = score_success_metrics(partial_artifact)
        assert result.score == 0.0
        assert result.passed is False

    def test_qualitative_metrics(self) -> None:
        content = "## Metrics\n- System should be fast\n- Users should be happy\n"
        result = score_success_metrics({"content": content})
        assert result.score == 0.0
        assert result.passed is False

    def test_mixed_metrics(self) -> None:
        content = "## Metrics\n- Uptime of 99.9%\n- Users should be satisfied\n"
        result = score_success_metrics({"content": content})
        assert result.score == 0.5
