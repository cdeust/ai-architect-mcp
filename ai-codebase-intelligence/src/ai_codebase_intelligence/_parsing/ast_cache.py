"""LRU AST cache with eviction tracking.

Wraps an OrderedDict to provide O(1) LRU eviction with cache
statistics (hits, misses, evictions). Used by the parsing pipeline
to avoid re-parsing unchanged files.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from pydantic import BaseModel, Field


class CacheStats(BaseModel):
    """Running statistics for an ASTCache instance.

    Args:
        hits: Number of cache hits.
        misses: Number of cache misses.
        evictions: Number of LRU evictions.
    """

    hits: int = Field(default=0, description="Number of cache hits")
    misses: int = Field(default=0, description="Number of cache misses")
    evictions: int = Field(default=0, description="Number of LRU evictions")

    @property
    def hit_rate(self) -> float:
        """Return the cache hit rate as a float in [0.0, 1.0]."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class ASTCache:
    """LRU cache for parsed AST trees.

    Args:
        max_size: Maximum number of entries. Must be >= 1.

    Raises:
        ValueError: If max_size < 1.
    """

    def __init__(self, max_size: int) -> None:
        if max_size < 1:
            msg = f"max_size must be >= 1, got {max_size}"
            raise ValueError(msg)
        self._max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._stats = CacheStats()

    @property
    def max_size(self) -> int:
        """Return the maximum cache capacity."""
        return self._max_size

    @property
    def stats(self) -> CacheStats:
        """Return current cache statistics."""
        return self._stats

    def get(self, path: str) -> Any | None:
        """Return the cached tree for *path*, or None on miss.

        A hit moves the entry to the most-recently-used position.

        Args:
            path: File path key.

        Returns:
            The cached AST tree, or None if not present.
        """
        if path in self._cache:
            self._cache.move_to_end(path)
            self._stats.hits += 1
            return self._cache[path]
        self._stats.misses += 1
        return None

    def put(self, path: str, tree: Any) -> None:
        """Store *tree* under *path*, evicting LRU if at capacity.

        Updating an existing key replaces the value without changing
        the cache size.

        Args:
            path: File path key.
            tree: Parsed AST tree object.
        """
        if path in self._cache:
            self._cache.move_to_end(path)
            self._cache[path] = tree
            return
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
            self._stats.evictions += 1
        self._cache[path] = tree

    def contains(self, path: str) -> bool:
        """Check membership without affecting LRU order.

        Args:
            path: File path key.

        Returns:
            True if *path* is cached.
        """
        return path in self._cache

    def clear(self) -> None:
        """Remove all entries and reset statistics."""
        self._cache.clear()
        self._stats = CacheStats()

    def resize(self, new_size: int) -> None:
        """Change the cache capacity.

        If *new_size* is smaller than the current entry count, the
        least-recently-used entries are evicted.

        Args:
            new_size: New maximum capacity. Must be >= 1.

        Raises:
            ValueError: If new_size < 1.
        """
        if new_size < 1:
            msg = f"max_size must be >= 1, got {new_size}"
            raise ValueError(msg)
        self._max_size = new_size
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
            self._stats.evictions += 1

    def __len__(self) -> int:
        return len(self._cache)
