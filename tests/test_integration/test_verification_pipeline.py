"""Integration test — all 64 HOR rules against known-good and known-bad PRD fixtures."""

from __future__ import annotations

import pytest

from ai_architect_mcp._verification.hor_rules.engine import HORRuleEngine

TOTAL_RULES = 64


class TestVerificationPipeline:
    """Test full HOR rule suite against PRD fixtures."""

    def test_known_good_prd_passes_most_rules(
        self, sample_prd_artifact: dict[str, object]
    ) -> None:
        """A well-formed PRD should pass the majority of HOR rules."""
        engine = HORRuleEngine()
        results = engine.run_all(sample_prd_artifact)

        assert len(results) == TOTAL_RULES
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        # A good PRD should pass at least 50% of rules
        assert passed > TOTAL_RULES * 0.5, (
            f"Good PRD passed only {passed}/{TOTAL_RULES} rules. "
            f"Failures: {[r.rule_name for r in results if not r.passed]}"
        )

    def test_empty_artifact_fails_critical_rules(self) -> None:
        """An empty artifact should fail critical structural rules."""
        engine = HORRuleEngine()
        results = engine.run_all({})

        assert len(results) == TOTAL_RULES

        # Rule 1 (title_exists) must fail on empty artifact
        rule_1 = next(r for r in results if r.rule_id == 1)
        assert rule_1.passed is False

    def test_adjusted_score_decreases_on_failures(self) -> None:
        """Score should decrease when rules fail."""
        engine = HORRuleEngine()

        good_results = engine.run_all({
            "title": "Good PRD",
            "content": "Comprehensive content",
            "sections": [{"name": s} for s in [
                "Overview", "Requirements", "User Stories",
                "Technical", "Acceptance", "Roadmap", "Testing",
            ]],
        })

        bad_results = engine.run_all({})

        good_score = engine.calculate_adjusted_score(1.0, good_results)
        bad_score = engine.calculate_adjusted_score(1.0, bad_results)

        assert good_score > bad_score

    def test_all_rule_ids_sequential(self) -> None:
        """Verify rules 1-64 are all registered with no gaps."""
        engine = HORRuleEngine()
        results = engine.run_all({"title": "Test"})
        rule_ids = sorted(r.rule_id for r in results)
        assert rule_ids == list(range(1, TOTAL_RULES + 1))

    def test_no_llm_imports_in_hor_rules(self) -> None:
        """Verify HOR rules module has no LLM dependencies."""
        import ai_architect_mcp._verification.hor_rules.structural as m
        source = m.__file__ or ""
        assert source  # File exists

        # The module should not import anthropic or openai
        import importlib
        module_names = [
            "ai_architect_mcp._verification.hor_rules.structural",
            "ai_architect_mcp._verification.hor_rules.architecture",
            "ai_architect_mcp._verification.hor_rules.security",
            "ai_architect_mcp._verification.hor_rules.resilience",
            "ai_architect_mcp._verification.hor_rules.quality",
            "ai_architect_mcp._verification.hor_rules.observability",
        ]
        for name in module_names:
            mod = importlib.import_module(name)
            mod_source = open(mod.__file__).read()  # noqa: SIM115
            assert "anthropic" not in mod_source, f"LLM import found in {name}"
            assert "openai" not in mod_source, f"LLM import found in {name}"
