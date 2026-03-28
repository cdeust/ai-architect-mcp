"""Tests for adaptive expansion."""

from __future__ import annotations

import pytest

from ai_architect_mcp._prompting.algorithms.adaptive_expansion import AdaptiveExpansion
from tests.conftest import StubLLMClient


class TestAdaptiveExpansion:
    @pytest.mark.asyncio
    async def test_graph_grows(self) -> None:
        expander = AdaptiveExpansion(client=StubLLMClient())
        result = await expander.expand("Test", "Context", max_depth=3)
        assert result.strategy_used == "adaptive_expansion"
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_iterations_tracked(self) -> None:
        expander = AdaptiveExpansion(client=StubLLMClient())
        result = await expander.expand("Test", "Context", max_depth=2)
        assert result.iterations >= 1

    def test_rejects_none_client(self) -> None:
        with pytest.raises(ValueError, match="requires an LLM client"):
            AdaptiveExpansion(client=None)
