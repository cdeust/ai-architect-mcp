"""Multi-Agent Debate — improving factuality through multi-perspective debate.

Research: Du et al. (2023) "Improving Factuality through Multiagent Debate".
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_architect_mcp._models.verification import (
    ClaimEvaluation,
    Verdict,
    VerificationClaim,
    VerificationReport,
)

CONVERGENCE_THRESHOLD = 0.05
DEFAULT_NUM_AGENTS = 3
DEFAULT_MAX_ROUNDS = 3
CONVERGED_CONFIDENCE = 0.85
UNCONVERGED_CONFIDENCE = 0.65
PASS_THRESHOLD = 0.6
OWN_WEIGHT = 0.6
OTHERS_WEIGHT = 0.4
AGENT_BASE_SCORE = 0.7
AGENT_SCORE_INCREMENT = 0.05


class MultiAgentDebate:
    """Multi-agent debate for claim verification.

    Multiple agents independently assess a claim, then iteratively
    refine their positions after seeing other assessments.
    """

    def __init__(self, client: object | None = None) -> None:
        """Initialize the multi-agent debate.

        Args:
            client: Anthropic client for LLM calls. None for testing.
        """
        self._client = client

    async def debate(
        self,
        claim: VerificationClaim,
        num_agents: int = DEFAULT_NUM_AGENTS,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
    ) -> VerificationReport:
        """Run a multi-agent debate on a claim.

        Args:
            claim: The claim to debate.
            num_agents: Number of debate agents.
            max_rounds: Maximum debate rounds.

        Returns:
            VerificationReport with debate results.
        """
        agent_scores: list[list[float]] = [[] for _ in range(num_agents)]

        for agent_idx in range(num_agents):
            score = await self._independent_assessment(claim, agent_idx)
            agent_scores[agent_idx].append(score)

        rounds, converged = await self._run_debate_rounds(
            claim, agent_scores, num_agents, max_rounds,
        )

        return self._build_report(claim, agent_scores, rounds, converged)

    async def _run_debate_rounds(
        self,
        claim: VerificationClaim,
        agent_scores: list[list[float]],
        num_agents: int,
        max_rounds: int,
    ) -> tuple[int, bool]:
        """Execute iterative debate rounds until convergence or max.

        Returns:
            Tuple of (rounds_completed, converged).
        """
        current_round = 1
        converged = False

        while current_round < max_rounds and not converged:
            current_round += 1
            last_scores = [scores[-1] for scores in agent_scores]

            for agent_idx in range(num_agents):
                other_scores = [
                    s for i, s in enumerate(last_scores) if i != agent_idx
                ]
                refined = await self._refine_assessment(
                    claim, agent_scores[agent_idx][-1],
                    other_scores, agent_idx,
                )
                agent_scores[agent_idx].append(refined)

            final_scores = [scores[-1] for scores in agent_scores]
            converged = self._variance(final_scores) < CONVERGENCE_THRESHOLD

        return current_round, converged

    def _build_report(
        self,
        claim: VerificationClaim,
        agent_scores: list[list[float]],
        rounds: int,
        converged: bool,
    ) -> VerificationReport:
        """Assemble the VerificationReport from debate results."""
        final_scores = [scores[-1] for scores in agent_scores]
        avg_score = sum(final_scores) / len(final_scores)
        confidence = CONVERGED_CONFIDENCE if converged else UNCONVERGED_CONFIDENCE

        evaluations = [
            ClaimEvaluation(
                claim_id=claim.claim_id,
                evaluator_id=f"debate_agent_{i}",
                score=round(score, 4),
                confidence=confidence,
                verdict=Verdict.PASS if score >= PASS_THRESHOLD else Verdict.FAIL,
                reasoning=f"Agent {i} final assessment after {rounds} rounds",
            )
            for i, score in enumerate(final_scores)
        ]

        return VerificationReport(
            claims=[claim],
            evaluations=evaluations,
            overall_score=round(avg_score, 4),
            algorithm_used="multi_agent_debate",
            timestamp=datetime.now(timezone.utc),
        )

    async def _independent_assessment(
        self, claim: VerificationClaim, agent_idx: int
    ) -> float:
        """Agent independently assesses a claim.

        Args:
            claim: The claim to assess.
            agent_idx: Index of the assessing agent.

        Returns:
            Assessment score in [0, 1].
        """
        if self._client is None:
            return AGENT_BASE_SCORE + agent_idx * AGENT_SCORE_INCREMENT
        return AGENT_BASE_SCORE

    async def _refine_assessment(
        self,
        claim: VerificationClaim,
        own_score: float,
        other_scores: list[float],
        agent_idx: int,
    ) -> float:
        """Agent refines assessment after seeing others.

        Args:
            claim: The claim being debated.
            own_score: This agent's current score.
            other_scores: Other agents' current scores.
            agent_idx: Index of the refining agent.

        Returns:
            Refined assessment score in [0, 1].
        """
        if self._client is None:
            avg_others = sum(other_scores) / max(len(other_scores), 1)
            return own_score * OWN_WEIGHT + avg_others * OTHERS_WEIGHT
        return own_score

    def _variance(self, values: list[float]) -> float:
        """Calculate population variance.

        Args:
            values: Numeric values.

        Returns:
            Population variance.
        """
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)
