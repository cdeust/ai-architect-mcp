"""Strategy Registry — deterministic strategy selection by project characteristics."""

from __future__ import annotations

from ai_architect_mcp._models.prompting import StrategySelection, ThinkingStrategy
from ai_architect_mcp._prompting.strategies.research_evidence import ResearchEvidenceDatabase


class StrategyRegistry:
    """Deterministic strategy selector based on project characteristics."""

    def __init__(self) -> None:
        self._db = ResearchEvidenceDatabase()

    def select(
        self,
        project_type: str,
        complexity: str,
        characteristics: list[str],
    ) -> StrategySelection:
        """Select the best thinking strategy for a problem.

        Args:
            project_type: Type of project (e.g., 'api', 'mobile', 'data').
            complexity: Complexity level ('low', 'medium', 'high').
            characteristics: Problem characteristics to match against.

        Returns:
            StrategySelection with best strategy and alternatives.
        """
        scored: list[tuple[float, ThinkingStrategy]] = []
        for strategy in self._db.get_all():
            score = self._score_strategy(strategy, characteristics)
            scored.append((score, strategy))

        scored.sort(key=lambda x: (-x[0], x[1].tier))

        best_score, best_strategy = scored[0]
        alternatives = [s for _, s in scored[1:4]]

        reason = self._generate_reason(best_strategy, characteristics, best_score)

        return StrategySelection(
            selected=best_strategy,
            reason=reason,
            score=round(best_score, 4),
            alternatives=alternatives,
        )

    def _score_strategy(
        self, strategy: ThinkingStrategy, characteristics: list[str]
    ) -> float:
        """Score a strategy against problem characteristics."""
        if not characteristics or not strategy.applicable_characteristics:
            return strategy.weight * 0.1

        matching = sum(
            1 for c in characteristics
            if c in strategy.applicable_characteristics
        )
        total = len(characteristics)
        overlap_ratio = matching / total if total > 0 else 0.0

        return strategy.weight * overlap_ratio

    def _generate_reason(
        self, strategy: ThinkingStrategy, characteristics: list[str], score: float
    ) -> str:
        """Generate a human-readable selection reason."""
        matching = [
            c for c in characteristics
            if c in strategy.applicable_characteristics
        ]
        return (
            f"Selected {strategy.name} (Tier {strategy.tier}, score={score:.2f}) — "
            f"matches characteristics: {', '.join(matching) if matching else 'general applicability'}. "
            f"Research: {strategy.research_paper}"
        )
