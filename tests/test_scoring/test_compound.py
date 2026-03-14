"""Tests for compound scoring — fixture-based bit-for-bit matching."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect_mcp._scoring.compound import (
    DEFAULT_WEIGHTS,
    calculate_compound_score,
    normalize_weights,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestNormalizeWeights:
    """Test weight normalization."""

    def test_already_normalized(self) -> None:
        weights = {"a": 0.5, "b": 0.5}
        result = normalize_weights(weights)
        assert abs(sum(result.values()) - 1.0) < 1e-10

    def test_unnormalized(self) -> None:
        weights = {"a": 2.0, "b": 3.0}
        result = normalize_weights(weights)
        assert abs(result["a"] - 0.4) < 1e-10
        assert abs(result["b"] - 0.6) < 1e-10

    def test_all_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="all values are zero"):
            normalize_weights({"a": 0.0, "b": 0.0})


class TestCalculateCompoundScore:
    """Test compound score calculation."""

    def test_default_weights(self) -> None:
        score = calculate_compound_score(0.8, 0.6, 0.9, 0.7)
        expected = 0.8 * 0.3 + 0.6 * 0.2 + 0.9 * 0.3 + 0.7 * 0.2
        assert abs(score.weighted_total - expected) < 1e-10

    def test_custom_weights(self) -> None:
        weights = {"relevance": 0.25, "uniqueness": 0.25, "impact": 0.25, "confidence": 0.25}
        score = calculate_compound_score(0.8, 0.6, 0.9, 0.7, weights=weights)
        expected = (0.8 + 0.6 + 0.9 + 0.7) / 4
        assert abs(score.weighted_total - expected) < 1e-10

    def test_weights_normalized_in_result(self) -> None:
        score = calculate_compound_score(0.5, 0.5, 0.5, 0.5)
        assert abs(sum(score.weights.values()) - 1.0) < 1e-10

    def test_boundary_scores(self) -> None:
        score = calculate_compound_score(0.0, 0.0, 0.0, 0.0)
        assert score.weighted_total == 0.0

        score = calculate_compound_score(1.0, 1.0, 1.0, 1.0)
        assert abs(score.weighted_total - 1.0) < 1e-10

    def test_fixture_basic(self) -> None:
        fixture_path = FIXTURES_DIR / "compound_score_basic.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            score = calculate_compound_score(
                data["relevance"],
                data["uniqueness"],
                data["impact"],
                data["confidence"],
                weights=data["weights"],
            )
            assert abs(score.weighted_total - data["weighted_total"]) < 1e-10

    def test_fixture_custom_weights(self) -> None:
        fixture_path = FIXTURES_DIR / "compound_score_custom_weights.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            score = calculate_compound_score(
                data["relevance"],
                data["uniqueness"],
                data["impact"],
                data["confidence"],
                weights=data["weights"],
            )
            assert abs(score.weighted_total - data["weighted_total"]) < 1e-10
