"""Tests for SSEObservabilityAdapter — SSE server and client management."""

from __future__ import annotations

import asyncio

import pytest

from ai_architect_mcp._observability.event_types import EventType, PipelineEvent
from ai_architect_mcp._observability.sse_adapter import SSEObservabilityAdapter


def _make_event(event_id: str = "s1") -> PipelineEvent:
    return PipelineEvent(
        event_id=event_id,
        event_type=EventType.TOOL_COMPLETED,
        stage_id=5,
        message="Test SSE event",
    )


class TestSSEObservabilityAdapter:
    @pytest.mark.asyncio
    async def test_start_assigns_port(self) -> None:
        adapter = SSEObservabilityAdapter()
        try:
            port = await adapter.start()
            assert port > 0
            assert adapter.port == port
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_emit_no_clients_is_noop(self) -> None:
        adapter = SSEObservabilityAdapter()
        await adapter.emit(_make_event())
        assert adapter.client_count == 0

    @pytest.mark.asyncio
    async def test_close_idempotent(self) -> None:
        adapter = SSEObservabilityAdapter()
        await adapter.start()
        await adapter.close()
        await adapter.close()
        assert adapter.client_count == 0

    @pytest.mark.asyncio
    async def test_client_receives_event(self) -> None:
        adapter = SSEObservabilityAdapter()
        port = await adapter.start()

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)

            writer.write(b"GET /events HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await writer.drain()

            await asyncio.sleep(0.1)

            await adapter.emit(_make_event("sse-test"))

            data = await asyncio.wait_for(reader.read(4096), timeout=1.0)
            text = data.decode("utf-8")

            assert "200 OK" in text
            assert "text/event-stream" in text

            writer.close()
            await writer.wait_closed()
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_multiple_clients_tracked(self) -> None:
        adapter = SSEObservabilityAdapter()
        port = await adapter.start()

        try:
            r1, w1 = await asyncio.open_connection("127.0.0.1", port)
            w1.write(b"GET /events HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await w1.drain()
            await asyncio.sleep(0.1)

            r2, w2 = await asyncio.open_connection("127.0.0.1", port)
            w2.write(b"GET /events HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await w2.drain()
            await asyncio.sleep(0.1)

            assert adapter.client_count == 2

            w1.close()
            await w1.wait_closed()
            w2.close()
            await w2.wait_closed()
        finally:
            await adapter.close()
