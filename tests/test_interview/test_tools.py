"""Tests for Plan Interview MCP tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_architect_mcp._tools.interview_tools import (
    _result_cache,
    ai_architect_query_interview_results,
    ai_architect_run_interview_gate,
    ai_architect_score_dimension,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def complete_artifact() -> dict[str, Any]:
    with open(FIXTURES / "interview_prd_complete.json") as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Clear the result cache before each test."""
    _result_cache.clear()


@pytest.mark.asyncio
class TestScoreDimensionTool:
    """Tests for ai_architect_score_dimension."""

    async def test_valid_dimension(self, complete_artifact: dict[str, Any]) -> None:
        result = await ai_architect_score_dimension(
            dimension="D1_SECTIONS_PRESENT",
            artifact=complete_artifact,
        )
        assert result["dimension_type"] == "D1_SECTIONS_PRESENT"
        assert "score" in result

    async def test_invalid_dimension(self, complete_artifact: dict[str, Any]) -> None:
        with pytest.raises(ValueError, match="Invalid dimension"):
            await ai_architect_score_dimension(
                dimension="INVALID",
                artifact=complete_artifact,
            )


@pytest.mark.asyncio
class TestRunInterviewGateTool:
    """Tests for ai_architect_run_interview_gate."""

    async def test_full_gate(self, complete_artifact: dict[str, Any]) -> None:
        result = await ai_architect_run_interview_gate(
            artifact=complete_artifact,
            finding_id="TOOL-TEST-001",
        )
        assert result["finding_id"] == "TOOL-TEST-001"
        assert result["gate_decision"] == "APPROVED"
        assert len(result["dimension_scores"]) == 10

    async def test_caches_result(self, complete_artifact: dict[str, Any]) -> None:
        await ai_architect_run_interview_gate(
            artifact=complete_artifact,
            finding_id="CACHE-TEST",
        )
        assert "CACHE-TEST" in _result_cache


@pytest.mark.asyncio
class TestQueryInterviewResultsTool:
    """Tests for ai_architect_query_interview_results."""

    async def test_missing_result(self) -> None:
        result = await ai_architect_query_interview_results(finding_id="NONEXISTENT")
        assert result["found"] is False

    async def test_found_result(self, complete_artifact: dict[str, Any]) -> None:
        await ai_architect_run_interview_gate(
            artifact=complete_artifact,
            finding_id="QUERY-TEST",
        )
        result = await ai_architect_query_interview_results(finding_id="QUERY-TEST")
        assert result["found"] is True
        assert result["gate_decision"] == "APPROVED"

    async def test_min_score_filter(self, complete_artifact: dict[str, Any]) -> None:
        await ai_architect_run_interview_gate(
            artifact=complete_artifact,
            finding_id="FILTER-TEST",
        )
        result = await ai_architect_query_interview_results(
            finding_id="FILTER-TEST",
            min_score=0.99,
        )
        assert result["found"] is True
        # Only dimensions scoring >= 0.99 should remain
        for score in result["dimension_scores"]:
            assert score["score"] >= 0.99
