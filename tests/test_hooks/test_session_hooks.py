"""Tests for session start and session end hooks."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect_mcp._hooks.base import HookContext, HookStatus
from ai_architect_mcp._hooks.save_session_summary import (
    SaveSessionSummaryHook,
)
from ai_architect_mcp._hooks.session_start import SessionStartHook


class TestSessionStartHook:
    """Tests for SessionStartHook."""

    @pytest.mark.asyncio
    async def test_empty_session_id_blocks(self) -> None:
        hook = SessionStartHook()
        ctx = HookContext(session_id="")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.BLOCK
        assert "session_id" in result.message.lower()

    @pytest.mark.asyncio
    async def test_valid_session_passes(self, tmp_path: Path) -> None:
        hook = SessionStartHook(project_root=tmp_path)
        ctx = HookContext(session_id="test-session", stage_id=0)
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS

    @pytest.mark.asyncio
    async def test_finds_skill_md(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "skills" / "stage-1-discovery"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Stage 1")

        hook = SessionStartHook(project_root=tmp_path)
        ctx = HookContext(session_id="sess-1", stage_id=1)
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
        assert "skill_md" in result.metadata


class TestSaveSessionSummaryHook:
    """Tests for SaveSessionSummaryHook."""

    @pytest.mark.asyncio
    async def test_generates_handoff(self) -> None:
        hook = SaveSessionSummaryHook()
        ctx = HookContext(
            session_id="test-session",
            input_data={
                "completed": ["Task A"],
                "in_progress": ["Task B"],
                "blocked": [],
                "next_actions": ["Task C"],
            },
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
        assert "handoff_markdown" in result.metadata
        assert "Task A" in result.metadata["handoff_markdown"]

    @pytest.mark.asyncio
    async def test_empty_session(self) -> None:
        hook = SaveSessionSummaryHook()
        ctx = HookContext(session_id="empty-session")
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
        assert "handoff_data" in result.metadata
