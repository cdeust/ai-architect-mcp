"""Tests for HOR tools."""

from __future__ import annotations

import pytest


class TestHORTools:
    @pytest.mark.asyncio
    async def test_run_hor_rules(self) -> None:
        from ai_architect_mcp._tools.hor_tools import ai_architect_run_hor_rules

        result = await ai_architect_run_hor_rules(artifact={"sections": []})
        assert "total_rules" in result
        assert "adjusted_score" in result

    @pytest.mark.asyncio
    async def test_run_hor_category(self) -> None:
        from ai_architect_mcp._tools.hor_tools import ai_architect_run_hor_category

        result = await ai_architect_run_hor_category(category="structural", artifact={"sections": []})
        assert "category" in result
        assert result["category"] == "structural"

    @pytest.mark.asyncio
    async def test_run_hor_single(self) -> None:
        from ai_architect_mcp._tools.hor_tools import ai_architect_run_hor_single

        result = await ai_architect_run_hor_single(rule_id=1, artifact={"sections": []})
        assert "passed" in result
