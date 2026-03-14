"""Tests for structural dimension scorers (D1–D4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_architect_mcp._interview.models import DimensionType
from ai_architect_mcp._interview.scorers.header_format import score_header_format
from ai_architect_mcp._interview.scorers.id_consistency import score_id_consistency
from ai_architect_mcp._interview.scorers.outline_flow import score_outline_flow
from ai_architect_mcp._interview.scorers.sections_present import score_sections_present

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


class TestSectionsPresent:
    """D1 scorer tests."""

    def test_all_sections_present(self, complete_artifact: dict[str, Any]) -> None:
        result = score_sections_present(complete_artifact)
        assert result.dimension_type == DimensionType.D1_SECTIONS_PRESENT
        assert result.score == 1.0
        assert result.passed is True
        assert len(result.findings) == 0

    def test_missing_sections(self, partial_artifact: dict[str, Any]) -> None:
        result = score_sections_present(partial_artifact)
        assert result.score < 1.0
        assert result.passed is False
        assert len(result.findings) > 0

    def test_empty_content(self) -> None:
        result = score_sections_present({"content": ""})
        assert result.score == 0.0
        assert result.passed is False

    def test_no_content_key(self) -> None:
        result = score_sections_present({})
        assert result.score == 0.0
        assert result.passed is False


class TestHeaderFormat:
    """D2 scorer tests."""

    def test_valid_headers(self, complete_artifact: dict[str, Any]) -> None:
        result = score_header_format(complete_artifact)
        assert result.dimension_type == DimensionType.D2_HEADER_FORMAT
        assert result.score >= 0.8
        assert result.passed is True

    def test_malformed_headers(self) -> None:
        artifact = {"content": "### bad header\n#### also bad\n## Good Header\n"}
        result = score_header_format(artifact)
        assert result.score < 1.0

    def test_no_headers(self) -> None:
        result = score_header_format({"content": "Just plain text"})
        assert result.score == 1.0
        assert result.passed is True

    def test_score_clamped_to_zero(self) -> None:
        content = "\n".join([f"### Bad Header {i}" for i in range(20)])
        result = score_header_format({"content": content})
        assert result.score == 0.0


class TestIdConsistency:
    """D3 scorer tests."""

    def test_consistent_ids(self, complete_artifact: dict[str, Any]) -> None:
        result = score_id_consistency(complete_artifact)
        assert result.dimension_type == DimensionType.D3_ID_CONSISTENCY
        assert result.passed is True

    def test_duplicate_ids(self) -> None:
        artifact = {"content": "FR-001: first\nFR-001: duplicate\nFR-002: second"}
        result = score_id_consistency(artifact)
        assert result.score < 1.0
        assert any("Duplicate" in f for f in result.findings)

    def test_no_ids(self) -> None:
        result = score_id_consistency({"content": "No identifiers here"})
        assert result.score == 0.0
        assert result.passed is False

    def test_non_sequential_ids(self) -> None:
        artifact = {"content": "FR-001: first\nFR-003: third"}
        result = score_id_consistency(artifact)
        assert any("Non-sequential" in f for f in result.findings)


class TestOutlineFlow:
    """D4 scorer tests."""

    def test_correct_order(self, complete_artifact: dict[str, Any]) -> None:
        result = score_outline_flow(complete_artifact)
        assert result.dimension_type == DimensionType.D4_OUTLINE_FLOW
        assert result.passed is True
        assert result.score == 1.0

    def test_wrong_order(self) -> None:
        content = "## Testing\ntest\n## Overview\noverview\n## Requirements\nreqs"
        result = score_outline_flow({"content": content})
        assert result.score < 1.0

    def test_no_sections(self) -> None:
        result = score_outline_flow({"content": "Just text"})
        assert result.score == 0.0
        assert result.passed is False

    def test_partial_sections_in_order(self) -> None:
        content = "## Overview\noverview\n## Requirements\nreqs\n## Testing\ntests"
        result = score_outline_flow({"content": content})
        assert result.score == 1.0
        assert result.passed is True
