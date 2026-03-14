"""Finding — atomic unit flowing through all 11 pipeline stages.

A Finding represents a single signal detected during Stage 1 (Discovery)
that flows through the pipeline, accumulating artifacts at each stage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SourceCategory(str, Enum):
    """Source categories for finding origin classification.

    Each category represents a major AI research organization or
    internal source from which findings can originate.
    """

    AMAZON_AWS = "amazon_aws"
    ANTHROPIC = "anthropic"
    APPLE = "apple"
    COHERE = "cohere"
    GOOGLE_DEEPMIND = "google_deepmind"
    HUGGING_FACE = "hugging_face"
    META_FAIR = "meta_fair"
    MICROSOFT = "microsoft"
    MOONSHOT_01AI = "moonshot_01ai"
    SAKANA_ALEPH_ALPHA = "sakana_aleph_alpha"
    SAMSUNG = "samsung"
    STABILITY_MIDJOURNEY = "stability_midjourney"
    TOGETHER_FIREWORKS = "together_fireworks"
    INTERNAL = "internal"


class Severity(str, Enum):
    """Severity levels for findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(BaseModel):
    """Atomic unit flowing through all 11 pipeline stages.

    A Finding is created in Stage 1 (Discovery) and accumulates
    artifacts as it progresses through the pipeline. Each stage
    reads the finding and writes its stage-specific output.
    """

    finding_id: str = Field(
        description="Unique identifier for the finding (e.g., FIND-001)"
    )
    title: str = Field(
        description="Short descriptive title summarizing the finding"
    )
    description: str = Field(
        description="Detailed description of the finding and its implications"
    )
    source_category: SourceCategory = Field(
        description="Origin category of the finding from the 14 source categories"
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance score from 0.0 (irrelevant) to 1.0 (critical)"
    )
    severity: Severity = Field(
        description="Severity level of the finding"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the finding was created"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional key-value metadata for the finding"
    )

    @model_validator(mode="after")
    def validate_title_and_description(self) -> Finding:
        """Ensure title and description are non-empty."""
        if not self.title.strip():
            msg = "Finding title must not be empty — provide a descriptive title summarizing the signal"
            raise ValueError(msg)
        if not self.description.strip():
            msg = "Finding description must not be empty — describe the finding and its implications"
            raise ValueError(msg)
        return self
