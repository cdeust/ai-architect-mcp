"""Tests for the _parsing subsystem: query registry and AST cache."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._parsing.ast_cache import ASTCache, CacheStats
from ai_codebase_intelligence._parsing.queries.query_registry import (
    get_queries_for_language,
)


# ---------------------------------------------------------------------------
# Query registry tests
# ---------------------------------------------------------------------------


class TestQueryRegistry:
    """Tests for the tree-sitter query registry."""

    def test_all_13_languages_have_queries(self) -> None:
        """Every SupportedLanguage must have a query dictionary."""
        for lang in SupportedLanguage:
            queries = get_queries_for_language(lang)
            assert queries, f"Missing queries for {lang.value}"

    def test_queries_are_non_empty(self) -> None:
        """Each language must define at least one query pattern."""
        for lang in SupportedLanguage:
            queries = get_queries_for_language(lang)
            assert len(queries) > 0, f"Empty queries for {lang.value}"

    def test_query_values_are_strings(self) -> None:
        """Query patterns must be S-expression strings."""
        for lang in SupportedLanguage:
            queries = get_queries_for_language(lang)
            for name, pattern in queries.items():
                assert isinstance(pattern, str), (
                    f"Query {name} for {lang.value} is not a string"
                )
                assert pattern.startswith("("), (
                    f"Query {name} for {lang.value} does not start with '('"
                )

    def test_get_queries_for_known_language(self) -> None:
        """get_queries_for_language returns dict for Python."""
        queries = get_queries_for_language(SupportedLanguage.PYTHON)
        assert "class_definition" in queries
        assert "function_definition" in queries

    def test_get_queries_returns_dict_for_all(self) -> None:
        """get_queries_for_language returns successfully for all languages."""
        for lang in SupportedLanguage:
            result = get_queries_for_language(lang)
            assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# AST Cache tests
# ---------------------------------------------------------------------------


class TestASTCache:
    """Tests for the LRU AST cache."""

    def _make_tree(self) -> MagicMock:
        """Create a mock tree-sitter Tree."""
        return MagicMock(name="MockTree")

    def test_put_and_get(self) -> None:
        """Inserting and retrieving a tree works."""
        cache = ASTCache(max_size=5)
        tree = self._make_tree()
        cache.put("/foo.py", tree)
        assert cache.get("/foo.py") is tree

    def test_get_miss_returns_none(self) -> None:
        """Cache miss returns None."""
        cache = ASTCache(max_size=5)
        assert cache.get("/nonexistent.py") is None

    def test_stats_tracking(self) -> None:
        """Hits and misses are tracked correctly."""
        cache = ASTCache(max_size=5)
        cache.get("/miss.py")
        cache.put("/hit.py", self._make_tree())
        cache.get("/hit.py")
        assert cache.stats.hits == 1
        assert cache.stats.misses == 1

    def test_lru_eviction(self) -> None:
        """Oldest entry is evicted when capacity is reached."""
        cache = ASTCache(max_size=2)
        cache.put("/a.py", self._make_tree())
        cache.put("/b.py", self._make_tree())
        cache.put("/c.py", self._make_tree())
        assert cache.get("/a.py") is None
        assert cache.get("/b.py") is not None
        assert cache.get("/c.py") is not None
        assert cache.stats.evictions == 1

    def test_lru_access_updates_order(self) -> None:
        """Accessing an entry makes it most-recently-used."""
        cache = ASTCache(max_size=2)
        cache.put("/a.py", self._make_tree())
        cache.put("/b.py", self._make_tree())
        cache.get("/a.py")
        cache.put("/c.py", self._make_tree())
        assert cache.get("/a.py") is not None
        assert cache.get("/b.py") is None

    def test_clear(self) -> None:
        """Clear removes all entries and resets stats."""
        cache = ASTCache(max_size=5)
        cache.put("/a.py", self._make_tree())
        cache.get("/a.py")
        cache.clear()
        assert len(cache) == 0
        assert cache.stats.hits == 0

    def test_resize_shrink(self) -> None:
        """Shrinking the cache evicts excess entries."""
        cache = ASTCache(max_size=5)
        for i in range(5):
            cache.put(f"/{i}.py", self._make_tree())
        cache.resize(2)
        assert len(cache) == 2
        assert cache.stats.evictions == 3

    def test_resize_grow(self) -> None:
        """Growing the cache does not evict entries."""
        cache = ASTCache(max_size=2)
        cache.put("/a.py", self._make_tree())
        cache.resize(10)
        assert len(cache) == 1
        assert cache.max_size == 10

    def test_invalid_max_size(self) -> None:
        """max_size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="max_size must be >= 1"):
            ASTCache(max_size=0)

    def test_invalid_resize(self) -> None:
        """Resizing to < 1 raises ValueError."""
        cache = ASTCache(max_size=5)
        with pytest.raises(ValueError, match="max_size must be >= 1"):
            cache.resize(0)

    def test_len(self) -> None:
        """__len__ returns number of cached entries."""
        cache = ASTCache(max_size=5)
        assert len(cache) == 0
        cache.put("/a.py", self._make_tree())
        assert len(cache) == 1

    def test_contains(self) -> None:
        """contains checks presence without affecting LRU order."""
        cache = ASTCache(max_size=5)
        cache.put("/a.py", self._make_tree())
        assert cache.contains("/a.py") is True
        assert cache.contains("/b.py") is False
        assert cache.stats.hits == 0

    def test_hit_rate(self) -> None:
        """Hit rate is computed correctly."""
        stats = CacheStats(hits=3, misses=7)
        assert abs(stats.hit_rate - 0.3) < 0.001

    def test_hit_rate_zero_accesses(self) -> None:
        """Hit rate is 0.0 with no accesses."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_put_updates_existing(self) -> None:
        """Putting a key that already exists updates the value."""
        cache = ASTCache(max_size=5)
        tree1 = self._make_tree()
        tree2 = self._make_tree()
        cache.put("/a.py", tree1)
        cache.put("/a.py", tree2)
        assert cache.get("/a.py") is tree2
        assert len(cache) == 1
