"""Tests for memory MCP tools — calls tool functions directly."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import ai_architect_mcp._tools.memory_tools as mt
import ai_architect_mcp._tools._composition as comp
from ai_architect_mcp._adapters.composition_root import CompositionRoot


@pytest.fixture(autouse=True)
def _inject_tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject a temporary CompositionRoot for all tests."""
    root = CompositionRoot(project_root=tmp_path)
    monkeypatch.setattr(comp, "_root", root)


@pytest.mark.asyncio
async def test_save_and_load_session_state() -> None:
    """Session state round-trips through tools."""
    state_data: dict[str, Any] = {
        "session_id": "sess-tool-001",
        "finding_id": "FIND-001",
        "current_stage": 3,
        "status": "running",
    }
    result = await mt.ai_architect_save_session_state(state_data)
    assert result["status"] == "saved"

    loaded = await mt.ai_architect_load_session_state("sess-tool-001")
    assert loaded is not None
    assert loaded["session_id"] == "sess-tool-001"
    assert loaded["current_stage"] == 3


@pytest.mark.asyncio
async def test_load_missing_session() -> None:
    """Loading non-existent session returns None."""
    result = await mt.ai_architect_load_session_state("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_save_and_list_experience_patterns() -> None:
    """Experience patterns save and list via tools."""
    pattern_data: dict[str, Any] = {
        "pattern_id": "pat-tool-001",
        "pattern_type": "success",
        "description": "Tool test pattern",
        "stage_id": 6,
    }
    result = await mt.ai_architect_save_experience_pattern(pattern_data)
    assert result["status"] == "saved"

    patterns = await mt.ai_architect_list_experience_patterns()
    assert len(patterns) == 1
    assert patterns[0]["pattern_id"] == "pat-tool-001"


@pytest.mark.asyncio
async def test_reinforce_pattern() -> None:
    """Reinforcing a pattern via tool increments count."""
    await mt.ai_architect_save_experience_pattern({
        "pattern_id": "pat-reinf",
        "pattern_type": "success",
        "description": "To reinforce",
        "stage_id": 3,
        "occurrence_count": 1,
    })
    reinforced = await mt.ai_architect_reinforce_pattern("pat-reinf")
    assert reinforced["occurrence_count"] == 2


@pytest.mark.asyncio
async def test_append_and_query_audit_events() -> None:
    """Audit events append and query via tools."""
    event_data: dict[str, Any] = {
        "event_id": "evt-tool-001",
        "session_id": "sess-001",
        "stage_id": 0,
        "tool_name": "test",
        "outcome": "pass",
        "message": "Tool test event",
    }
    result = await mt.ai_architect_append_audit_event(event_data)
    assert result["status"] == "appended"

    events = await mt.ai_architect_query_audit_events({})
    assert len(events) == 1
    assert events[0]["event_id"] == "evt-tool-001"


@pytest.mark.asyncio
async def test_check_context_budget_l3() -> None:
    """Budget check at 50% returns L3."""
    result = await mt.ai_architect_check_context_budget(
        total_tokens=100000, used_tokens=50000
    )
    assert result["disclosure_level"] == "l3_full"
    assert result["should_compact"] is False


@pytest.mark.asyncio
async def test_check_context_budget_l1() -> None:
    """Budget check at 94% returns L1 and should_compact."""
    result = await mt.ai_architect_check_context_budget(
        total_tokens=100000, used_tokens=94000
    )
    assert result["disclosure_level"] == "l1_config"
    assert result["should_compact"] is True
