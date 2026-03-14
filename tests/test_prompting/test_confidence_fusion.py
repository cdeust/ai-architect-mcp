"""Tests for confidence fusion — fixture-based deterministic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._models.prompting import ConfidenceEstimate, EnhancementSource
from ai_architect_mcp._prompting.confidence_fusion import ConfidenceFusionEngine

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestConfidenceFusion:
    def test_uniform_estimates(self) -> None:
        estimates = [
            ConfidenceEstimate(source=EnhancementSource.THOUGHT_BUFFER, value=0.8, uncertainty=0.05, reasoning="t"),
            ConfidenceEstimate(source=EnhancementSource.ADAPTIVE_EXPANSION, value=0.8, uncertainty=0.05, reasoning="t"),
            ConfidenceEstimate(source=EnhancementSource.METACOGNITIVE, value=0.8, uncertainty=0.05, reasoning="t"),
        ]
        result = ConfidenceFusionEngine().fuse(estimates)
        assert result.lower <= result.point <= result.upper

    def test_outlier_handling(self) -> None:
        estimates = [
            ConfidenceEstimate(source=EnhancementSource.THOUGHT_BUFFER, value=0.9, uncertainty=0.05, reasoning="t"),
            ConfidenceEstimate(source=EnhancementSource.ADAPTIVE_EXPANSION, value=0.9, uncertainty=0.05, reasoning="t"),
            ConfidenceEstimate(source=EnhancementSource.METACOGNITIVE, value=0.3, uncertainty=0.1, reasoning="t"),
        ]
        result = ConfidenceFusionEngine().fuse(estimates)
        assert result.point < 0.9

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            ConfidenceFusionEngine().fuse([])

    def test_bounds_valid(self) -> None:
        estimates = [
            ConfidenceEstimate(source=EnhancementSource.TRM_REFINEMENT, value=0.7, uncertainty=0.1, reasoning="t"),
        ]
        result = ConfidenceFusionEngine().fuse(estimates)
        assert 0.0 <= result.lower <= result.point
        assert result.point <= result.upper <= 1.0
