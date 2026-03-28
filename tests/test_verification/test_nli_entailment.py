"""Tests for NLI entailment evaluator."""

from __future__ import annotations

import pytest

from ai_architect_mcp._models.verification import (
    ClaimSource,
    ClaimType,
    Verdict,
    VerificationClaim,
)
from ai_architect_mcp._verification.algorithms.nli_entailment import (
    NLIEntailmentEvaluator,
)
from tests.conftest import StubLLMClient


class TestNLIEntailment:
    """Tests for NLIEntailmentEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluate_returns_result(self) -> None:
        """Evaluation with stub client returns valid classification."""
        evaluator = NLIEntailmentEvaluator(client=StubLLMClient())
        claim = VerificationClaim(
            content="The system uses OAuth 2.0",
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.GENERATION,
            priority=50,
        )
        result = await evaluator.evaluate(
            claim, "The system implements authentication"
        )
        assert result.score >= 0.0
        assert result.evaluator_id == "nli_entailment"
        assert result.verdict in (Verdict.PASS, Verdict.INCONCLUSIVE, Verdict.FAIL)

    @pytest.mark.asyncio
    async def test_batch_evaluate(self) -> None:
        """Batch evaluation returns one result per claim."""
        evaluator = NLIEntailmentEvaluator(client=StubLLMClient())
        claims = [
            VerificationClaim(
                content=f"Claim {i}",
                claim_type=ClaimType.ATOMIC_FACT,
                source=ClaimSource.GENERATION,
                priority=50,
            )
            for i in range(3)
        ]
        results = await evaluator.evaluate_batch(claims, "Some premise")
        assert len(results) == 3

    def test_rejects_none_client(self) -> None:
        with pytest.raises(ValueError, match="requires an LLM client"):
            NLIEntailmentEvaluator(client=None)
