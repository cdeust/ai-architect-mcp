"""Tests for collaborative inference."""

from __future__ import annotations

import pytest

from ai_architect_mcp._prompting.algorithms.collaborative_inference import CollaborativeInference


class TestCollaborativeInference:
    @pytest.mark.asyncio
    async def test_path_count(self) -> None:
        ci = CollaborativeInference(client=None)
        result = await ci.infer("Test", "Context", path_count=3)
        assert result.strategy_used == "collaborative_inference"

    @pytest.mark.asyncio
    async def test_consensus_detection(self) -> None:
        ci = CollaborativeInference(client=None)
        result = await ci.infer("Test", "Context", path_count=5, max_steps=3)
        assert result.confidence > 0.0
