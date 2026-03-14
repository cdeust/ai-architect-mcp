"""Foundation models — Pydantic v2 types shared across all pipeline stages.

All models use Pydantic v2 BaseModel with strict validation. Every field
has a description. Every model round-trips through model_dump/model_validate.
"""

from __future__ import annotations

from ai_architect_mcp._models.consensus import (
    AgreementLevel,
    ConsensusAlgorithm,
    ConsensusResult,
    DisagreementResolution,
    TieBreaker,
)
from ai_architect_mcp._models.finding import Finding, Severity, SourceCategory
from ai_architect_mcp._models.graph import (
    ClaimGraphEdge,
    ClaimGraphNode,
    ClaimRelationshipGraph,
    NodeType,
    RelationshipType,
    ThoughtEdge,
    ThoughtGraph,
    ThoughtNode,
)
from ai_architect_mcp._models.pipeline import (
    PipelineState,
    StageOutput,
    StageStatus,
)
from ai_architect_mcp._models.prompting import (
    ConfidenceEstimate,
    EnhancedPrompt,
    EnhancementSource,
    FusedConfidence,
    StrategySelection,
    ThinkingStrategy,
)
from ai_architect_mcp._models.scoring import (
    CompoundScore,
    ImpactReport,
    PropagationPath,
    Recommendation,
    RiskLevel,
)
from ai_architect_mcp._models.audit_event import AuditEvent, AuditOutcome, AuditQuery
from ai_architect_mcp._models.disclosure import ContextBudget, DisclosureLevel
from ai_architect_mcp._models.experience_pattern import ExperiencePattern, PatternType
from ai_architect_mcp._models.session_state import PipelineStatus, SessionState
from ai_architect_mcp._models.verification import (
    ClaimEvaluation,
    ClaimSource,
    ClaimType,
    HORRuleResult,
    HORSeverity,
    Verdict,
    VerificationClaim,
    VerificationReport,
)

__all__ = [
    "AgreementLevel",
    "AuditEvent",
    "AuditOutcome",
    "AuditQuery",
    "ContextBudget",
    "DisclosureLevel",
    "ExperiencePattern",
    "ClaimEvaluation",
    "ClaimGraphEdge",
    "ClaimGraphNode",
    "ClaimRelationshipGraph",
    "ClaimSource",
    "ClaimType",
    "CompoundScore",
    "ConfidenceEstimate",
    "ConsensusAlgorithm",
    "ConsensusResult",
    "DisagreementResolution",
    "TieBreaker",
    "EnhancedPrompt",
    "EnhancementSource",
    "Finding",
    "FusedConfidence",
    "HORRuleResult",
    "HORSeverity",
    "ImpactReport",
    "NodeType",
    "PatternType",
    "PipelineState",
    "PipelineStatus",
    "PropagationPath",
    "Recommendation",
    "RelationshipType",
    "RiskLevel",
    "SessionState",
    "Severity",
    "SourceCategory",
    "StageOutput",
    "StageStatus",
    "StrategySelection",
    "ThinkingStrategy",
    "ThoughtEdge",
    "ThoughtGraph",
    "ThoughtNode",
    "Verdict",
    "VerificationClaim",
    "VerificationReport",
]
