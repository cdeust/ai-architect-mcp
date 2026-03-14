"""Tests for ContextBudget and DisclosureLevel models."""

from __future__ import annotations

from ai_architect_mcp._models.disclosure import ContextBudget, DisclosureLevel


def test_remaining_tokens() -> None:
    """remaining_tokens is total minus used."""
    budget = ContextBudget(total_tokens=100000, used_tokens=30000)
    assert budget.remaining_tokens == 70000


def test_usage_percent() -> None:
    """usage_percent is fraction of total consumed."""
    budget = ContextBudget(total_tokens=100000, used_tokens=50000)
    assert budget.usage_percent == 0.5


def test_recommend_l3_at_50_percent() -> None:
    """At 50% usage, recommend L3 (full)."""
    budget = ContextBudget(total_tokens=100000, used_tokens=50000)
    assert budget.recommend_level() == DisclosureLevel.L3_FULL


def test_recommend_l2_at_71_percent() -> None:
    """At 71% usage, recommend L2 (summary)."""
    budget = ContextBudget(total_tokens=100000, used_tokens=71000)
    assert budget.recommend_level() == DisclosureLevel.L2_SUMMARY


def test_recommend_l1_at_94_percent() -> None:
    """At 94% usage, recommend L1 (config only)."""
    budget = ContextBudget(total_tokens=100000, used_tokens=94000)
    assert budget.recommend_level() == DisclosureLevel.L1_CONFIG


def test_remaining_tokens_never_negative() -> None:
    """remaining_tokens floors at 0 if used exceeds total."""
    budget = ContextBudget(total_tokens=100, used_tokens=100)
    assert budget.remaining_tokens == 0
