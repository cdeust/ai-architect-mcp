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
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class MultiAgentDebate:
    """Multi-agent debate for claim verification.

    Multiple agents independently assess a claim, then iteratively
    refine their positions after seeing other assessments.
    """

    def __init__(self, client: object, model: str = DEFAULT_MODEL) -> None:
        """Initialize the multi-agent debate.

        Args:
            client: Anthropic client for LLM calls.
            model: Model ID for LLM calls.
        """
        if client is None:
            raise ValueError(
                "MultiAgentDebate requires an LLM client. "
                "Provide a Claude CLI client or AsyncAnthropic instance."
            )
        self._client = client
        self._model = model

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
        personas = [
            "You are a skeptical analyst. Look for flaws and weaknesses.",
            "You are a supportive analyst. Look for strengths and merit.",
            "You are a neutral analyst. Weigh evidence impartially.",
        ]
        persona = personas[agent_idx % len(personas)]

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=50,
                temperature=0.3 + (agent_idx * 0.1),
                system=(
                    f"{persona} Rate the claim's validity from 0.0 to 1.0. "
                    "Respond with only a number."
                ),
                messages=[{
                    "role": "user",
                    "content": f"Claim: {claim.content}",
                }],
            )
            text = response.content[0].text.strip()
            score = float(text.split()[0].strip(".,;:"))
            return max(0.0, min(1.0, score))
        except (AttributeError, IndexError, TypeError, ValueError):
            return 0.5
        except Exception:
            return 0.5

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
        other_summary = ", ".join(f"{s:.2f}" for s in other_scores)
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=50,
                temperature=0.1,
                system=(
                    "You previously scored a claim. Other agents scored differently. "
                    "Reconsider and provide a revised score (0.0-1.0). "
                    "Respond with only a number."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Claim: {claim.content}\n"
                        f"Your previous score: {own_score:.2f}\n"
                        f"Other agents' scores: {other_summary}"
                    ),
                }],
            )
            text = response.content[0].text.strip()
            score = float(text.split()[0].strip(".,;:"))
            return max(0.0, min(1.0, score))
        except (AttributeError, IndexError, TypeError, ValueError):
            avg_others = sum(other_scores) / max(len(other_scores), 1)
            return own_score * OWN_WEIGHT + avg_others * OTHERS_WEIGHT
        except Exception:
            avg_others = sum(other_scores) / max(len(other_scores), 1)
            return own_score * OWN_WEIGHT + avg_others * OTHERS_WEIGHT

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
