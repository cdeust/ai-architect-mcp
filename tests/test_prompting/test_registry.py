"""Tests for strategy registry."""

from __future__ import annotations

from ai_architect_mcp._prompting.strategies.registry import StrategyRegistry


class TestStrategyRegistry:
    def test_deterministic_selection(self) -> None:
        registry = StrategyRegistry()
        r1 = registry.select("api", "high", ["mathematical_reasoning"])
        r2 = registry.select("api", "high", ["mathematical_reasoning"])
        assert r1.selected.strategy_id == r2.selected.strategy_id

    def test_returns_alternatives(self) -> None:
        registry = StrategyRegistry()
        result = registry.select("mobile", "medium", ["code_generation"])
        assert len(result.alternatives) <= 3

    def test_score_is_positive(self) -> None:
        registry = StrategyRegistry()
        result = registry.select("data", "low", ["factual_verification"])
        assert result.score >= 0.0
