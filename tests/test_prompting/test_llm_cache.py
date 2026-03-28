"""Tests for LLM response cache."""

from __future__ import annotations

import pytest

from ai_architect_mcp._prompting.llm_cache import DEFAULT_MAX_ENTRIES, LLMResponseCache


class TestLLMResponseCache:
    """Tests for LLMResponseCache."""

    def test_cache_miss_returns_none(self) -> None:
        cache = LLMResponseCache()
        assert cache.get("prompt", "ctx", "model") is None

    def test_cache_hit_returns_stored_value(self) -> None:
        cache = LLMResponseCache()
        cache.put("prompt", "ctx", "model", {"text": "response"})
        result = cache.get("prompt", "ctx", "model")
        assert result == {"text": "response"}

    def test_different_inputs_no_collision(self) -> None:
        cache = LLMResponseCache()
        cache.put("a", "ctx", "model", "resp-a")
        cache.put("b", "ctx", "model", "resp-b")
        assert cache.get("a", "ctx", "model") == "resp-a"
        assert cache.get("b", "ctx", "model") == "resp-b"

    def test_model_change_invalidates(self) -> None:
        cache = LLMResponseCache()
        cache.put("prompt", "ctx", "claude-sonnet", "sonnet-resp")
        assert cache.get("prompt", "ctx", "claude-opus") is None

    def test_lru_eviction(self) -> None:
        cache = LLMResponseCache(max_entries=2)
        cache.put("a", "", "m", "1")
        cache.put("b", "", "m", "2")
        cache.put("c", "", "m", "3")  # evicts "a"
        assert cache.get("a", "", "m") is None
        assert cache.get("b", "", "m") == "2"
        assert cache.get("c", "", "m") == "3"

    def test_lru_access_refreshes(self) -> None:
        cache = LLMResponseCache(max_entries=2)
        cache.put("a", "", "m", "1")
        cache.put("b", "", "m", "2")
        cache.get("a", "", "m")  # refresh "a"
        cache.put("c", "", "m", "3")  # evicts "b" (not "a")
        assert cache.get("a", "", "m") == "1"
        assert cache.get("b", "", "m") is None

    def test_clear_resets_everything(self) -> None:
        cache = LLMResponseCache()
        cache.put("p", "c", "m", "r")
        cache.clear()
        assert cache.size == 0
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0
        # After clear, get is a miss (increments counter)
        assert cache.get("p", "c", "m") is None
        assert cache.stats["misses"] == 1

    def test_hit_rate_tracking(self) -> None:
        cache = LLMResponseCache()
        cache.put("p", "c", "m", "r")
        cache.get("p", "c", "m")  # hit
        cache.get("x", "c", "m")  # miss
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 1
        assert cache.stats["hit_rate"] == 0.5

    def test_default_max_entries(self) -> None:
        cache = LLMResponseCache()
        assert cache.stats["max_entries"] == DEFAULT_MAX_ENTRIES

    def test_size_tracking(self) -> None:
        cache = LLMResponseCache()
        assert cache.size == 0
        cache.put("a", "", "m", "1")
        assert cache.size == 1
        cache.put("b", "", "m", "2")
        assert cache.size == 2

    def test_overwrite_same_key(self) -> None:
        cache = LLMResponseCache()
        cache.put("p", "c", "m", "old")
        cache.put("p", "c", "m", "new")
        assert cache.get("p", "c", "m") == "new"
        assert cache.size == 1
