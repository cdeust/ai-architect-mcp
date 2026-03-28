"""Metacognitive Monitor — self-aware reasoning with intervention triggers.

Research: Kadavath et al. (2022); Zhang et al. MetaMind (Stanford).
"""

from __future__ import annotations

from enum import Enum

from ai_architect_mcp._models.prompting import EnhancedPrompt

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class Intervention(str, Enum):
    """Types of metacognitive interventions."""

    CONTINUE = "continue"
    TRIGGER_REFLECTION = "trigger_reflection"
    SWITCH_STRATEGY = "switch_strategy"
    TERMINATE = "terminate"


FALLBACK_STRATEGIES = [
    "chartered_path",
    "analytical_decomposition",
    "symbolic_reasoning",
    "empirical_sampling",
]


class MetacognitiveMonitor:
    """Metacognitive monitor for self-aware reasoning."""

    def __init__(self, client: object, model: str = DEFAULT_MODEL) -> None:
        if client is None:
            raise ValueError(
                "MetacognitiveMonitor requires an LLM client. "
                "Provide a Claude CLI client or AsyncAnthropic instance."
            )
        self._client = client
        self._model = model
        self._current_strategy_idx = 0

    async def monitor(
        self,
        prompt: str,
        response: str,
        context: str,
        max_iterations: int = 5,
    ) -> EnhancedPrompt:
        """Monitor and enhance reasoning with metacognitive interventions.

        Args:
            prompt: The original prompt.
            response: Initial response to monitor.
            context: Supporting context.
            max_iterations: Maximum monitoring iterations.

        Returns:
            EnhancedPrompt with metacognitively enhanced version.
        """
        current = response
        iterations = 0
        trajectory: list[float] = []

        for i in range(max_iterations):
            iterations = i + 1
            confidence = await self._assess_confidence(current, context)
            trajectory.append(confidence)

            intervention = self._assess_intervention(trajectory)

            if intervention == Intervention.TERMINATE:
                break
            elif intervention == Intervention.TRIGGER_REFLECTION:
                current = await self._reflect(prompt, current, context)
            elif intervention == Intervention.SWITCH_STRATEGY:
                current = await self._switch_strategy(prompt, current, context)

        final_confidence = trajectory[-1] if trajectory else 0.5

        return EnhancedPrompt(
            original=prompt,
            enhanced=current,
            strategy_used="metacognitive",
            confidence=round(min(1.0, final_confidence), 4),
            iterations=iterations,
        )

    def _assess_intervention(self, trajectory: list[float]) -> Intervention:
        """Determine what intervention is needed.

        Args:
            trajectory: History of confidence values.

        Returns:
            The intervention type to apply.
        """
        if not trajectory:
            return Intervention.CONTINUE

        latest = trajectory[-1]
        if latest >= 0.85:
            return Intervention.TERMINATE

        if len(trajectory) >= 2:
            improvement = latest - trajectory[-2]
            if improvement < -0.1:
                return Intervention.SWITCH_STRATEGY
            if abs(improvement) < 0.01:
                return Intervention.TRIGGER_REFLECTION

        return Intervention.CONTINUE

    async def _assess_confidence(self, response: str, context: str) -> float:
        """Assess confidence in a response using LLM.

        Args:
            response: The response to assess.
            context: Supporting context.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        try:
            result = await self._client.messages.create(
                model=self._model,
                max_tokens=50,
                temperature=0.1,
                system=(
                    "Rate the quality and completeness of this response "
                    "on a scale of 0.0 to 1.0. Respond with only a number."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Response:\n{response[:2000]}\n\n"
                        f"Context:\n{context[:1000]}"
                    ),
                }],
            )
            text = result.content[0].text.strip()
            score = float(text.split()[0].strip(".,;:"))
            return max(0.0, min(1.0, score))
        except (AttributeError, IndexError, TypeError, ValueError):
            return 0.7
        except Exception:
            return 0.7

    async def _reflect(self, prompt: str, response: str, context: str) -> str:
        """Trigger a reflection intervention using LLM.

        Args:
            prompt: The original prompt.
            response: The current response.
            context: Supporting context.

        Returns:
            Reflected response.
        """
        try:
            result = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.7,
                system=(
                    "You are a metacognitive reviewer. The response below may have "
                    "issues. Reflect on its assumptions, identify gaps, and produce "
                    "an improved version."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Original task: {prompt}\n\n"
                        f"Current response:\n{response}\n\n"
                        f"Context:\n{context}"
                    ),
                }],
            )
            return result.content[0].text.strip()
        except (AttributeError, IndexError, TypeError):
            return response
        except Exception:
            return response

    async def _switch_strategy(
        self, prompt: str, response: str, context: str
    ) -> str:
        """Switch to a fallback strategy using LLM.

        Args:
            prompt: The original prompt.
            response: The current response.
            context: Supporting context.

        Returns:
            Response with new strategy applied.
        """
        self._current_strategy_idx = (
            (self._current_strategy_idx + 1) % len(FALLBACK_STRATEGIES)
        )
        strategy = FALLBACK_STRATEGIES[self._current_strategy_idx]

        try:
            result = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.7,
                system=(
                    f"The current approach isn't working. Switch to a "
                    f"'{strategy}' strategy. Re-approach the task from "
                    f"this new angle and produce a better response."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Task: {prompt}\n\n"
                        f"Previous attempt:\n{response}\n\n"
                        f"Context:\n{context}"
                    ),
                }],
            )
            return result.content[0].text.strip()
        except (AttributeError, IndexError, TypeError):
            return response
        except Exception:
            return response
