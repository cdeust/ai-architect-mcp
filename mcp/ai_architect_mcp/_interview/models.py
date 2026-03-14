"""Data models for the Plan Interview stage (4.5).

Defines dimension types, gate decisions, scoring results,
configuration, and the top-level interview result.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class DimensionType(str, Enum):
    """The 10 evaluation dimensions for PRD quality."""

    D1_SECTIONS_PRESENT = "D1_SECTIONS_PRESENT"
    D2_HEADER_FORMAT = "D2_HEADER_FORMAT"
    D3_ID_CONSISTENCY = "D3_ID_CONSISTENCY"
    D4_OUTLINE_FLOW = "D4_OUTLINE_FLOW"
    D5_ARTIFACT_COHERENCE = "D5_ARTIFACT_COHERENCE"
    D6_CLARITY_LEVEL = "D6_CLARITY_LEVEL"
    D7_STAKEHOLDER_ALIGNMENT = "D7_STAKEHOLDER_ALIGNMENT"
    D8_REQUIREMENT_PRECISION = "D8_REQUIREMENT_PRECISION"
    D9_ASSUMPTION_VALIDATION = "D9_ASSUMPTION_VALIDATION"
    D10_SUCCESS_METRICS = "D10_SUCCESS_METRICS"


class GateDecision(str, Enum):
    """Possible outcomes of the Plan Interview gate."""

    APPROVED = "APPROVED"
    PROVISIONAL = "PROVISIONAL"
    REJECTED = "REJECTED"


class DimensionScore(BaseModel):
    """Score for a single evaluation dimension."""

    dimension_type: DimensionType = Field(
        description="Which of the 10 dimensions this score covers.",
    )
    dimension_name: str = Field(
        description="Human-readable name of the dimension.",
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalised score from 0.0 (worst) to 1.0 (best).",
    )
    passed: bool = Field(
        description="Whether this dimension met its pass threshold.",
    )
    findings: list[str] = Field(
        default_factory=list,
        description="Diagnostic messages explaining the score.",
    )


class InterviewConfig(BaseModel):
    """Tunable thresholds for the interview gate."""

    critical_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum score for critical dimensions to pass.",
    )
    advisory_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum score for advisory dimensions to pass.",
    )
    timeout_seconds: int = Field(
        default=60,
        gt=0,
        description="Maximum wall-clock seconds before the interview aborts.",
    )


class InterviewResult(BaseModel):
    """Complete output of a Plan Interview run."""

    finding_id: str = Field(
        description="Identifier linking this result to a pipeline finding.",
    )
    stage_id: int = Field(
        default=45,
        description="Pipeline stage number (always 45 for Plan Interview).",
    )
    dimension_scores: list[DimensionScore] = Field(
        description="Score for every evaluated dimension.",
    )
    gate_decision: GateDecision = Field(
        description="Overall gate decision derived from dimension scores.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the interview completed.",
    )

    @model_validator(mode="after")
    def _validate_non_empty_scores(self) -> InterviewResult:
        """Ensure at least one dimension score is present."""
        if not self.dimension_scores:
            msg = (
                "dimension_scores must not be empty — "
                "run at least one scorer before creating an InterviewResult"
            )
            raise ValueError(msg)
        return self
