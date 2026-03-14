"""Tests for BudgetMonitor context management."""

from __future__ import annotations

from ai_architect_mcp._context.budget_monitor import BudgetMonitor
from ai_architect_mcp._models.disclosure import DisclosureLevel


def test_initial_state_is_l3() -> None:
    """Fresh monitor starts at L3 (full disclosure)."""
    monitor = BudgetMonitor(total_tokens=100000)
    assert monitor.current_budget.disclosure_level == DisclosureLevel.L3_FULL


def test_update_to_l2_at_71_percent() -> None:
    """Updating to 71% usage recommends L2."""
    monitor = BudgetMonitor(total_tokens=100000)
    budget = monitor.update(71000)
    assert budget.disclosure_level == DisclosureLevel.L2_SUMMARY


def test_update_to_l1_at_94_percent() -> None:
    """Updating to 94% usage recommends L1."""
    monitor = BudgetMonitor(total_tokens=100000)
    budget = monitor.update(94000)
    assert budget.disclosure_level == DisclosureLevel.L1_CONFIG


def test_should_compact_false_at_50_percent() -> None:
    """50% usage should not trigger compaction."""
    monitor = BudgetMonitor(total_tokens=100000)
    monitor.update(50000)
    assert not monitor.should_compact()


def test_should_compact_true_at_94_percent() -> None:
    """94% usage triggers compaction."""
    monitor = BudgetMonitor(total_tokens=100000)
    monitor.update(94000)
    assert monitor.should_compact()


def test_remaining_tokens_tracked() -> None:
    """Budget tracks remaining tokens after update."""
    monitor = BudgetMonitor(total_tokens=100000)
    budget = monitor.update(60000)
    assert budget.remaining_tokens == 40000


def test_transition_l3_to_l2_to_l1() -> None:
    """Monitor transitions through all levels as usage increases."""
    monitor = BudgetMonitor(total_tokens=100000)

    b1 = monitor.update(30000)
    assert b1.disclosure_level == DisclosureLevel.L3_FULL

    b2 = monitor.update(75000)
    assert b2.disclosure_level == DisclosureLevel.L2_SUMMARY

    b3 = monitor.update(95000)
    assert b3.disclosure_level == DisclosureLevel.L1_CONFIG
