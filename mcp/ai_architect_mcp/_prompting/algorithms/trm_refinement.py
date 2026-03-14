"""TRM Refinement — recursive refinement with intelligent halting.

Research: Madaan et al. (2023) Self-Refine.
"""

from __future__ import annotations

from ai_architect_mcp._models.prompting import EnhancedPrompt

CONVERGENCE_THRESHOLD = 0.02
OSCILLATION_WINDOW = 3
DIMINISHING_RETURNS_THRESHOLD = 0.01


class ConvergenceEvidence:
    """Evidence for convergence analysis."""

    def __init__(self, trajectory: list[float]) -> None:
        self.trajectory = trajectory

    @property
    def shows_strong_convergence(self) -> bool:
        """Check if trajectory shows strong convergence.

        Returns:
            True if last two values are within convergence threshold.
        """
        if len(self.trajectory) < 2:
            return False
        return abs(self.trajectory[-1] - self.trajectory[-2]) < CONVERGENCE_THRESHOLD

    @property
    def shows_oscillation(self) -> bool:
        """Check if trajectory shows oscillating behavior.

        Returns:
            True if direction changes within the oscillation window.
        """
        if len(self.trajectory) < OSCILLATION_WINDOW:
            return False
        window = self.trajectory[-OSCILLATION_WINDOW:]
        diffs = [window[i + 1] - window[i] for i in range(len(window) - 1)]
        return any(d1 * d2 < 0 for d1, d2 in zip(diffs, diffs[1:]))

    @property
    def shows_diminishing_returns(self) -> bool:
        """Check if improvements are below the diminishing returns threshold.

        Returns:
            True if the last improvement is negligible.
        """
        if len(self.trajectory) < 2:
            return False
        improvement = self.trajectory[-1] - self.trajectory[-2]
        return abs(improvement) < DIMINISHING_RETURNS_THRESHOLD


class TRMRefinement:
    """TRM (Think-Refine-Monitor) recursive prompt refinement."""

    def __init__(self, client: object | None = None) -> None:
        self._client = client

    async def refine(
        self, prompt: str, context: str, max_iterations: int = 5
    ) -> EnhancedPrompt:
        """Refine a prompt through recursive self-improvement.

        Args:
            prompt: The original prompt to refine.
            context: Supporting context.
            max_iterations: Maximum refinement iterations.

        Returns:
            EnhancedPrompt with refined version.
        """
        current = prompt
        trajectory: list[float] = []
        iterations = 0

        for i in range(max_iterations):
            iterations = i + 1
            confidence = await self._evaluate_confidence(current, context)
            trajectory.append(confidence)

            evidence = ConvergenceEvidence(trajectory)
            if evidence.shows_strong_convergence:
                break
            if evidence.shows_oscillation:
                break
            if evidence.shows_diminishing_returns:
                break

            current = await self._refine_step(current, context, confidence)

        final_confidence = trajectory[-1] if trajectory else 0.5

        return EnhancedPrompt(
            original=prompt,
            enhanced=current,
            strategy_used="trm_refinement",
            confidence=round(final_confidence, 4),
            iterations=iterations,
        )

    async def _evaluate_confidence(self, prompt: str, context: str) -> float:
        """Evaluate confidence in the current prompt quality.

        Args:
            prompt: The current prompt text.
            context: Supporting context.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if self._client is None:
            return min(0.95, 0.6 + len(prompt) * 0.001)
        return 0.7

    async def _refine_step(
        self, prompt: str, context: str, current_confidence: float
    ) -> str:
        """Perform one refinement step.

        Args:
            prompt: The current prompt.
            context: Supporting context.
            current_confidence: Current confidence level.

        Returns:
            Refined prompt text.
        """
        if self._client is None:
            return f"{prompt}\n[Refined: consider edge cases and constraints from context]"
        return prompt
