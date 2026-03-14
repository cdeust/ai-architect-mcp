"""Tests for context tools."""

from __future__ import annotations

import pytest


class TestContextTools:
    @pytest.mark.asyncio
    async def test_save_and_load_context(self) -> None:
        from ai_architect_mcp._tools.context_tools import (
            ai_architect_load_context,
            ai_architect_save_context,
        )

        save_result = await ai_architect_save_context(
            stage_id=1,
            finding_id="test-finding-001",
            artifact={"key": "value"},
        )
        assert save_result["status"] == "saved"

        load_result = await ai_architect_load_context(
            stage_id=1,
            finding_id="test-finding-001",
        )
        assert load_result["key"] == "value"

    @pytest.mark.asyncio
    async def test_create_handoff(self) -> None:
        from ai_architect_mcp._tools.context_tools import ai_architect_create_handoff

        result = await ai_architect_create_handoff(
            completed=["task1"],
            in_progress=["task2"],
            blocked=[],
            next_actions=["task3"],
            session_id="test-session",
        )
        assert "markdown" in result
        assert result["session_id"] == "test-session"
