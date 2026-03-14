"""Tests for verification tools."""

from __future__ import annotations

import pytest


class TestVerificationTools:
    @pytest.mark.asyncio
    async def test_verify_claim(self) -> None:
        from ai_architect_mcp._tools.verification_tools import ai_architect_verify_claim

        result = await ai_architect_verify_claim(content="Test claim", context="Context")
        assert "score" in result

    @pytest.mark.asyncio
    async def test_verify_graph(self) -> None:
        from ai_architect_mcp._tools.verification_tools import ai_architect_verify_graph

        result = await ai_architect_verify_graph(graph_data={"nodes": [], "edges": []})
        assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_decompose_claim(self) -> None:
        from ai_architect_mcp._tools.verification_tools import ai_architect_decompose_claim

        result = await ai_architect_decompose_claim(content="Simple claim")
        assert len(result) >= 1
