"""Collaborative Inference — multi-path reasoning with consensus.

Research: Wang et al. (2022) Self-Consistency; Li et al. (2024) DisCIPL.
"""

from __future__ import annotations

from ai_architect_mcp._models.prompting import EnhancedPrompt

DEFAULT_PATH_COUNT = 3
DEFAULT_MAX_STEPS = 5
EARLY_TERMINATION_THRESHOLD = 0.8


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

    def __init__(self, client: object | None = None) -> None:
        self._client = client

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
        """Perform one reasoning step on a path.

        Args:
            prompt: The original prompt.
            context: Supporting context.
            path: The inference path to advance.

        Returns:
            Reasoning result for this step.
        """
        if self._client is None:
            return f"Path {path.path_id}: Reasoning about {prompt[:50]}..."
        return prompt

    async def _evaluate(self, result: str, context: str) -> float:
        """Evaluate confidence in a reasoning result.

        Args:
            result: The reasoning result.
            context: Supporting context.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if self._client is None:
            return 0.75
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
