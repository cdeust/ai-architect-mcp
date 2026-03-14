"""Tests for chain of verification."""

from __future__ import annotations

import pytest

from ai_architect_mcp._models.verification import (
    ClaimSource,
    ClaimType,
    VerificationClaim,
)
from ai_architect_mcp._verification.algorithms.chain_of_verification import (
    ChainOfVerification,
)


class TestChainOfVerification:
    """Tests for ChainOfVerification.verify."""

    @pytest.mark.asyncio
    async def test_verify(self) -> None:
        """Verification produces valid evaluation with evidence."""
        cov = ChainOfVerification(client=None)
        claim = VerificationClaim(
            content="Test claim",
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.GENERATION,
            priority=50,
        )
        result = await cov.verify(claim, "Some context")
        assert result.evaluator_id == "chain_of_verification"
        assert result.score >= 0.0
        assert len(result.evidence) > 0
