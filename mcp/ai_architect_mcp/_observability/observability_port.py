"""Port interface for pipeline observability.

Defines the abstract base class for emitting pipeline events.
Concrete adapters (file, SSE, composite) implement this port
and are injected at the composition root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_architect_mcp._observability.event_types import PipelineEvent


class ObservabilityPort(ABC):
    """Port for emitting pipeline events to observers.

    Implementations may write to files, stream via SSE,
    or multiplex across multiple backends. All methods are async.
    """

    @abstractmethod
    async def emit(self, event: PipelineEvent) -> None:
        """Emit a single pipeline event.

        Args:
            event: The immutable event to emit.
        """
        ...

    @abstractmethod
    async def flush(self) -> None:
        """Flush any buffered events to their destination.

        Called at stage boundaries to ensure events are persisted.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Release resources held by this adapter.

        Called during shutdown. Must be safe to call multiple times.
        """
        ...
