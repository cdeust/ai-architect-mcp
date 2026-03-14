"""Tests for enforce doc read hook."""

from __future__ import annotations

import pytest

from ai_architect_mcp._hooks.base import HookContext, HookStatus
from ai_architect_mcp._hooks.enforce_doc_read import EnforceDocReadHook


class TestEnforceDocReadHook:
    """Tests for EnforceDocReadHook."""

    @pytest.mark.asyncio
    async def test_blocks_when_not_read(self) -> None:
        hook = EnforceDocReadHook()
        ctx = HookContext(
            tool_name="ai_architect_verify_claim",
            skill_md_read=False,
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.BLOCK
        assert "SKILL.md" in result.message

    @pytest.mark.asyncio
    async def test_passes_when_read(self) -> None:
        hook = EnforceDocReadHook()
        ctx = HookContext(
            tool_name="ai_architect_verify_claim",
            skill_md_read=True,
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS

    @pytest.mark.asyncio
    async def test_exempt_tool_passes(self) -> None:
        hook = EnforceDocReadHook()
        ctx = HookContext(
            tool_name="ai_architect_load_session_state",
            skill_md_read=False,
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
        assert "exempt" in result.message

    @pytest.mark.asyncio
    async def test_budget_check_exempt(self) -> None:
        hook = EnforceDocReadHook()
        ctx = HookContext(
            tool_name="ai_architect_check_context_budget",
            skill_md_read=False,
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
