"""Tests for pipeline event types and PipelineEvent model."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_architect_mcp._observability.event_types import EventType, PipelineEvent


class TestEventType:
    def test_has_14_event_types(self) -> None:
        assert len(EventType) == 14

    def test_all_values_are_lowercase_snake_case(self) -> None:
        for et in EventType:
            assert et.value == et.value.lower()
            assert " " not in et.value

    def test_stage_started_value(self) -> None:
        assert EventType.STAGE_STARTED.value == "stage_started"

    def test_ooda_checkpoint_value(self) -> None:
        assert EventType.OODA_CHECKPOINT.value == "ooda_checkpoint"


class TestPipelineEvent:
    def test_create_minimal_event(self) -> None:
        event = PipelineEvent(
            event_id="test-001",
            event_type=EventType.TOOL_CALLED,
            stage_id=3,
        )
        assert event.event_id == "test-001"
        assert event.event_type == EventType.TOOL_CALLED
        assert event.stage_id == 3
        assert event.session_id == ""
        assert event.tool_name == ""
        assert event.duration_ms is None
        assert event.metadata == {}

    def test_create_full_event(self) -> None:
        ts = datetime(2026, 3, 15, tzinfo=timezone.utc)
        event = PipelineEvent(
            event_id="test-002",
            event_type=EventType.HOR_RULE_EVALUATED,
            stage_id=7,
            session_id="sess-abc",
            timestamp=ts,
            tool_name="verify",
            message="Rule 1 passed",
            duration_ms=42.5,
            metadata={"rule_id": "1"},
        )
        assert event.session_id == "sess-abc"
        assert event.duration_ms == 42.5
        assert event.metadata["rule_id"] == "1"

    def test_event_is_frozen(self) -> None:
        event = PipelineEvent(
            event_id="test-003",
            event_type=EventType.STAGE_STARTED,
            stage_id=0,
        )
        try:
            event.stage_id = 5  # type: ignore[misc]
            assert False, "Should have raised"
        except (AttributeError, TypeError, ValueError):
            pass

    def test_serialization_roundtrip(self) -> None:
        event = PipelineEvent(
            event_id="test-004",
            event_type=EventType.GATE_EVALUATED,
            stage_id=7,
            message="Gate passed",
        )
        json_str = event.model_dump_json()
        restored = PipelineEvent.model_validate_json(json_str)
        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type

    def test_stage_id_validation(self) -> None:
        try:
            PipelineEvent(
                event_id="bad",
                event_type=EventType.STAGE_STARTED,
                stage_id=11,
            )
            assert False, "Should have raised for stage_id > 10"
        except ValueError:
            pass
