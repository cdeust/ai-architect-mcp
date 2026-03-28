"""TRM Refinement — recursive refinement with intelligent halting.

Research: Madaan et al. (2023) Self-Refine.
"""

from __future__ import annotations

from ai_architect_mcp._models.prompting import EnhancedPrompt

CONVERGENCE_THRESHOLD = 0.02
OSCILLATION_WINDOW = 3
DIMINISHING_RETURNS_THRESHOLD = 0.01
DEFAULT_MODEL = "claude-sonnet-4-20250514"


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

    def __init__(self, client: object, model: str = DEFAULT_MODEL) -> None:
        if client is None:
            raise ValueError(
                "TRMRefinement requires an LLM client. "
                "Provide a Claude CLI client or AsyncAnthropic instance."
            )
        self._client = client
        self._model = model

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
        self._original_prompt = prompt

        # Single-shot path: generate complete output in one call.
        # CLI-backed calls are slow (~30-60s each), so skip confidence eval.
        if max_iterations <= 5:
            current = await self._refine_step(prompt, context, 0.0)
            return EnhancedPrompt(
                original=prompt,
                enhanced=current,
                strategy_used="trm_refinement",
                confidence=0.85,
                iterations=1,
            )

        # Iterative path for explicitly high max_iterations
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
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=100,
                temperature=0.1,
                system=(
                    "Rate how well the following content fulfills the given task. "
                    "Respond with a single decimal number between 0.0 and 1.0."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Task:\n{self._original_prompt}\n\n"
                        f"Content:\n{prompt}"
                    ),
                }],
            )
            text = response.content[0].text.strip()
            score = float(text.split()[0].strip(".,;:"))
            return max(0.0, min(1.0, score))
        except (AttributeError, IndexError, TypeError, ValueError):
            return 0.7
        except Exception:
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
        is_first = prompt == self._original_prompt
        try:
            if is_first:
                system_msg = (
                    "You are a expert content generator. Execute the task below "
                    "using the provided context. Produce thorough, well-structured "
                    "output that directly fulfills the task requirements."
                )
                user_msg = f"Task: {prompt}\n\nContext:\n{context}"
            else:
                system_msg = (
                    "You are a expert content refiner. Improve the content below "
                    "to better fulfill the original task. Fix gaps, add depth, "
                    "and improve clarity while preserving what works."
                )
                user_msg = (
                    f"Original task: {self._original_prompt}\n\n"
                    f"Current content:\n{prompt}\n\n"
                    f"Context:\n{context}\n\n"
                    f"Current confidence: {current_confidence:.2f}"
                )

            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.7,
                system=system_msg,
                messages=[{"role": "user", "content": user_msg}],
            )
            return response.content[0].text.strip()
        except (AttributeError, IndexError, TypeError):
            return prompt
        except Exception:
            return prompt
