"""Tests for CompositeObservabilityAdapter — fan-out with error isolation."""

from __future__ import annotations

import pytest

from ai_architect_mcp._observability.composite_adapter import (
    CompositeObservabilityAdapter,
)
from ai_architect_mcp._observability.event_types import EventType, PipelineEvent
from ai_architect_mcp._observability.observability_port import ObservabilityPort


class FakeAdapter(ObservabilityPort):
    """Test double that records calls."""

    def __init__(self) -> None:
        self.events: list[PipelineEvent] = []
        self.flushed: int = 0
        self.closed: int = 0

    async def emit(self, event: PipelineEvent) -> None:
        self.events.append(event)

    async def flush(self) -> None:
        self.flushed += 1

    async def close(self) -> None:
        self.closed += 1


class FailingAdapter(ObservabilityPort):
    """Test double that always raises."""

    async def emit(self, event: PipelineEvent) -> None:
        raise RuntimeError("emit failed")

    async def flush(self) -> None:
        raise RuntimeError("flush failed")

    async def close(self) -> None:
        raise RuntimeError("close failed")


def _make_event(event_id: str = "c1") -> PipelineEvent:
    return PipelineEvent(
        event_id=event_id,
        event_type=EventType.STAGE_STARTED,
        stage_id=1,
    )


class TestCompositeObservabilityAdapter:
    @pytest.mark.asyncio
    async def test_emit_fans_out(self) -> None:
        a1, a2 = FakeAdapter(), FakeAdapter()
        composite = CompositeObservabilityAdapter(adapters=[a1, a2])
        await composite.emit(_make_event())
        assert len(a1.events) == 1
        assert len(a2.events) == 1

    @pytest.mark.asyncio
    async def test_error_isolation_on_emit(self) -> None:
        good = FakeAdapter()
        bad = FailingAdapter()
        composite = CompositeObservabilityAdapter(adapters=[bad, good])
        await composite.emit(_make_event())
        assert len(good.events) == 1

    @pytest.mark.asyncio
    async def test_flush_fans_out(self) -> None:
        a1, a2 = FakeAdapter(), FakeAdapter()
        composite = CompositeObservabilityAdapter(adapters=[a1, a2])
        await composite.flush()
        assert a1.flushed == 1
        assert a2.flushed == 1

    @pytest.mark.asyncio
    async def test_close_fans_out(self) -> None:
        a1, a2 = FakeAdapter(), FakeAdapter()
        composite = CompositeObservabilityAdapter(adapters=[a1, a2])
        await composite.close()
        assert a1.closed == 1
        assert a2.closed == 1

    @pytest.mark.asyncio
    async def test_error_isolation_on_close(self) -> None:
        good = FakeAdapter()
        bad = FailingAdapter()
        composite = CompositeObservabilityAdapter(adapters=[bad, good])
        await composite.close()
        assert good.closed == 1

    def test_adapter_count(self) -> None:
        composite = CompositeObservabilityAdapter(adapters=[FakeAdapter()] * 3)
        assert composite.adapter_count == 3
