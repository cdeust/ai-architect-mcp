"""Local JSONL adapter for immutable audit event logging.

Stores events in {data_dir}/audit/events.jsonl, one JSON line per event.
Append-only — events are never modified or deleted.
Implements AuditPort.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_architect_mcp._adapters.memory_ports import AuditPort
from ai_architect_mcp._models.audit_event import AuditEvent, AuditQuery

AUDIT_DIR: str = "audit"
EVENTS_FILE: str = "events.jsonl"


class LocalAudit(AuditPort):
    """JSONL append-only persistence for audit events.

    Each event is a single JSON line appended to the events file.
    Query reads all lines and applies filters in memory.

    Args:
        data_dir: Root directory for all persistence data.
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize the local audit adapter.

        Args:
            data_dir: Root directory for persistence.
        """
        self._dir = data_dir / AUDIT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / EVENTS_FILE

    async def append(self, event: AuditEvent) -> None:
        """Append an audit event as a single JSONL line.

        Args:
            event: The immutable event to record.
        """
        line = event.model_dump_json() + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query audit events with optional filters.

        Args:
            query: Filter parameters combined with AND logic.

        Returns:
            Matching events sorted by timestamp descending, capped at limit.
        """
        if not self._path.exists():
            return []

        events: list[AuditEvent] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            event = AuditEvent.model_validate(json.loads(stripped))
            if not self._matches(event, query):
                continue
            events.append(event)

        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[: query.limit]

    @staticmethod
    def _matches(event: AuditEvent, query: AuditQuery) -> bool:
        """Check if an event matches all non-None query filters.

        Args:
            event: The event to test.
            query: Filter criteria.

        Returns:
            True if the event passes all filters.
        """
        if query.session_id is not None and event.session_id != query.session_id:
            return False
        if query.stage_id is not None and event.stage_id != query.stage_id:
            return False
        if query.outcome is not None and event.outcome != query.outcome:
            return False
        if query.since is not None and event.timestamp < query.since:
            return False
        return True
