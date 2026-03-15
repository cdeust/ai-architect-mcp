"""Fixture validation — brain-trace-sample.jsonl schema and coverage tests.

Every line in the fixture must validate against PipelineEvent.
All 14 EventType values must be represented.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_architect_mcp._observability.event_types import EventType, PipelineEvent

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "brain-trace-sample.jsonl"


class TestBrainTraceFixture:
    def test_fixture_exists(self) -> None:
        assert FIXTURE_PATH.exists(), f"Fixture not found: {FIXTURE_PATH}"

    def test_all_lines_validate(self) -> None:
        lines = FIXTURE_PATH.read_text().strip().splitlines()
        assert len(lines) > 0, "Fixture is empty"

        for i, line in enumerate(lines):
            parsed = json.loads(line)
            event = PipelineEvent.model_validate(parsed)
            assert event.event_id, f"Line {i}: missing event_id"
            assert event.event_type in EventType, f"Line {i}: invalid type"

    def test_covers_all_event_types(self) -> None:
        lines = FIXTURE_PATH.read_text().strip().splitlines()
        types_found: set[EventType] = set()

        for line in lines:
            parsed = json.loads(line)
            event = PipelineEvent.model_validate(parsed)
            types_found.add(event.event_type)

        missing = set(EventType) - types_found
        assert not missing, (
            f"Fixture missing event types: {[m.value for m in missing]}"
        )

    def test_has_14_lines(self) -> None:
        lines = FIXTURE_PATH.read_text().strip().splitlines()
        assert len(lines) == 14, f"Expected 14 lines (one per type), got {len(lines)}"

    def test_roundtrip_serialization(self) -> None:
        lines = FIXTURE_PATH.read_text().strip().splitlines()
        for line in lines:
            parsed = json.loads(line)
            event = PipelineEvent.model_validate(parsed)
            reserialized = json.loads(event.model_dump_json())
            assert reserialized["event_id"] == parsed["event_id"]
            assert reserialized["event_type"] == parsed["event_type"]
            assert reserialized["stage_id"] == parsed["stage_id"]
