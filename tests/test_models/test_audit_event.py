"""Tests for AuditEvent, AuditOutcome, and AuditQuery models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._models.audit_event import (
    AuditEvent,
    AuditOutcome,
    AuditQuery,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_audit_event_is_frozen() -> None:
    """AuditEvent cannot be modified after creation."""
    event = AuditEvent(
        event_id="evt-001",
        session_id="sess-001",
        stage_id=0,
        tool_name="test_tool",
        outcome=AuditOutcome.PASS,
        message="Test event",
    )
    with pytest.raises(Exception):
        event.message = "modified"  # type: ignore[misc]


def test_audit_event_creation() -> None:
    """AuditEvent can be created with all required fields."""
    event = AuditEvent(
        event_id="evt-002",
        session_id="sess-001",
        stage_id=5,
        tool_name="ai_architect_verify",
        outcome=AuditOutcome.FAIL,
        message="Verification failed",
    )
    assert event.outcome == AuditOutcome.FAIL
    assert event.metadata == {}


def test_audit_query_defaults() -> None:
    """AuditQuery has sensible defaults."""
    query = AuditQuery()
    assert query.session_id is None
    assert query.stage_id is None
    assert query.outcome is None
    assert query.since is None
    assert query.limit == 100


def test_audit_outcome_values() -> None:
    """AuditOutcome has all expected values."""
    expected = {"pass", "fail", "skip", "error"}
    actual = {o.value for o in AuditOutcome}
    assert actual == expected


def test_fixture_round_trip() -> None:
    """Events from fixture file round-trip through model."""
    raw = json.loads((FIXTURES / "audit_events_sample.json").read_text())
    events = [AuditEvent.model_validate(item) for item in raw]
    assert len(events) == 5
    assert events[0].event_id == "evt-001"
