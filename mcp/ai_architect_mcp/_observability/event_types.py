"""Pipeline event types for real-time observability.

Defines the 12 event types emitted during pipeline execution and the
PipelineEvent model that carries event data. Events are immutable
after creation — frozen Pydantic models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

MIN_STAGE: int = 0
MAX_STAGE: int = 10


class EventType(str, Enum):
    """Types of events emitted during pipeline execution."""

    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"
    ARTIFACT_SAVED = "artifact_saved"
    HOR_RULE_EVALUATED = "hor_rule_evaluated"
    GATE_EVALUATED = "gate_evaluated"
    OODA_CHECKPOINT = "ooda_checkpoint"
    CONTEXT_LOADED = "context_loaded"
    PIPELINE_ERROR = "pipeline_error"
    THINKING_STEP = "thinking_step"
    DECISION_MADE = "decision_made"


class PipelineEvent(BaseModel, frozen=True):
    """Immutable event emitted during pipeline execution.

    Frozen after creation. Cannot be modified or deleted.
    Used for real-time observability via SSE and JSONL persistence.

    Attributes:
        event_id: Unique identifier for this event.
        event_type: Category of the event.
        stage_id: Pipeline stage where the event occurred (0-10).
        session_id: Session that produced this event.
        timestamp: UTC timestamp of the event.
        tool_name: Name of the tool involved, if any.
        message: Human-readable event description.
        duration_ms: Duration in milliseconds for timed events.
        metadata: Additional context as key-value pairs.
    """

    event_id: str = Field(description="Unique identifier for this event")
    event_type: EventType = Field(description="Category of the event")
    stage_id: int = Field(
        ge=MIN_STAGE, le=MAX_STAGE, description="Pipeline stage (0-10)"
    )
    session_id: str = Field(
        default="", description="Session that produced this event"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the event",
    )
    tool_name: str = Field(
        default="", description="Tool involved in this event"
    )
    message: str = Field(
        default="", description="Human-readable event description"
    )
    duration_ms: float | None = Field(
        default=None, description="Duration in milliseconds for timed events"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context as key-value pairs",
    )
