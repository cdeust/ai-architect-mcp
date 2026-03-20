"""Tests for search modules (Epic 10)."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._models.search_types import (
    BM25Result,
    HybridSearchResult,
    SearchResultKind,
)
from ai_codebase_intelligence._search.hybrid_search import (
    RRF_K,
    _build_ranked_items,
    _compute_rrf,
)


class TestRRFComputation:
    """Tests for Reciprocal Rank Fusion."""

    def test_single_result(self) -> None:
        bm25 = [
            BM25Result(
                node_id="a", score=3.5, matched_field="name"
            )
        ]
        ranked = _build_ranked_items(bm25)
        scores = _compute_rrf(ranked)
        # RRF score = 1/(K + rank + 1) = 1/(60 + 0 + 1) = 1/61
        assert abs(scores["a"] - 1.0 / (RRF_K + 1)) < 0.001

    def test_multiple_results_ordered(self) -> None:
        bm25 = [
            BM25Result(node_id="a", score=5.0, matched_field="name"),
            BM25Result(node_id="b", score=3.0, matched_field="name"),
            BM25Result(node_id="c", score=1.0, matched_field="name"),
        ]
        ranked = _build_ranked_items(bm25)
        scores = _compute_rrf(ranked)
        assert scores["a"] > scores["b"] > scores["c"]

    def test_rrf_k_constant(self) -> None:
        """Verify K=60 as per RRF specification."""
        assert RRF_K == 60


class TestBM25Result:
    """Tests for BM25 result model."""

    def test_create(self) -> None:
        result = BM25Result(
            node_id="test:func:Function",
            score=2.8,
            matched_field="signature",
            snippet="def process_data(items: list):",
            table_name="Function",
        )
        assert result.score == 2.8
        assert result.table_name == "Function"
