"""Tests for prompting tools."""

from __future__ import annotations

import pytest


class TestPromptingTools:
    @pytest.mark.asyncio
    async def test_select_strategy(self) -> None:
        from ai_architect_mcp._tools.prompting_tools import ai_architect_select_strategy

        result = await ai_architect_select_strategy(
            project_type="api",
            complexity="medium",
            characteristics=["mathematical_reasoning"],
        )
        assert "selected" in result
        assert "score" in result

    @pytest.mark.asyncio
    async def test_fuse_confidence(self) -> None:
        from ai_architect_mcp._tools.prompting_tools import ai_architect_fuse_confidence

        estimates = [
            {"source": "thought_buffer", "value": 0.8, "uncertainty": 0.05, "reasoning": "test"},
            {"source": "metacognitive", "value": 0.7, "uncertainty": 0.1, "reasoning": "test"},
        ]
        result = await ai_architect_fuse_confidence(estimates=estimates)
        assert "point" in result
        assert "lower" in result
        assert "upper" in result
