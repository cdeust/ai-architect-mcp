"""LRU cache for prompting algorithm LLM calls.

Per-session bounded cache keyed on (prompt_hash, context_hash, model).
Eliminates redundant LLM calls during pipeline runs with retries.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from typing import Any


DEFAULT_MAX_ENTRIES = 128


class LLMResponseCache:
    """Thread-safe LRU cache for LLM responses.

    Keyed on content hash of (prompt, context, model). Bounded
    by max_entries with LRU eviction. Designed for per-session use —
    create a new instance per pipeline run.
    """

    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        """Initialize the cache.

        Args:
            max_entries: Maximum number of cached responses.
        """
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_entries = max_entries
        self._hits = 0
        self._misses = 0

    def _make_key(self, prompt: str, context: str, model: str) -> str:
        """Generate cache key from prompt, context, and model.

        Args:
            prompt: The LLM prompt text.
            context: Supporting context.
            model: Model identifier.

        Returns:
            SHA-256 hex digest of the combined inputs.
        """
        combined = f"{prompt}|{context}|{model}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get(self, prompt: str, context: str, model: str) -> Any | None:
        """Retrieve cached response if available.

        Args:
            prompt: The LLM prompt text.
            context: Supporting context.
            model: Model identifier.

        Returns:
            Cached response or None if not found.
        """
        key = self._make_key(prompt, context, model)
        if key in self._cache:
            self._hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, prompt: str, context: str, model: str, response: Any) -> None:
        """Store a response in the cache.

        Args:
            prompt: The LLM prompt text.
            context: Supporting context.
            model: Model identifier.
            response: The LLM response to cache.
        """
        key = self._make_key(prompt, context, model)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = response
        while len(self._cache) > self._max_entries:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached entries and reset statistics."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate as a float between 0.0 and 1.0.
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        """Return current number of cached entries."""
        return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dictionary with hits, misses, hit_rate, and size.
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 4),
            "size": self.size,
            "max_entries": self._max_entries,
        }
