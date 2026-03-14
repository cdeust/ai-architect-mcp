"""Verification models — claims, evaluations, HOR rules, and reports.

Models used by the 5 verification algorithms and 64 HOR rules in the
verification engine. Claims flow through decomposition, evaluation,
and consensus to produce a VerificationReport.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class ClaimType(str, Enum):
    """Type classification for verification claims."""

    VERIFICATION_QUESTION = "verification_question"
    ATOMIC_FACT = "atomic_fact"
    NLI_ASSERTION = "nli_assertion"
    GRAPH_NODE = "graph_node"


class ClaimSource(str, Enum):
    """Origin of a verification claim in the pipeline."""

    GENERATION = "generation"
    DECOMPOSITION = "decomposition"
    REFINEMENT = "refinement"


class Verdict(str, Enum):
    """Verification verdict for a claim evaluation."""

    PASS = "pass"
    SPEC_COMPLETE = "spec_complete"
    NEEDS_RUNTIME = "needs_runtime"
    INCONCLUSIVE = "inconclusive"
    FAIL = "fail"


PENALTY_CRITICAL = 0.15
PENALTY_WARNING = 0.05


class HORSeverity(str, Enum):
    """Severity levels for HOR rule violations."""

    CRITICAL = "critical"
    WARNING = "warning"


class VerificationClaim(BaseModel):
    """A single claim to be verified by the verification engine.

    Claims are atomic, self-contained assertions that can be independently
    evaluated. They are produced by decomposition of complex statements.
    """

    claim_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this claim",
    )
    content: str = Field(
        description="The claim text to be verified",
    )
    claim_type: ClaimType = Field(
        description="Classification of the claim type",
    )
    source: ClaimSource = Field(
        description="How this claim was produced",
    )
    context: str | None = Field(
        default=None,
        description="Optional context needed to evaluate the claim",
    )
    priority: int = Field(
        ge=1,
        le=100,
        description="Priority from 1 (lowest) to 100 (highest)",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional metadata for the claim",
    )


class ClaimEvaluation(BaseModel):
    """Result of evaluating a single claim by one evaluator.

    Each evaluator produces one ClaimEvaluation per claim. Multiple
    evaluations are aggregated by consensus algorithms.
    """

    claim_id: UUID = Field(
        description="ID of the claim that was evaluated",
    )
    evaluator_id: str = Field(
        description="Identifier of the evaluator that produced this result",
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Evaluation score from 0.0 (fail) to 1.0 (pass)",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the evaluation from 0.0 to 1.0",
    )
    verdict: Verdict = Field(
        description="Categorical verdict for this evaluation",
    )
    reasoning: str = Field(
        description="Explanation of why this verdict was reached",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Supporting evidence for the verdict",
    )


class HORRuleResult(BaseModel):
    """Result of running a single HOR (Higher-Order Reasoning) rule.

    Each of the 64 HOR rules produces a binary pass/fail result.
    Critical failures apply a 0.15 penalty, warnings apply 0.05.
    """

    rule_id: int = Field(
        ge=1,
        le=64,
        description="HOR rule number (1-64)",
    )
    rule_name: str = Field(
        description="Human-readable name of the rule",
    )
    category: str = Field(
        description="Category grouping (structural, architecture, security, etc.)",
    )
    passed: bool = Field(
        description="Whether the rule check passed",
    )
    message: str = Field(
        description="Explanation of the result",
    )
    severity: HORSeverity = Field(
        description="Severity level: critical (0.15 penalty) or warning (0.05 penalty)",
    )
    penalty: float = Field(
        description="Score penalty to apply if rule failed (0.15 critical, 0.05 warning)",
    )

    @model_validator(mode="after")
    def validate_penalty(self) -> HORRuleResult:
        """Ensure penalty matches severity.

        Returns:
            The validated HORRuleResult instance.

        Raises:
            ValueError: If penalty does not match the expected value for the severity.
        """
        expected = (
            PENALTY_CRITICAL
            if self.severity == HORSeverity.CRITICAL
            else PENALTY_WARNING
        )
        if abs(self.penalty - expected) > 1e-10:
            msg = (
                f"Penalty {self.penalty} does not match severity "
                f"{self.severity.value} — expected {expected}"
            )
            raise ValueError(msg)
        return self


class VerificationReport(BaseModel):
    """Complete verification report for a finding or PRD.

    Aggregates all claim evaluations, HOR rule results, and produces
    an overall score. Used as the Stage 7 output artifact.
    """

    claims: list[VerificationClaim] = Field(
        default_factory=list,
        description="All claims that were verified",
    )
    evaluations: list[ClaimEvaluation] = Field(
        default_factory=list,
        description="All individual claim evaluations",
    )
    hor_results: list[HORRuleResult] = Field(
        default_factory=list,
        description="Results from all 64 HOR rules",
    )
    overall_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Aggregate verification score (0.0-1.0)",
    )
    algorithm_used: str = Field(
        description="Name of the verification algorithm that produced this report",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this report was generated",
    )
