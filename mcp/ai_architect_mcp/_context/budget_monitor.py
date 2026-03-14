"""Budget monitor — tracks token usage and recommends disclosure levels.

Wraps ContextBudget with update semantics and compaction detection.
Used by the orchestrator to decide when to switch rendering levels
and when to trigger context compaction.
"""

from __future__ import annotations

from ai_architect_mcp._models.disclosure import (
    ContextBudget,
    DisclosureLevel,
    THRESHOLD_L1,
)

THRESHOLD_L2: float = 0.70
COMPACT_THRESHOLD: float = THRESHOLD_L1


class BudgetMonitor:
    """Stateful monitor for context token budget.

    Tracks consumption and recommends progressive disclosure levels.

    Args:
        total_tokens: Maximum token capacity for the session.
    """

    def __init__(self, total_tokens: int) -> None:
        """Initialize the budget monitor.

        Args:
            total_tokens: Maximum token capacity.
        """
        self._budget = ContextBudget(total_tokens=total_tokens)

    def update(self, used_tokens: int) -> ContextBudget:
        """Update the token usage and recalculate the disclosure level.

        Args:
            used_tokens: Total tokens consumed so far.

        Returns:
            Updated ContextBudget with recommended disclosure level.
        """
        self._budget = ContextBudget(
            total_tokens=self._budget.total_tokens,
            used_tokens=used_tokens,
            disclosure_level=self._budget.recommend_level(),
        )
        # Recalculate after update
        self._budget = ContextBudget(
            total_tokens=self._budget.total_tokens,
            used_tokens=used_tokens,
            disclosure_level=self._recommend(used_tokens),
        )
        return self._budget

    def should_compact(self) -> bool:
        """Check if context should be compacted.

        Returns:
            True if usage is at or above the compaction threshold (93%).
        """
        return self._budget.usage_percent >= COMPACT_THRESHOLD

    @property
    def current_budget(self) -> ContextBudget:
        """Get the current budget state.

        Returns:
            Current ContextBudget snapshot.
        """
        return self._budget

    def _recommend(self, used_tokens: int) -> DisclosureLevel:
        """Calculate recommended level for given usage.

        Args:
            used_tokens: Total tokens consumed.

        Returns:
            Appropriate disclosure level.
        """
        pct = used_tokens / self._budget.total_tokens
        if pct >= COMPACT_THRESHOLD:
            return DisclosureLevel.L1_CONFIG
        if pct >= THRESHOLD_L2:
            return DisclosureLevel.L2_SUMMARY
        return DisclosureLevel.L3_FULL
