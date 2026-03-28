"""Verification tools — claim verification, graph analysis, NLI, debate, consensus."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastmcp import Context

from ai_architect_mcp._adapters.sampling_client import SamplingClient
from ai_architect_mcp._models.consensus import (
    ConsensusAlgorithm,
    ConsensusResult,
    TieBreaker,
)
from ai_architect_mcp._models.graph import ClaimRelationshipGraph
from ai_architect_mcp._models.verification import (
    ClaimEvaluation,
    ClaimSource,
    ClaimType,
    Verdict,
    VerificationClaim,
    VerificationReport,
)
from ai_architect_mcp._verification.algorithms.atomic_claim_decomposer import AtomicClaimDecomposer
from ai_architect_mcp._verification.algorithms.chain_of_verification import ChainOfVerification
from ai_architect_mcp._verification.algorithms.graph_constrained import GraphConstrainedVerifier
from ai_architect_mcp._verification.algorithms.multi_agent_debate import MultiAgentDebate
from ai_architect_mcp._verification.algorithms.nli_entailment import NLIEntailmentEvaluator
from ai_architect_mcp._verification.consensus_router import get_consensus_algorithm
from ai_architect_mcp._app import mcp
from ai_architect_mcp._config.loader import load_config
from ai_architect_mcp._observability.instrumentation import observe_tool_call


def _llm_model() -> str:
    """Get the configured LLM model ID."""
    return load_config().prompting.llm_model


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_verify_claim(
    content: str,
    ctx: Context,
    claim_type: str = "atomic_fact",
    context: str = "",
    priority: int = 50,
) -> dict[str, Any]:
    """Verify a single claim using Chain of Verification.

    Args:
        content: The claim text to verify.
        ctx: FastMCP context (injected) — used for LLM sampling.
        claim_type: Type of claim (atomic_fact, verification_question, etc).
        context: Supporting context for verification.
        priority: Priority from 1-100.

    Returns:
        ClaimEvaluation as a dictionary.
    """
    claim = VerificationClaim(
        content=content,
        claim_type=ClaimType(claim_type),
        source=ClaimSource.GENERATION,
        priority=priority,
    )
    cov = ChainOfVerification(client=SamplingClient(ctx), model=_llm_model())
    result = await cov.verify(claim, context)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_verify_graph(
    graph_data: dict[str, Any],
) -> dict[str, Any]:
    """Verify a claim relationship graph for structural issues.

    Zero LLM calls. Detects cycles, contradictions, and orphans.

    Args:
        graph_data: ClaimRelationshipGraph as a dictionary with:
            nodes (list): Each node requires:
                - node_id (UUID str): Unique node identifier (auto-generated if omitted).
                - claim_id (UUID str): ID of the verification claim.
                - label (str): Human-readable label.
                - node_type (str): One of "requirement", "specification",
                  "implementation", "test", "constraint".
            edges (list): Each edge requires:
                - source_id (UUID str): Must reference an existing node's node_id.
                - target_id (UUID str): Must reference an existing node's node_id.
                - relationship (str): One of "implies", "requires", "implements",
                  "contradicts", "depends", "tests".
                - weight (float): Relationship strength (0.0-1.0).

    Returns:
        VerificationReport as a dictionary with overall_score, evaluations,
        hor_results, claims, algorithm_used, and timestamp.
    """
    graph = ClaimRelationshipGraph.model_validate(graph_data)
    verifier = GraphConstrainedVerifier()
    report = verifier.verify(graph)
    return report.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_evaluate_nli(
    claim_content: str,
    premise: str,
    ctx: Context,
    strict: bool = True,
) -> dict[str, Any]:
    """Evaluate a claim against a premise using NLI classification.

    Classifies the entailment relationship: ENTAILMENT (score 1.0),
    NEUTRAL (0.3 strict / 0.6 lenient), CONTRADICTION (0.0).

    Requires LLM sampling support (ctx.sample). When sampling is
    unavailable, returns an INCONCLUSIVE verdict with NEUTRAL score
    instead of raising an error.

    Args:
        claim_content: The claim to evaluate.
        premise: The context/premise.
        ctx: FastMCP context (injected) — used for LLM sampling.
        strict: If True, NEUTRAL scores 0.3; if False, 0.6.

    Returns:
        ClaimEvaluation as a dictionary with fields:
            claim_id, evaluator_id, score, confidence, verdict, reasoning, evidence.
    """
    claim = VerificationClaim(
        content=claim_content,
        claim_type=ClaimType.NLI_ASSERTION,
        source=ClaimSource.GENERATION,
        priority=50,
    )
    try:
        evaluator = NLIEntailmentEvaluator(client=SamplingClient(ctx), strict=strict, model=_llm_model())
        result = await evaluator.evaluate(claim, premise)
        return result.model_dump(mode="json")
    except Exception as exc:
        # Graceful degradation when sampling is unavailable
        neutral_score = 0.3 if strict else 0.6
        fallback = ClaimEvaluation(
            claim_id=claim.claim_id,
            evaluator_id="nli_entailment",
            score=neutral_score,
            confidence=0.0,
            verdict=Verdict.INCONCLUSIVE,
            reasoning=f"NLI evaluation unavailable: {exc}. Returning NEUTRAL fallback.",
            evidence=[premise[:200]],
        )
        return fallback.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
@observe_tool_call
async def ai_architect_debate_claim(
    content: str,
    ctx: Context,
    num_agents: int = 3,
    max_rounds: int = 3,
) -> dict[str, Any]:
    """Run multi-agent debate on a claim.

    Args:
        content: The claim to debate.
        ctx: FastMCP context (injected) — used for LLM sampling.
        num_agents: Number of debate agents.
        max_rounds: Maximum debate rounds.

    Returns:
        VerificationReport as a dictionary.
    """
    claim = VerificationClaim(
        content=content,
        claim_type=ClaimType.ATOMIC_FACT,
        source=ClaimSource.GENERATION,
        priority=50,
    )
    debate = MultiAgentDebate(client=SamplingClient(ctx), model=_llm_model())
    report = await debate.debate(claim, num_agents=num_agents, max_rounds=max_rounds)
    return report.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_consensus(
    scores: list[float],
    confidences: list[float],
    algorithm: str = "weighted_average",
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    voting_threshold: float = 0.5,
    tie_breaker: str = "highest_confidence",
) -> dict[str, Any]:
    """Run consensus on a set of evaluator scores.

    Args:
        scores: List of evaluator scores.
        confidences: List of evaluator confidences.
        algorithm: Algorithm (weighted_average, adaptive_stability, bayesian, majority_voting).
        prior_alpha: Alpha for Bayesian prior (bayesian only).
        prior_beta: Beta for Bayesian prior (bayesian only).
        voting_threshold: Score threshold for YES vote (majority_voting only).
        tie_breaker: Tie strategy (highest_confidence, random_seeded, escalate_to_debate).

    Returns:
        ConsensusResult as a dictionary.
    """
    from uuid import uuid4

    claim_id = uuid4()
    evaluations = [
        ClaimEvaluation(
            claim_id=claim_id,
            evaluator_id=f"evaluator_{i}",
            score=s,
            confidence=c,
            verdict=Verdict.PASS if s >= 0.6 else Verdict.FAIL,
            reasoning=f"Score: {s}",
        )
        for i, (s, c) in enumerate(zip(scores, confidences))
    ]

    algo_enum = ConsensusAlgorithm(algorithm)
    resolver = get_consensus_algorithm(
        algorithm=algo_enum,
        prior_alpha=prior_alpha,
        prior_beta=prior_beta,
        voting_threshold=voting_threshold,
        tie_breaker=TieBreaker(tie_breaker),
    )
    result = resolver.resolve(evaluations)

    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_decompose_claim(
    content: str,
    priority: int = 50,
) -> list[dict[str, Any]]:
    """Decompose a compound claim into atomic sub-claims.

    Args:
        content: The claim text to decompose.
        priority: Base priority for sub-claims.

    Returns:
        List of atomic VerificationClaim dictionaries.
    """
    claim = VerificationClaim(
        content=content,
        claim_type=ClaimType.ATOMIC_FACT,
        source=ClaimSource.GENERATION,
        priority=priority,
    )
    decomposer = AtomicClaimDecomposer()
    results = await decomposer.decompose(claim)
    return [r.model_dump(mode="json") for r in results]
