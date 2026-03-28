"""Collaborative Inference — multi-path reasoning with consensus.

Research: Wang et al. (2022) Self-Consistency; Li et al. (2024) DisCIPL.
"""

from __future__ import annotations

from ai_architect_mcp._models.prompting import EnhancedPrompt

DEFAULT_PATH_COUNT = 3
DEFAULT_MAX_STEPS = 5
EARLY_TERMINATION_THRESHOLD = 0.8
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class InferencePath:
    """A single reasoning path in collaborative inference."""

    def __init__(self, path_id: int) -> None:
        self.path_id = path_id
        self.confidence = 0.5
        self.is_complete = False
        self.reasoning = ""
        self.history: list[str] = []


class CollaborativeInference:
    """Multi-path collaborative inference with consensus detection."""

    def __init__(self, client: object, model: str = DEFAULT_MODEL) -> None:
        if client is None:
            raise ValueError(
                "CollaborativeInference requires an LLM client. "
                "Provide a Claude CLI client or AsyncAnthropic instance."
            )
        self._client = client
        self._model = model

    async def infer(
        self,
        prompt: str,
        context: str,
        path_count: int = DEFAULT_PATH_COUNT,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> EnhancedPrompt:
        """Run collaborative inference across multiple paths.

        Args:
            prompt: The original prompt.
            context: Supporting context.
            path_count: Number of reasoning paths.
            max_steps: Maximum steps per path.

        Returns:
            EnhancedPrompt with consensus-enhanced version.
        """
        paths = [InferencePath(i) for i in range(path_count)]
        iterations = 0

        for step in range(max_steps):
            iterations = step + 1
            for path in paths:
                if not path.is_complete:
                    result = await self._step(prompt, context, path)
                    path.reasoning = result
                    path.history.append(result)
                    path.confidence = await self._evaluate(result, context)
                    if path.confidence >= EARLY_TERMINATION_THRESHOLD:
                        path.is_complete = True

            if self._detect_consensus(paths):
                break

            if all(p.is_complete for p in paths):
                break

        best = max(paths, key=lambda p: p.confidence)
        avg_confidence = sum(p.confidence for p in paths) / len(paths)

        return EnhancedPrompt(
            original=prompt,
            enhanced=best.reasoning,
            strategy_used="collaborative_inference",
            confidence=round(min(1.0, avg_confidence), 4),
            iterations=iterations,
        )

    async def _step(
        self, prompt: str, context: str, path: InferencePath
    ) -> str:
        """Perform one reasoning step on a path using LLM.

        Args:
            prompt: The original prompt.
            context: Supporting context.
            path: The inference path to advance.

        Returns:
            Reasoning result for this step.
        """
        history_text = "\n".join(path.history[-3:]) if path.history else ""

        try:
            result = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                temperature=0.5 + (path.path_id * 0.1),
                system=(
                    f"You are reasoning path #{path.path_id}. "
                    "Approach the task from your unique perspective. "
                    "Build on your previous reasoning if any."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Task: {prompt}\n\n"
                        f"Context:\n{context}\n\n"
                        f"Previous reasoning:\n{history_text}"
                    ),
                }],
            )
            return result.content[0].text.strip()
        except (AttributeError, IndexError, TypeError):
            return prompt
        except Exception:
            return prompt

    async def _evaluate(self, result: str, context: str) -> float:
        """Evaluate confidence in a reasoning result using LLM.

        Args:
            result: The reasoning result.
            context: Supporting context.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=50,
                temperature=0.1,
                system=(
                    "Rate the quality of this reasoning on a scale of 0.0 to 1.0. "
                    "Respond with only a number."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Reasoning:\n{result[:2000]}\n\n"
                        f"Context:\n{context[:1000]}"
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

    def _detect_consensus(self, paths: list[InferencePath]) -> bool:
        """Detect if paths have reached consensus.

        Args:
            paths: All inference paths.

        Returns:
            True if paths show low variance and high mean confidence.
        """
        confidences = [p.confidence for p in paths if p.confidence > 0]
        if len(confidences) < 2:
            return False
        mean = sum(confidences) / len(confidences)
        variance = sum((c - mean) ** 2 for c in confidences) / len(confidences)
        return variance < 0.02 and mean > 0.7
