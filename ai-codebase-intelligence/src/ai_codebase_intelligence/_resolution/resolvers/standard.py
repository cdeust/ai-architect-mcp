"""Standard import resolver with FIFO cache and suffix-index lookup."""

from __future__ import annotations

import math
from collections import OrderedDict
from pathlib import PurePosixPath


class ResolutionCache:
    """FIFO cache with oldest-20% eviction at capacity.

    Args:
        max_size: Maximum number of entries before eviction triggers.
    """

    def __init__(self, max_size: int) -> None:
        self._max_size = max_size
        self._store: OrderedDict[str, str | None] = OrderedDict()

    def put(self, key: str, value: str | None) -> None:
        """Store a key-value pair, evicting oldest 20% if at capacity.

        Args:
            key: Cache key.
            value: Resolved path or None for negative caching.
        """
        if key in self._store:
            self._store[key] = value
            return

        if len(self._store) >= self._max_size:
            evict_count = max(1, math.ceil(self._max_size * 0.2))
            for _ in range(evict_count):
                self._store.popitem(last=False)

        self._store[key] = value

    def get(self, key: str) -> tuple[bool, str | None]:
        """Look up a cached resolution.

        Args:
            key: Cache key.

        Returns:
            Tuple of (hit, value). Miss returns (False, None).
        """
        if key in self._store:
            return True, self._store[key]
        return False, None

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._store)


class StandardResolver:
    """Resolve imports using suffix-index lookup with caching.

    Handles dotted imports (Python), relative imports (./), and
    TypeScript .tsx fallback.

    Args:
        suffix_index: Mapping from suffix keys to file path lists.
    """

    def __init__(self, suffix_index: dict[str, list[str]]) -> None:
        self._index = suffix_index
        self._cache = ResolutionCache(max_size=1024)

    def resolve(self, import_spec: str, current_file: str) -> str | None:
        """Resolve an import specifier to a file path.

        Args:
            import_spec: The import string (e.g. "utils", "pkg.helpers", "./Button").
            current_file: Path of the file containing the import.

        Returns:
            Resolved file path or None if unresolvable.
        """
        cache_key = f"{import_spec}:{current_file}"
        hit, cached = self._cache.get(cache_key)
        if hit:
            return cached

        result = self._do_resolve(import_spec, current_file)
        self._cache.put(cache_key, result)
        return result

    def _do_resolve(self, import_spec: str, current_file: str) -> str | None:
        """Internal resolution logic without caching."""
        if import_spec.startswith("./"):
            return self._resolve_relative(import_spec, current_file)
        return self._resolve_absolute(import_spec)

    def _resolve_relative(self, spec: str, current_file: str) -> str | None:
        """Resolve a relative import (starts with ./)."""
        current_dir = str(PurePosixPath(current_file).parent)
        bare = spec[2:]  # strip "./"
        candidate = f"{current_dir}/{bare}"

        # Try direct match in index
        result = self._lookup(candidate)
        if result is not None:
            return result

        # Try with .tsx extension for TypeScript
        tsx_key = f"{candidate}.tsx"
        for paths in self._index.values():
            for p in paths:
                if p.endswith(tsx_key) or p == tsx_key:
                    return p

        # Try bare name in index (parent/stem style)
        parent = PurePosixPath(current_dir).name
        key = f"{parent}/{bare}"
        result = self._lookup(key)
        if result is not None:
            return result

        # Try .tsx with parent/stem
        return self._lookup_tsx(key)

    def _resolve_absolute(self, spec: str) -> str | None:
        """Resolve a dotted or plain import."""
        # Convert dots to slashes for package imports
        key = spec.replace(".", "/")
        result = self._lookup(key)
        if result is not None:
            return result

        # Try bare stem (last component)
        stem = key.rsplit("/", 1)[-1]
        return self._lookup(stem)

    def _lookup(self, key: str) -> str | None:
        """Look up a key in the suffix index."""
        matches = self._index.get(key)
        if matches:
            return matches[0]
        return None

    def _lookup_tsx(self, key: str) -> str | None:
        """Try to find a .tsx file matching the key."""
        for idx_key, paths in self._index.items():
            if idx_key == key:
                for p in paths:
                    if p.endswith(".tsx"):
                        return p
        return None
