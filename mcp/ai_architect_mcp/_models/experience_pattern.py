"""Experience pattern model — biological decay for learned patterns.

Patterns capture recurring successes, failures, and optimizations observed
during pipeline execution. Relevance decays exponentially over time using
a configurable half-life, ensuring stale patterns fade while recent
observations remain prominent.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

MIN_STAGE: int = 0
MAX_STAGE: int = 10
REINFORCEMENT_BOOST: float = 0.05


class PatternType(str, Enum):
    """Classification of an experience pattern."""

    SUCCESS = "success"
    FAILURE = "failure"
    OPTIMIZATION = "optimization"
    REGRESSION = "regression"
    ANOMALY = "anomaly"


class ExperiencePattern(BaseModel):
    """A learned pattern with biological relevance decay.

    Relevance decreases exponentially with a configurable half-life.
    Patterns can be reinforced when re-observed, boosting their
    initial relevance and resetting the decay clock.

    Attributes:
        pattern_id: Unique identifier for this pattern.
        pattern_type: Classification of what this pattern represents.
        description: Human-readable summary of the pattern.
        stage_id: Pipeline stage where this pattern was observed (0-10).
        initial_relevance: Starting relevance before decay (0.0-1.0).
        half_life_days: Days until relevance halves.
        occurrence_count: Number of times this pattern has been seen.
        created_at: UTC timestamp of first observation.
        last_seen_at: UTC timestamp of most recent observation.
        tags: Free-form labels for filtering.
    """

    pattern_id: str = Field(description="Unique identifier for this pattern")
    pattern_type: PatternType = Field(description="Classification of the pattern")
    description: str = Field(description="Human-readable pattern summary")
    stage_id: int = Field(
        ge=MIN_STAGE, le=MAX_STAGE, description="Pipeline stage where observed (0-10)"
    )
    initial_relevance: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Starting relevance before decay"
    )
    half_life_days: float = Field(
        default=30.0, gt=0.0, description="Days until relevance halves"
    )
    occurrence_count: int = Field(
        default=1, ge=1, description="Number of times observed"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of first observation",
    )
    last_seen_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of most recent observation",
    )
    tags: list[str] = Field(default_factory=list, description="Free-form labels")

    def current_relevance(self, now: datetime | None = None) -> float:
        """Calculate current relevance after exponential decay.

        Args:
            now: Reference time for decay calculation. Defaults to UTC now.

        Returns:
            Decayed relevance value between 0.0 and initial_relevance.
        """
        reference = now or datetime.now(timezone.utc)
        elapsed = (reference - self.last_seen_at).total_seconds()
        elapsed_days = elapsed / 86400.0
        return self.initial_relevance * math.pow(0.5, elapsed_days / self.half_life_days)

    def reinforce(self) -> ExperiencePattern:
        """Create a reinforced copy with boosted relevance and updated timestamp.

        Returns:
            New ExperiencePattern with incremented count and boosted relevance.
        """
        new_count = self.occurrence_count + 1
        boosted = min(
            1.0, self.initial_relevance * (1.0 + new_count * REINFORCEMENT_BOOST)
        )
        return self.model_copy(
            update={
                "initial_relevance": boosted,
                "occurrence_count": new_count,
                "last_seen_at": datetime.now(timezone.utc),
            }
        )
