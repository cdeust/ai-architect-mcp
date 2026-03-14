"""Scoring models — compound scores, propagation paths, and impact reports.

Used by the scoring engine in Stage 2 (Impact Analysis) and Stage 5 (Review).
All scoring is deterministic — no LLM calls.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

SCORE_MIN = 0.0
SCORE_MAX = 1.0
WEIGHT_TOLERANCE = 1e-6


class RiskLevel(str, Enum):
    """Risk classification for impact assessment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Recommendation(str, Enum):
    """Action recommendation based on impact assessment."""

    PROCEED = "proceed"
    REVIEW = "review"
    REJECT = "reject"


class CompoundScore(BaseModel):
    """Multi-signal compound score aggregation.

    Combines relevance, uniqueness, impact, and confidence scores
    using configurable weights to produce a weighted total.
    """

    relevance: float = Field(ge=SCORE_MIN, le=SCORE_MAX, description="Relevance score (0.0-1.0)")
    uniqueness: float = Field(ge=SCORE_MIN, le=SCORE_MAX, description="Uniqueness score (0.0-1.0)")
    impact: float = Field(ge=SCORE_MIN, le=SCORE_MAX, description="Impact score (0.0-1.0)")
    confidence: float = Field(ge=SCORE_MIN, le=SCORE_MAX, description="Confidence score (0.0-1.0)")
    weighted_total: float = Field(ge=SCORE_MIN, le=SCORE_MAX, description="Computed weighted total score")
    weights: dict[str, float] = Field(description="Weight for each score component — must sum to 1.0")

    @model_validator(mode="after")
    def validate_weights(self) -> CompoundScore:
        """Ensure weights sum to 1.0 and all scores are in range."""
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > WEIGHT_TOLERANCE:
            msg = f"Weights must sum to 1.0, got {weight_sum} — adjust weights so they total exactly 1.0"
            raise ValueError(msg)
        return self


class PropagationPath(BaseModel):
    """A single path through the dependency graph showing impact propagation."""

    source_module: str = Field(description="Module where the change originates")
    target_modules: list[str] = Field(description="Modules affected along this path")
    propagation_type: str = Field(description="Type of propagation (direct, transitive, interface)")
    depth: int = Field(ge=1, description="Depth of propagation from source")


class ImpactReport(BaseModel):
    """Complete impact assessment for a finding.

    Produced by Stage 2 (Impact Analysis). Combines compound scoring
    with dependency graph propagation analysis.
    """

    finding_id: str = Field(description="ID of the finding being assessed")
    compound_score: CompoundScore = Field(description="Multi-signal compound score")
    propagation_paths: list[PropagationPath] = Field(default_factory=list, description="Impact propagation paths through the dependency graph")
    affected_modules: list[str] = Field(default_factory=list, description="All modules affected by this finding")
    risk_level: RiskLevel = Field(description="Overall risk classification")
    recommendation: Recommendation = Field(description="Action recommendation based on assessment")
