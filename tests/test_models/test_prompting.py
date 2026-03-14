"""Tests for prompting models — strategy tiers, weights, research papers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._models.prompting import (
    ConfidenceEstimate,
    EnhancedPrompt,
    EnhancementSource,
    FusedConfidence,
    StrategySelection,
    ThinkingStrategy,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestThinkingStrategy:
    """Test ThinkingStrategy model."""

    def test_valid_strategy(self) -> None:
        strategy = ThinkingStrategy(
            strategy_id="recursive_refinement",
            name="Recursive Refinement",
            description="Iteratively refine outputs using self-evaluation",
            research_paper="DeepSeek-R1: Incentivizing Reasoning Capability",
            research_institution="DeepSeek",
            year=2025,
            improvement_claim="+32% MATH-500",
            tier=1,
            weight=1.0,
            applicable_characteristics=["mathematical_reasoning", "iterative_refinement"],
        )
        assert strategy.tier == 1
        assert strategy.weight == 1.0

    def test_tier_below_min_rejected(self) -> None:
        with pytest.raises(ValueError):
            ThinkingStrategy(
                strategy_id="test",
                name="Test",
                description="Test",
                research_paper="Test paper",
                research_institution="Test",
                year=2024,
                improvement_claim="none",
                tier=0,
                weight=0.5,
                applicable_characteristics=[],
            )

    def test_tier_above_max_rejected(self) -> None:
        with pytest.raises(ValueError):
            ThinkingStrategy(
                strategy_id="test",
                name="Test",
                description="Test",
                research_paper="Test paper",
                research_institution="Test",
                year=2024,
                improvement_claim="none",
                tier=5,
                weight=0.5,
                applicable_characteristics=[],
            )

    def test_weight_range(self) -> None:
        with pytest.raises(ValueError):
            ThinkingStrategy(
                strategy_id="test",
                name="Test",
                description="Test",
                research_paper="Test paper",
                research_institution="Test",
                year=2024,
                improvement_claim="none",
                tier=1,
                weight=1.5,
                applicable_characteristics=[],
            )

    def test_research_paper_required(self) -> None:
        strategy = ThinkingStrategy(
            strategy_id="test",
            name="Test",
            description="Test",
            research_paper="Some Research Paper",
            research_institution="MIT",
            year=2024,
            improvement_claim="+10%",
            tier=2,
            weight=0.7,
            applicable_characteristics=["test"],
        )
        assert strategy.research_paper != ""


class TestEnhancedPrompt:
    """Test EnhancedPrompt model."""

    def test_valid_enhanced_prompt(self) -> None:
        prompt = EnhancedPrompt(
            original="Write a function",
            enhanced="Think step by step. Write a function that...",
            strategy_used="recursive_refinement",
            confidence=0.85,
            iterations=3,
        )
        assert prompt.iterations == 3

    def test_iterations_below_one_rejected(self) -> None:
        with pytest.raises(ValueError):
            EnhancedPrompt(
                original="test",
                enhanced="test enhanced",
                strategy_used="test",
                confidence=0.5,
                iterations=0,
            )


class TestConfidenceEstimate:
    """Test ConfidenceEstimate model."""

    def test_valid_estimate(self) -> None:
        estimate = ConfidenceEstimate(
            source=EnhancementSource.THOUGHT_BUFFER,
            value=0.82,
            uncertainty=0.08,
            reasoning="Based on template match rate",
        )
        assert estimate.value == 0.82

    def test_all_sources_present(self) -> None:
        assert len(EnhancementSource) == 5


class TestFusedConfidence:
    """Test FusedConfidence model."""

    def test_valid_fused(self) -> None:
        fused = FusedConfidence(
            point=0.85,
            lower=0.78,
            upper=0.92,
            contributing_estimates=[
                ConfidenceEstimate(
                    source=EnhancementSource.THOUGHT_BUFFER,
                    value=0.82,
                    uncertainty=0.08,
                    reasoning="template match",
                ),
            ],
            fusion_method="weighted_average",
        )
        assert fused.lower <= fused.point <= fused.upper

    def test_fixture(self) -> None:
        fixture_path = FIXTURES_DIR / "strategy_selection_result.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            selection = StrategySelection.model_validate(data)
            assert selection.score >= 0.0
