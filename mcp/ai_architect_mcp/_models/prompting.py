"""Prompting models — strategies, selections, enhanced prompts, and confidence.

Models for the 5 prompting enhancement algorithms and 16 thinking strategies.
Each strategy traces to its research paper and institution.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EnhancementSource(str, Enum):
    """Source of a confidence estimate from enhancement algorithms."""

    THOUGHT_BUFFER = "thought_buffer"
    ADAPTIVE_EXPANSION = "adaptive_expansion"
    COLLABORATIVE_INFERENCE = "collaborative_inference"
    METACOGNITIVE = "metacognitive"
    TRM_REFINEMENT = "trm_refinement"


class ThinkingStrategy(BaseModel):
    """A thinking strategy backed by research evidence.

    Each strategy maps to a specific research paper and institution,
    with measured improvement claims and applicable characteristics.
    """

    strategy_id: str = Field(description="Unique identifier (e.g., recursive_refinement)")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="What this strategy does and when to use it")
    research_paper: str = Field(description="Reference to the research paper backing this strategy")
    research_institution: str = Field(description="Institution that published the research")
    year: int = Field(ge=2020, le=2026, description="Publication year")
    improvement_claim: str = Field(description="Measured improvement claim (e.g., +32% MATH-500)")
    confidence_interval: tuple[float, float] | None = Field(default=None, description="95% confidence interval for the improvement claim")
    tier: int = Field(ge=1, le=4, description="Strategy tier (1=highest weight, 4=lowest)")
    weight: float = Field(ge=0.0, le=1.0, description="Tier-based weight (T1=1.0, T2=0.7, T3=0.4, T4=0.2)")
    applicable_characteristics: list[str] = Field(description="Problem characteristics this strategy handles well")


class StrategySelection(BaseModel):
    """Result of selecting a thinking strategy for a problem.

    The strategy registry scores each strategy against problem
    characteristics and returns the best match with alternatives.
    """

    selected: ThinkingStrategy = Field(description="The selected thinking strategy")
    reason: str = Field(description="Why this strategy was selected")
    score: float = Field(ge=0.0, description="Selection score")
    alternatives: list[ThinkingStrategy] = Field(default_factory=list, description="Top-3 alternative strategies considered")


class EnhancedPrompt(BaseModel):
    """Result of enhancing a prompt with a thinking strategy.

    Contains both the original and enhanced versions, along with
    metadata about the enhancement process.
    """

    original: str = Field(description="The original prompt before enhancement")
    enhanced: str = Field(description="The enhanced prompt after applying the strategy")
    strategy_used: str = Field(description="ID of the strategy that was applied")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the enhancement quality")
    iterations: int = Field(ge=1, description="Number of enhancement iterations performed")


class ConfidenceEstimate(BaseModel):
    """A single confidence estimate from one enhancement source.

    Multiple estimates are fused by the ConfidenceFusionEngine.
    """

    source: EnhancementSource = Field(description="Which algorithm produced this estimate")
    value: float = Field(ge=0.0, le=1.0, description="Confidence value (0.0-1.0)")
    uncertainty: float = Field(ge=0.0, description="Uncertainty in the estimate")
    reasoning: str = Field(description="Explanation of how the confidence was calculated")


class FusedConfidence(BaseModel):
    """Result of fusing multiple confidence estimates.

    Combines estimates from different sources into a single
    point estimate with confidence bounds.
    """

    point: float = Field(ge=0.0, le=1.0, description="Fused point estimate")
    lower: float = Field(ge=0.0, le=1.0, description="Lower confidence bound")
    upper: float = Field(ge=0.0, le=1.0, description="Upper confidence bound")
    contributing_estimates: list[ConfidenceEstimate] = Field(description="All estimates that were fused")
    fusion_method: str = Field(description="Method used for fusion (e.g., weighted_average)")
