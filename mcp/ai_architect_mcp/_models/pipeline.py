"""Pipeline state models — stage tracking and artifact management.

Models for tracking finding progression through the 11-stage pipeline.
Each finding maintains its own PipelineState with per-stage outputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


MIN_STAGE_ID = 0
MAX_STAGE_ID = 10


class StageStatus(str, Enum):
    """Status of a pipeline stage for a specific finding."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageOutput(BaseModel):
    """Output artifact from a single pipeline stage.

    Each stage produces exactly one StageOutput per finding. The artifact
    dict contains stage-specific data (e.g., compound scores, PRD content,
    verification reports).
    """

    stage_id: int = Field(
        ge=MIN_STAGE_ID,
        le=MAX_STAGE_ID,
        description="Pipeline stage number (0-10)"
    )
    finding_id: str = Field(
        description="Unique identifier of the finding this output belongs to"
    )
    artifact: dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific output data"
    )
    status: StageStatus = Field(
        description="Current status of this stage"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this stage output was created or last updated"
    )
    error_message: str | None = Field(
        default=None,
        description="Error details if status is FAILED, None otherwise"
    )

    @model_validator(mode="after")
    def validate_error_message_consistency(self) -> StageOutput:
        """Ensure error_message is set when status is FAILED."""
        if self.status == StageStatus.FAILED and not self.error_message:
            msg = "error_message is required when status is FAILED — describe what went wrong and how to fix it"
            raise ValueError(msg)
        return self


class PipelineState(BaseModel):
    """Complete pipeline state for a single finding.

    Tracks which stages have been completed, what the current stage is,
    and stores all stage outputs. This is the top-level state object
    that persists across sessions via HandoffDocument.
    """

    finding_id: str = Field(
        description="Unique identifier of the finding being processed"
    )
    current_stage: int = Field(
        ge=MIN_STAGE_ID,
        le=MAX_STAGE_ID,
        description="The stage currently being executed (0-10)"
    )
    stage_outputs: dict[int, StageOutput] = Field(
        default_factory=dict,
        description="Map of stage_id to StageOutput for completed stages"
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When pipeline processing started for this finding"
    )
    completed_stages: list[int] = Field(
        default_factory=list,
        description="Sorted list of completed stage IDs"
    )

    @model_validator(mode="after")
    def validate_pipeline_state(self) -> PipelineState:
        """Validate pipeline state consistency."""
        for stage_id in self.completed_stages:
            if not (MIN_STAGE_ID <= stage_id <= MAX_STAGE_ID):
                msg = f"completed_stages contains invalid stage_id {stage_id} — must be {MIN_STAGE_ID}-{MAX_STAGE_ID}"
                raise ValueError(msg)

        if self.completed_stages != sorted(set(self.completed_stages)):
            msg = "completed_stages must be sorted and contain no duplicates"
            raise ValueError(msg)

        return self
