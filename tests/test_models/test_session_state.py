"""Tests for SessionState and PipelineStatus models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._models.session_state import (
    PipelineStatus,
    SessionState,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_session_state_creation() -> None:
    """SessionState can be created with required fields."""
    state = SessionState(
        session_id="sess-001",
        finding_id="FIND-001",
        current_stage=3,
        status=PipelineStatus.RUNNING,
    )
    assert state.session_id == "sess-001"
    assert state.current_stage == 3
    assert state.status == PipelineStatus.RUNNING
    assert state.completed_stages == []
    assert state.error_message is None


def test_session_state_from_fixture() -> None:
    """SessionState round-trips through JSON fixture."""
    raw = json.loads((FIXTURES / "session_state_running.json").read_text())
    state = SessionState.model_validate(raw)
    assert state.status == PipelineStatus.RUNNING
    assert state.completed_stages == [0, 1, 2]
    dumped = state.model_dump(mode="json")
    restored = SessionState.model_validate(dumped)
    assert restored.session_id == state.session_id


def test_completed_stages_validation_out_of_range() -> None:
    """completed_stages rejects stage numbers outside 0-10."""
    with pytest.raises(ValueError, match="outside the valid range"):
        SessionState(
            session_id="sess-bad",
            finding_id="FIND-001",
            current_stage=0,
            status=PipelineStatus.IDLE,
            completed_stages=[0, 1, 11],
        )


def test_completed_stages_sorted() -> None:
    """completed_stages are automatically sorted."""
    state = SessionState(
        session_id="sess-sort",
        finding_id="FIND-001",
        current_stage=5,
        status=PipelineStatus.RUNNING,
        completed_stages=[3, 1, 2],
    )
    assert state.completed_stages == [1, 2, 3]


def test_pipeline_status_enum_values() -> None:
    """PipelineStatus has all expected values."""
    expected = {"idle", "running", "paused", "completed", "failed", "cancelled"}
    actual = {s.value for s in PipelineStatus}
    assert actual == expected
