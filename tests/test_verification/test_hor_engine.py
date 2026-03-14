"""Tests for HOR rule engine — registration, run_all, penalty calculation."""

from __future__ import annotations

from ai_architect_mcp._models.verification import PENALTY_CRITICAL, PENALTY_WARNING, HORSeverity
from ai_architect_mcp._verification.hor_rules.engine import HORRuleEngine

TOTAL_RULES = 64


class TestHORRuleEngine:
    def test_auto_discover_registers_64_rules(self) -> None:
        engine = HORRuleEngine()
        assert engine.rule_count == TOTAL_RULES

    def test_run_all_returns_64_results(self) -> None:
        engine = HORRuleEngine()
        results = engine.run_all({"title": "Test PRD", "content": "", "sections": []})
        assert len(results) == TOTAL_RULES

    def test_run_by_category(self) -> None:
        engine = HORRuleEngine()
        structural = engine.run_by_category("structural", {"title": "Test", "content": ""})
        assert len(structural) == 10

    def test_run_single(self) -> None:
        engine = HORRuleEngine()
        result = engine.run_single(1, {"title": "Valid Title"})
        assert result.rule_id == 1
        assert result.passed is True

    def test_penalty_calculation_no_failures(self) -> None:
        engine = HORRuleEngine()
        results = engine.run_all({"title": "Test", "content": ""})
        passing = [r for r in results if r.passed]
        score = engine.calculate_adjusted_score(1.0, passing)
        assert score == 1.0

    def test_penalty_calculation_with_failures(self) -> None:
        engine = HORRuleEngine()
        results = engine.run_all({"content": ""})
        score = engine.calculate_adjusted_score(1.0, results)
        assert score < 1.0

    def test_score_never_below_zero(self) -> None:
        engine = HORRuleEngine()
        results = engine.run_all({})
        score = engine.calculate_adjusted_score(0.1, results)
        assert score >= 0.0
