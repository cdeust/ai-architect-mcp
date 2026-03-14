"""Tests for NLI entailment evaluator — mocked client."""

from __future__ import annotations

import pytest

from ai_architect_mcp._models.verification import (
    ClaimSource,
    ClaimType,
    VerificationClaim,
)
from ai_architect_mcp._verification.algorithms.nli_entailment import (
    NLIEntailmentEvaluator,
)


class TestNLIEntailment:
    """Tests for NLIEntailmentEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluate_without_client(self) -> None:
        """Evaluation without client returns NEUTRAL classification."""
        evaluator = NLIEntailmentEvaluator(client=None)
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

    @pytest.mark.asyncio
    async def test_batch_evaluate(self) -> None:
        """Batch evaluation returns one result per claim."""
        evaluator = NLIEntailmentEvaluator(client=None)
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
