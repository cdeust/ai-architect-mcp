"""SSE adapter for real-time pipeline event streaming.

Starts an HTTP server on an ephemeral port (port 0) that streams
pipeline events as Server-Sent Events. No-op when no clients are
connected — zero overhead when not observed.
"""

from __future__ import annotations

import asyncio
import logging

from ai_architect_mcp._observability.event_types import PipelineEvent
from ai_architect_mcp._observability.observability_port import ObservabilityPort

SSE_CONTENT_TYPE: str = "text/event-stream"
SSE_HEADERS: dict[str, str] = {
    "Content-Type": SSE_CONTENT_TYPE,
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": "*",
}

logger = logging.getLogger(__name__)


class SSEObservabilityAdapter(ObservabilityPort):
    """HTTP SSE adapter for real-time event streaming.

    Binds to port 0 (OS-assigned) on start. Maintains a set of
    connected client queues. Events are only serialized when at
    least one client is connected.

    Call start() before emitting events. Call close() to shut down.
    """

    def __init__(self) -> None:
        """Initialize the SSE adapter with empty client set."""
        self._clients: list[asyncio.Queue[str]] = []
        self._handler_tasks: list[asyncio.Task[None]] = []
        self._server: asyncio.AbstractServer | None = None
        self._port: int = 0
        self._started: bool = False

    @property
    def port(self) -> int:
        """Return the port the SSE server is listening on."""
        return self._port

    @property
    def client_count(self) -> int:
        """Return the number of connected SSE clients."""
        return len(self._clients)

    async def start(self) -> int:
        """Start the SSE HTTP server on an ephemeral port.

        Returns:
            The port number assigned by the OS.
        """
        self._server = await asyncio.start_server(
            self._on_connect, host="127.0.0.1", port=0
        )
        addr = self._server.sockets[0].getsockname()
        self._port = addr[1]
        self._started = True
        logger.info("SSE observability server listening on port %d", self._port)
        return self._port

    async def emit(self, event: PipelineEvent) -> None:
        """Send event to all connected SSE clients.

        No-op when no clients are connected — zero serialization overhead.

        Args:
            event: The immutable event to stream.
        """
        if not self._clients:
            return

        data = event.model_dump_json()
        sse_message = f"event: pipeline\ndata: {data}\n\n"

        disconnected: list[asyncio.Queue[str]] = []
        for queue in self._clients:
            try:
                queue.put_nowait(sse_message)
            except asyncio.QueueFull:
                disconnected.append(queue)

        for queue in disconnected:
            self._clients.remove(queue)

    async def flush(self) -> None:
        """No-op — SSE events are pushed immediately."""

    async def close(self) -> None:
        """Shut down the SSE server and disconnect all clients.

        Cancels all handler tasks and waits for cleanup.
        Safe to call multiple times.
        """
        for task in self._handler_tasks:
            task.cancel()

        if self._handler_tasks:
            await asyncio.gather(*self._handler_tasks, return_exceptions=True)
        self._handler_tasks.clear()

        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self._clients.clear()
        self._started = False
        logger.info("SSE observability server closed")

    def _on_connect(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Spawn a handler task for a new client connection.

        Args:
            reader: Client stream reader.
            writer: Client stream writer.
        """
        task = asyncio.create_task(self._handle_client(reader, writer))
        self._handler_tasks.append(task)
        task.add_done_callback(self._cleanup_task)

    def _cleanup_task(self, task: asyncio.Task[None]) -> None:
        """Remove a completed handler task from tracking.

        Args:
            task: The completed task to remove.
        """
        if task in self._handler_tasks:
            self._handler_tasks.remove(task)

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle an incoming SSE client connection.

        Args:
            reader: Client stream reader.
            writer: Client stream writer.
        """
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=256)
        self._clients.append(queue)
        logger.debug("SSE client connected, total: %d", len(self._clients))

        try:
            header = self._build_sse_header()
            writer.write(header.encode("utf-8"))
            await writer.drain()

            while True:
                message = await queue.get()
                writer.write(message.encode("utf-8"))
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
            pass
        finally:
            if queue in self._clients:
                self._clients.remove(queue)
            writer.close()
            logger.debug("SSE client disconnected, total: %d", len(self._clients))

    @staticmethod
    def _build_sse_header() -> str:
        """Build the HTTP response header for SSE streaming.

        Returns:
            HTTP response header string.
        """
        lines = ["HTTP/1.1 200 OK"]
        for key, value in SSE_HEADERS.items():
            lines.append(f"{key}: {value}")
        lines.append("")
        lines.append("")
        return "\r\n".join(lines)
