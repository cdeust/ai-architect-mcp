"""Tests for atomic claim decomposer."""

from __future__ import annotations

import pytest

from ai_architect_mcp._models.verification import (
    ClaimSource,
    ClaimType,
    VerificationClaim,
)
from ai_architect_mcp._verification.algorithms.atomic_claim_decomposer import (
    AtomicClaimDecomposer,
)


class TestAtomicClaimDecomposer:
    """Tests for AtomicClaimDecomposer."""

    @pytest.mark.asyncio
    async def test_atomic_stays_intact(self) -> None:
        """An already-atomic claim is returned unchanged."""
        decomposer = AtomicClaimDecomposer(client=None)
        claim = VerificationClaim(
            content="The system is secure",
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.GENERATION,
            priority=50,
        )
        results = await decomposer.decompose(claim)
        assert len(results) == 1
        assert results[0].content == "The system is secure"

    @pytest.mark.asyncio
    async def test_compound_splits(self) -> None:
        """A compound claim with 'and' is split into parts."""
        decomposer = AtomicClaimDecomposer(client=None)
        claim = VerificationClaim(
            content=(
                "The system is secure and it supports OAuth 2.0"
                " and it handles rate limiting"
            ),
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.GENERATION,
            priority=50,
        )
        results = await decomposer.decompose(claim)
        assert len(results) > 1

    def test_is_atomic_simple(self) -> None:
        """Simple claims are atomic, compound claims are not."""
        decomposer = AtomicClaimDecomposer()
        assert decomposer.is_atomic("The system is secure") is True
        assert decomposer.is_atomic("The system is secure and fast") is False

    @pytest.mark.asyncio
    async def test_priority_parsing(self) -> None:
        """Priority annotations are parsed from claim text."""
        decomposer = AtomicClaimDecomposer(client=None)
        claim = VerificationClaim(
            content=(
                "[PRIORITY:80] First claim"
                " and [PRIORITY:90] second claim"
            ),
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.GENERATION,
            priority=50,
        )
        results = await decomposer.decompose(claim)
        assert len(results) >= 2
