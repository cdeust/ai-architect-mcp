"""Tests for metacognitive monitor."""

from __future__ import annotations

import pytest

from ai_architect_mcp._prompting.algorithms.metacognitive import MetacognitiveMonitor


class TestMetacognitiveMonitor:
    @pytest.mark.asyncio
    async def test_intervention_triggering(self) -> None:
        monitor = MetacognitiveMonitor(client=None)
        result = await monitor.monitor("Prompt", "Response", "Context", max_iterations=5)
        assert result.strategy_used == "metacognitive"
        assert result.iterations >= 1

    @pytest.mark.asyncio
    async def test_strategy_switching(self) -> None:
        monitor = MetacognitiveMonitor(client=None)
        result = await monitor.monitor("Test", "Bad response", "Context", max_iterations=3)
        assert result.confidence > 0.0
