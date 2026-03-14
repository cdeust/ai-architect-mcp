"""Session state model — tracks pipeline execution for a single session.

Stores the current stage, status, completed stages, and timing metadata.
Named SessionState (not PipelineState) to avoid collision with the existing
PipelineState model used for stage-level tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class PipelineStatus(str, Enum):
    """Status of a pipeline execution session."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


MIN_STAGE: int = 0
MAX_STAGE: int = 10


class SessionState(BaseModel):
    """Persistent state for a single pipeline execution session.

    Tracks which stage the pipeline is on, which stages have completed,
    and when the session was started and last updated.

    Attributes:
        session_id: Unique identifier for this session.
        finding_id: Finding being processed in this session.
        current_stage: Pipeline stage currently executing (0-10).
        status: Current execution status.
        started_at: UTC timestamp when the session began.
        updated_at: UTC timestamp of the last state change.
        completed_stages: Sorted list of stage numbers that finished.
        error_message: Description of failure if status is FAILED.
        metadata: Arbitrary key-value pairs for extension.
    """

    session_id: str = Field(description="Unique identifier for this session")
    finding_id: str = Field(description="Finding being processed")
    current_stage: int = Field(
        ge=MIN_STAGE, le=MAX_STAGE, description="Pipeline stage currently executing (0-10)"
    )
    status: PipelineStatus = Field(description="Current execution status")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the session began",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the last state change",
    )
    completed_stages: list[int] = Field(
        default_factory=list,
        description="Sorted list of completed stage numbers",
    )
    error_message: str | None = Field(
        default=None, description="Failure description if status is FAILED"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Arbitrary key-value extension data"
    )

    @model_validator(mode="after")
    def _validate_completed_stages(self) -> SessionState:
        """Ensure completed_stages are valid stage numbers and sorted."""
        for stage in self.completed_stages:
            if stage < MIN_STAGE or stage > MAX_STAGE:
                msg = (
                    f"completed_stages contains {stage} which is outside "
                    f"the valid range {MIN_STAGE}-{MAX_STAGE}"
                )
                raise ValueError(msg)
        self.completed_stages = sorted(self.completed_stages)
        return self
