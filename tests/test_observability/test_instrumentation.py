"""Tests for instrumentation — observe_tool_call decorator and helpers."""

from __future__ import annotations

import pytest

from ai_architect_mcp._observability.event_types import EventType, PipelineEvent
from ai_architect_mcp._observability.instrumentation import (
    emit_artifact_saved,
    emit_hor_rule,
    observe_tool_call,
    set_observability_port,
)
from ai_architect_mcp._observability.observability_port import ObservabilityPort


class RecordingPort(ObservabilityPort):
    """Test double that records emitted events."""

    def __init__(self) -> None:
        self.events: list[PipelineEvent] = []

    async def emit(self, event: PipelineEvent) -> None:
        self.events.append(event)

    async def flush(self) -> None:
        pass

    async def close(self) -> None:
        pass


class TestObserveToolCall:
    @pytest.mark.asyncio
    async def test_emits_called_and_completed(self) -> None:
        port = RecordingPort()
        set_observability_port(port)

        @observe_tool_call
        async def ai_architect_test_tool(x: int) -> int:
            return x * 2

        try:
            result = await ai_architect_test_tool(5)
            assert result == 10
            assert len(port.events) == 2
            assert port.events[0].event_type == EventType.TOOL_CALLED
            assert port.events[1].event_type == EventType.TOOL_COMPLETED
            assert port.events[1].duration_ms is not None
        finally:
            set_observability_port(None)

    @pytest.mark.asyncio
    async def test_emits_failed_on_exception(self) -> None:
        port = RecordingPort()
        set_observability_port(port)

        @observe_tool_call
        async def ai_architect_failing() -> None:
            raise ValueError("boom")

        try:
            with pytest.raises(ValueError, match="boom"):
                await ai_architect_failing()
            assert len(port.events) == 2
            assert port.events[1].event_type == EventType.TOOL_FAILED
            assert "boom" in port.events[1].message
        finally:
            set_observability_port(None)

    @pytest.mark.asyncio
    async def test_noop_without_port(self) -> None:
        set_observability_port(None)

        @observe_tool_call
        async def ai_architect_quiet(x: int) -> int:
            return x + 1

        result = await ai_architect_quiet(3)
        assert result == 4


class TestEmitArtifactSaved:
    @pytest.mark.asyncio
    async def test_emits_event(self) -> None:
        port = RecordingPort()
        set_observability_port(port)
        try:
            await emit_artifact_saved(stage_id=3, finding_id="f-123")
            assert len(port.events) == 1
            assert port.events[0].event_type == EventType.ARTIFACT_SAVED
            assert port.events[0].metadata["finding_id"] == "f-123"
        finally:
            set_observability_port(None)

    @pytest.mark.asyncio
    async def test_noop_without_port(self) -> None:
        set_observability_port(None)
        await emit_artifact_saved(stage_id=0, finding_id="x")


class TestEmitHORRule:
    @pytest.mark.asyncio
    async def test_emits_event(self) -> None:
        port = RecordingPort()
        set_observability_port(port)
        try:
            await emit_hor_rule(
                rule_id=1,
                rule_name="title_exists",
                category="structural",
                passed=True,
            )
            assert len(port.events) == 1
            assert port.events[0].event_type == EventType.HOR_RULE_EVALUATED
            assert port.events[0].metadata["rule_id"] == "1"
            assert port.events[0].metadata["passed"] == "True"
        finally:
            set_observability_port(None)
