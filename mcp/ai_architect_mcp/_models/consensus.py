"""Consensus models — agreement levels, resolution strategies, and results.

Models for consensus algorithms that aggregate multiple evaluator scores
into a single agreement result. Used by weighted average, adaptive
stability, Bayesian, and majority voting consensus methods.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

AGREEMENT_HIGH_THRESHOLD = 0.05
AGREEMENT_MEDIUM_THRESHOLD = 0.15
DEFAULT_VOTING_THRESHOLD = 0.5
DEFAULT_PRIOR_ALPHA = 1.0
DEFAULT_PRIOR_BETA = 1.0


class AgreementLevel(str, Enum):
    """Agreement level based on score variance.

    HIGH: variance < 0.05
    MEDIUM: variance < 0.15
    LOW: variance >= 0.15
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DisagreementResolution(str, Enum):
    """Strategy for resolving disagreements between evaluators."""

    ACCEPT = "accept"
    REJECT = "reject"
    FLAG_FOR_REVIEW = "flag_for_review"
    RE_EVALUATE = "re_evaluate"


class TieBreaker(str, Enum):
    """Strategy for breaking ties in majority voting.

    HIGHEST_CONFIDENCE: select the side with higher average confidence.
    RANDOM_SEEDED: use SHA-256 seeded RNG for deterministic tie-breaking.
    ESCALATE_TO_DEBATE: flag the claim for multi-agent debate review.
    """

    HIGHEST_CONFIDENCE = "highest_confidence"
    RANDOM_SEEDED = "random_seeded"
    ESCALATE_TO_DEBATE = "escalate_to_debate"


class ConsensusAlgorithm(str, Enum):
    """Available consensus algorithms.

    All four algorithms are fully implemented:
    - WEIGHTED_AVERAGE: confidence-weighted score averaging
    - ADAPTIVE_STABILITY: KS test convergence detection
    - BAYESIAN: Beta-Binomial posterior updating
    - MAJORITY_VOTING: threshold-based majority decision
    """

    WEIGHTED_AVERAGE = "weighted_average"
    ADAPTIVE_STABILITY = "adaptive_stability"
    BAYESIAN = "bayesian"
    MAJORITY_VOTING = "majority_voting"


class ConsensusResult(BaseModel):
    """Result of running a consensus algorithm on multiple evaluations.

    Produced when multiple evaluators assess the same claim and their
    scores need to be aggregated into a single consensus.
    """

    algorithm: ConsensusAlgorithm = Field(description="Which consensus algorithm produced this result")
    consensus_score: float = Field(ge=0.0, le=1.0, description="Aggregated consensus score (0.0-1.0)")
    consensus_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the consensus (0.0-1.0)")
    agreement_level: AgreementLevel = Field(description="Level of agreement among evaluators")
    resolution: DisagreementResolution = Field(description="How disagreements were resolved")
    individual_scores: list[float] = Field(description="Original scores from each evaluator")
    iteration_count: int = Field(ge=1, description="Number of consensus iterations performed")
    converged: bool = Field(description="Whether the consensus algorithm converged")
