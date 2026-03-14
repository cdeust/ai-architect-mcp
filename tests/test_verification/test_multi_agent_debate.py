"""Tests for multi-agent debate."""

from __future__ import annotations

import pytest

from ai_architect_mcp._models.verification import (
    ClaimSource,
    ClaimType,
    VerificationClaim,
)
from ai_architect_mcp._verification.algorithms.multi_agent_debate import (
    MultiAgentDebate,
)


class TestMultiAgentDebate:
    """Tests for MultiAgentDebate.debate."""

    @pytest.mark.asyncio
    async def test_debate_converges(self) -> None:
        """Debate with mock client converges to consensus."""
        debate = MultiAgentDebate(client=None)
        claim = VerificationClaim(
            content="Test claim",
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.GENERATION,
            priority=50,
        )
        report = await debate.debate(claim, num_agents=3, max_rounds=3)
        assert report.algorithm_used == "multi_agent_debate"
        assert len(report.evaluations) == 3
        assert report.overall_score > 0.0

    @pytest.mark.asyncio
    async def test_round_count(self) -> None:
        """Debate with 2 agents and 2 rounds produces valid report."""
        debate = MultiAgentDebate(client=None)
        claim = VerificationClaim(
            content="Test",
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.GENERATION,
            priority=50,
        )
        report = await debate.debate(claim, num_agents=2, max_rounds=2)
        assert report.overall_score > 0.0
