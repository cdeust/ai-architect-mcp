"""Tests for signal-aware thought buffer."""

from __future__ import annotations

import pytest

from ai_architect_mcp._prompting.algorithms.thought_buffer import SignalAwareThoughtBuffer


class TestThoughtBuffer:
    @pytest.mark.asyncio
    async def test_template_retrieval(self) -> None:
        buffer = SignalAwareThoughtBuffer(client=None)
        result = await buffer.process("Analyze this architecture", "Context")
        assert result.strategy_used == "thought_buffer"

    @pytest.mark.asyncio
    async def test_confidence_tracked(self) -> None:
        buffer = SignalAwareThoughtBuffer(client=None)
        result = await buffer.process("Test", "Context")
        assert result.confidence > 0.0
