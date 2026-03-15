"""Local JSONL adapter for pipeline event persistence.

Stores events in {data_dir}/brain-trace.jsonl, one JSON line per event.
Append-only — events are never modified or deleted.
Implements ObservabilityPort.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ai_architect_mcp._observability.event_types import PipelineEvent
from ai_architect_mcp._observability.observability_port import ObservabilityPort

TRACE_FILE: str = "brain-trace.jsonl"

logger = logging.getLogger(__name__)


class FileObservabilityAdapter(ObservabilityPort):
    """JSONL append-only persistence for pipeline events.

    Each event is a single JSON line appended to the trace file.
    Creates parent directories on initialization.

    Args:
        data_dir: Directory where brain-trace.jsonl is written.
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize the file observability adapter.

        Args:
            data_dir: Directory for the trace file.
        """
        self._dir = data_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / TRACE_FILE
        self._file_handle = None

    async def emit(self, event: PipelineEvent) -> None:
        """Append an event as a single JSONL line.

        Args:
            event: The immutable event to record.
        """
        line = event.model_dump_json() + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    async def flush(self) -> None:
        """No-op — each emit writes immediately."""

    async def close(self) -> None:
        """No-op — no persistent file handle to close."""
        logger.debug("FileObservabilityAdapter closed")
