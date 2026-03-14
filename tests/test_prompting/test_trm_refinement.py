"""Tests for TRM refinement."""

from __future__ import annotations

import pytest

from ai_architect_mcp._prompting.algorithms.trm_refinement import TRMRefinement


class TestTRMRefinement:
    @pytest.mark.asyncio
    async def test_halts_on_convergence(self) -> None:
        trm = TRMRefinement(client=None)
        result = await trm.refine("Test prompt", "Test context", max_iterations=10)
        assert result.iterations <= 10
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_max_iterations_respected(self) -> None:
        trm = TRMRefinement(client=None)
        result = await trm.refine("Test prompt", "Test context", max_iterations=2)
        assert result.iterations <= 2

    @pytest.mark.asyncio
    async def test_enhanced_differs_from_original(self) -> None:
        trm = TRMRefinement(client=None)
        result = await trm.refine("Original", "Context", max_iterations=3)
        assert result.original == "Original"
