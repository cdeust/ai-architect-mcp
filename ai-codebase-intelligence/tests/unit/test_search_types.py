"""Tests for search type models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_codebase_intelligence._models.search_types import (
    BM25Result,
    HybridSearchResult,
    SearchRequest,
    SearchResultKind,
)


class TestBM25Result:
    """Tests for BM25Result model."""

    def test_create_result(self) -> None:
        result = BM25Result(
            node_id="src/main.py:main:Function",
            score=2.5,
            matched_field="name",
            snippet="def main():",
        )
        assert result.score == 2.5
        assert result.matched_field == "name"


class TestHybridSearchResult:
    """Tests for HybridSearchResult model."""

    def test_default_scores(self) -> None:
        result = HybridSearchResult(
            node_id="a:b:Function",
            name="process",
            kind=SearchResultKind.SYMBOL,
        )
        assert result.rrf_score == 0.0
        assert result.bm25_score == 0.0
        assert result.process_score == 0.0
        assert result.processes == []

    def test_full_result(self) -> None:
        result = HybridSearchResult(
            node_id="a:b:Function",
            name="process_data",
            kind=SearchResultKind.SYMBOL,
            file_path="src/pipeline.py",
            rrf_score=0.85,
            bm25_score=3.2,
            process_score=0.7,
            processes=["DataIngestion", "ETL"],
            community="data-processing",
        )
        assert len(result.processes) == 2


class TestSearchRequest:
    """Tests for SearchRequest model."""

    def test_default_request(self) -> None:
        req = SearchRequest(query="bias correction")
        assert req.limit == 20
        assert req.include_processes is True
        assert req.language_filter is None

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=0)
        with pytest.raises(ValidationError):
            SearchRequest(query="test", limit=101)
