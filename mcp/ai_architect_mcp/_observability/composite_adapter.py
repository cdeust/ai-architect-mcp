"""Composite adapter that multiplexes events to N observability backends.

Error-isolated: if one adapter fails, others still receive the event.
Logs errors but never raises from emit/flush — observability must not
break the pipeline.
"""

from __future__ import annotations

import logging

from ai_architect_mcp._observability.event_types import PipelineEvent
from ai_architect_mcp._observability.observability_port import ObservabilityPort

logger = logging.getLogger(__name__)


class CompositeObservabilityAdapter(ObservabilityPort):
    """Multiplexes pipeline events to multiple adapters.

    Each adapter is called independently. Failures in one adapter
    do not affect others — errors are logged, not raised.

    Args:
        adapters: List of ObservabilityPort implementations to fan out to.
    """

    def __init__(self, adapters: list[ObservabilityPort]) -> None:
        """Initialize with a list of adapters.

        Args:
            adapters: Backend adapters to multiplex events to.
        """
        self._adapters = list(adapters)

    @property
    def adapter_count(self) -> int:
        """Return the number of registered adapters."""
        return len(self._adapters)

    async def emit(self, event: PipelineEvent) -> None:
        """Emit event to all adapters, error-isolated.

        Args:
            event: The immutable event to emit.
        """
        for adapter in self._adapters:
            try:
                await adapter.emit(event)
            except Exception:
                logger.exception(
                    "Observability adapter %s failed to emit event %s",
                    type(adapter).__name__,
                    event.event_id,
                )

    async def flush(self) -> None:
        """Flush all adapters, error-isolated."""
        for adapter in self._adapters:
            try:
                await adapter.flush()
            except Exception:
                logger.exception(
                    "Observability adapter %s failed to flush",
                    type(adapter).__name__,
                )

    async def close(self) -> None:
        """Close all adapters, error-isolated."""
        for adapter in self._adapters:
            try:
                await adapter.close()
            except Exception:
                logger.exception(
                    "Observability adapter %s failed to close",
                    type(adapter).__name__,
                )
