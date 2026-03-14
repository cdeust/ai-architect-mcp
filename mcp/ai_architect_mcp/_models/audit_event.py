"""Audit event model — immutable log entries for pipeline actions.

Every tool call, gate decision, and stage transition produces an audit
event. Events are append-only and frozen after creation — they cannot
be modified or deleted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

MIN_STAGE: int = 0
MAX_STAGE: int = 10


class AuditOutcome(str, Enum):
    """Outcome of an audited action."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


class AuditEvent(BaseModel, frozen=True):
    """Immutable audit log entry for a pipeline action.

    Frozen after creation. Cannot be modified or deleted.

    Attributes:
        event_id: Unique identifier for this event.
        session_id: Session that produced this event.
        stage_id: Pipeline stage where the action occurred (0-10).
        tool_name: Name of the tool or gate that was invoked.
        outcome: Result of the action.
        message: Human-readable description of what happened.
        timestamp: UTC timestamp of the event.
        metadata: Additional context as key-value pairs.
    """

    event_id: str = Field(description="Unique identifier for this event")
    session_id: str = Field(description="Session that produced this event")
    stage_id: int = Field(
        ge=MIN_STAGE, le=MAX_STAGE, description="Pipeline stage (0-10)"
    )
    tool_name: str = Field(description="Tool or gate that was invoked")
    outcome: AuditOutcome = Field(description="Result of the action")
    message: str = Field(description="Human-readable event description")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the event",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional context key-value pairs"
    )


class AuditQuery(BaseModel):
    """Filter parameters for querying audit events.

    All fields are optional. When set, they are combined with AND logic.

    Attributes:
        session_id: Filter by session.
        stage_id: Filter by pipeline stage.
        outcome: Filter by action outcome.
        since: Only events after this timestamp.
        limit: Maximum number of events to return (1-1000).
    """

    session_id: str | None = Field(
        default=None, description="Filter by session"
    )
    stage_id: int | None = Field(
        default=None, description="Filter by pipeline stage"
    )
    outcome: AuditOutcome | None = Field(
        default=None, description="Filter by action outcome"
    )
    since: datetime | None = Field(
        default=None, description="Only events after this timestamp"
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Max events to return"
    )
