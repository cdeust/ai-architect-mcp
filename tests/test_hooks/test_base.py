"""Tests for hook base types."""

from __future__ import annotations

import pytest

from ai_architect_mcp._hooks.base import (
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)


class TestHookPhase:
    """Tests for HookPhase enum."""

    def test_values(self) -> None:
        assert HookPhase.SESSION_START == "session_start"
        assert HookPhase.PRE_TOOL == "pre_tool"
        assert HookPhase.POST_TOOL == "post_tool"
        assert HookPhase.SESSION_END == "session_end"

    def test_count(self) -> None:
        assert len(HookPhase) == 4


class TestHookStatus:
    """Tests for HookStatus enum."""

    def test_values(self) -> None:
        assert HookStatus.PASS == "pass"
        assert HookStatus.BLOCK == "block"
        assert HookStatus.ERROR == "error"


class TestHookResult:
    """Tests for HookResult model."""

    def test_creation(self) -> None:
        result = HookResult(
            hook_name="test_hook",
            status=HookStatus.PASS,
            message="all good",
        )
        assert result.hook_name == "test_hook"
        assert result.status == HookStatus.PASS
        assert result.timestamp is not None

    def test_round_trip(self) -> None:
        result = HookResult(
            hook_name="test", status=HookStatus.BLOCK, message="blocked",
        )
        data = result.model_dump(mode="json")
        restored = HookResult.model_validate(data)
        assert restored.hook_name == result.hook_name


class TestHookContext:
    """Tests for HookContext model."""

    def test_defaults(self) -> None:
        ctx = HookContext()
        assert ctx.session_id == ""
        assert ctx.stage_id == 0
        assert ctx.skill_md_read is False

    def test_custom_values(self) -> None:
        ctx = HookContext(
            session_id="sess-1",
            stage_id=5,
            tool_name="ai_architect_verify_claim",
            skill_md_read=True,
        )
        assert ctx.session_id == "sess-1"
        assert ctx.skill_md_read is True
