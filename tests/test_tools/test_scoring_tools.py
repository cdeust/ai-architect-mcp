"""Tests for scoring tools."""

from __future__ import annotations

import pytest


class TestScoringTools:
    @pytest.mark.asyncio
    async def test_compound_score(self) -> None:
        from ai_architect_mcp._tools.scoring_tools import ai_architect_compound_score

        result = await ai_architect_compound_score(
            relevance=0.8,
            uniqueness=0.7,
            impact=0.9,
            confidence=0.85,
        )
        assert "weighted_total" in result

    @pytest.mark.asyncio
    async def test_trace_propagation(self) -> None:
        from ai_architect_mcp._tools.scoring_tools import ai_architect_trace_propagation

        result = await ai_architect_trace_propagation(
            source_module="auth",
            dependency_graph={"auth": ["api", "db"], "api": ["frontend"], "db": [], "frontend": []},
            max_depth=3,
        )
        assert "source" in result
        assert result["source"] == "auth"
        assert "total_paths" in result
