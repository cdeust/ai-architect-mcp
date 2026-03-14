"""Disclosure model — progressive context budget management.

Controls how much detail is rendered based on remaining token budget.
Three levels: L1 (config only), L2 (summaries), L3 (full content).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

THRESHOLD_L2: float = 0.70
THRESHOLD_L1: float = 0.93


class DisclosureLevel(str, Enum):
    """How much detail to render in context output."""

    L1_CONFIG = "l1_config"
    L2_SUMMARY = "l2_summary"
    L3_FULL = "l3_full"


class ContextBudget(BaseModel):
    """Token budget tracker with automatic disclosure level recommendation.

    Attributes:
        total_tokens: Maximum token capacity.
        used_tokens: Tokens consumed so far.
        disclosure_level: Current rendering level.
    """

    total_tokens: int = Field(gt=0, description="Maximum token capacity")
    used_tokens: int = Field(
        default=0, ge=0, description="Tokens consumed so far"
    )
    disclosure_level: DisclosureLevel = Field(
        default=DisclosureLevel.L3_FULL, description="Current rendering level"
    )

    @property
    def remaining_tokens(self) -> int:
        """Tokens still available."""
        return max(0, self.total_tokens - self.used_tokens)

    @property
    def usage_percent(self) -> float:
        """Fraction of budget consumed (0.0 to 1.0)."""
        return self.used_tokens / self.total_tokens

    def recommend_level(self) -> DisclosureLevel:
        """Recommend a disclosure level based on current usage.

        Returns:
            L1_CONFIG if usage >= 93%, L2_SUMMARY if >= 70%, else L3_FULL.
        """
        pct = self.usage_percent
        if pct >= THRESHOLD_L1:
            return DisclosureLevel.L1_CONFIG
        if pct >= THRESHOLD_L2:
            return DisclosureLevel.L2_SUMMARY
        return DisclosureLevel.L3_FULL
