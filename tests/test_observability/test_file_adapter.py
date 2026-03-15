"""Tests for FileObservabilityAdapter — JSONL persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._observability.event_types import EventType, PipelineEvent
from ai_architect_mcp._observability.file_adapter import (
    TRACE_FILE,
    FileObservabilityAdapter,
)


@pytest.fixture
def trace_dir(tmp_path: Path) -> Path:
    return tmp_path / "trace"


@pytest.fixture
def adapter(trace_dir: Path) -> FileObservabilityAdapter:
    return FileObservabilityAdapter(data_dir=trace_dir)


def _make_event(event_id: str, event_type: EventType = EventType.TOOL_CALLED) -> PipelineEvent:
    return PipelineEvent(
        event_id=event_id,
        event_type=event_type,
        stage_id=3,
        message=f"Test event {event_id}",
    )


class TestFileObservabilityAdapter:
    @pytest.mark.asyncio
    async def test_creates_directory(self, adapter: FileObservabilityAdapter, trace_dir: Path) -> None:
        assert trace_dir.exists()

    @pytest.mark.asyncio
    async def test_emit_writes_jsonl(self, adapter: FileObservabilityAdapter, trace_dir: Path) -> None:
        event = _make_event("e1")
        await adapter.emit(event)

        trace_path = trace_dir / TRACE_FILE
        assert trace_path.exists()

        lines = trace_path.read_text().strip().splitlines()
        assert len(lines) == 1

        parsed = json.loads(lines[0])
        assert parsed["event_id"] == "e1"
        assert parsed["event_type"] == "tool_called"

    @pytest.mark.asyncio
    async def test_multiple_emits_append(self, adapter: FileObservabilityAdapter, trace_dir: Path) -> None:
        await adapter.emit(_make_event("e1"))
        await adapter.emit(_make_event("e2"))
        await adapter.emit(_make_event("e3"))

        trace_path = trace_dir / TRACE_FILE
        lines = trace_path.read_text().strip().splitlines()
        assert len(lines) == 3

    @pytest.mark.asyncio
    async def test_each_line_valid_json(self, adapter: FileObservabilityAdapter, trace_dir: Path) -> None:
        for i in range(5):
            await adapter.emit(_make_event(f"e{i}"))

        trace_path = trace_dir / TRACE_FILE
        for line in trace_path.read_text().strip().splitlines():
            parsed = json.loads(line)
            assert "event_id" in parsed
            assert "event_type" in parsed

    @pytest.mark.asyncio
    async def test_flush_is_noop(self, adapter: FileObservabilityAdapter) -> None:
        await adapter.flush()

    @pytest.mark.asyncio
    async def test_close_is_safe(self, adapter: FileObservabilityAdapter) -> None:
        await adapter.close()
        await adapter.close()
