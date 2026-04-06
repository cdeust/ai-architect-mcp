"""Tiered symbol resolution with caching.

Resolution proceeds through four tiers of decreasing confidence:
1. Same-file symbols (highest confidence)
2. Named imports (explicit import-from)
3. Import-scoped (star/module imports)
4. Global fallback (lowest confidence)
"""

from __future__ import annotations

from dataclasses import dataclass

from .symbol_table import SymbolTable

SAME_FILE_CONFIDENCE: float = 1.0
NAMED_IMPORT_CONFIDENCE: float = 0.9
IMPORT_SCOPED_CONFIDENCE: float = 0.7
GLOBAL_CONFIDENCE: float = 0.3
CACHE_MAX_SIZE: int = 4096

_SENTINEL = object()


@dataclass(frozen=True)
class ResolutionResult:
    """Result of resolving a symbol name.

    Args:
        node_id: The resolved node's ID.
        tier: Which resolution tier matched.
        confidence: Confidence score for this resolution.
    """

    node_id: str
    tier: str
    confidence: float


class ResolutionContext:
    """Tiered symbol resolver with LRU-style cache.

    Resolves a symbol name within the context of a source file by
    checking four tiers in order: same_file, named_import,
    import_scoped, global.

    Args:
        symbol_table: The populated SymbolTable to resolve against.
        import_map: File -> list of imported file paths.
        named_imports: File -> {name: source_file} for explicit imports.
    """

    def __init__(
        self,
        symbol_table: SymbolTable,
        import_map: dict[str, list[str]] | None = None,
        named_imports: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self._table = symbol_table
        self._import_map = import_map or {}
        self._named_imports = named_imports or {}
        self._cache: dict[tuple[str, str], ResolutionResult | None] = {}

    def resolve(
        self, name: str, source_file: str,
    ) -> ResolutionResult | None:
        """Resolve a symbol name from the perspective of source_file.

        Args:
            name: Symbol name to resolve.
            source_file: File where the reference appears.

        Returns:
            ResolutionResult if found, None if unresolvable.
        """
        key = (source_file, name)
        if key in self._cache:
            return self._cache[key]

        result = self._resolve_uncached(name, source_file)
        self._put_cache(key, result)
        return result

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self._cache.clear()

    def _put_cache(
        self,
        key: tuple[str, str],
        value: ResolutionResult | None,
    ) -> None:
        """Insert into cache, evicting oldest entries at capacity."""
        if len(self._cache) >= CACHE_MAX_SIZE:
            excess = len(self._cache) - CACHE_MAX_SIZE + 1
            keys_to_remove = list(self._cache.keys())[:excess]
            for k in keys_to_remove:
                del self._cache[k]
        self._cache[key] = value

    def _resolve_uncached(
        self, name: str, source_file: str,
    ) -> ResolutionResult | None:
        """Walk through resolution tiers without caching."""
        # Tier 1: same file
        nodes = self._table.lookup_in_file(source_file, name)
        if nodes:
            return ResolutionResult(
                node_id=nodes[0].id,
                tier="same_file",
                confidence=SAME_FILE_CONFIDENCE,
            )

        # Tier 2: named import
        named = self._named_imports.get(source_file, {})
        if name in named:
            src_file = named[name]
            nodes = self._table.lookup_in_file(src_file, name)
            if nodes:
                return ResolutionResult(
                    node_id=nodes[0].id,
                    tier="named_import",
                    confidence=NAMED_IMPORT_CONFIDENCE,
                )

        # Tier 3: import-scoped
        imported_files = self._import_map.get(source_file, [])
        for imp_file in imported_files:
            nodes = self._table.lookup_in_file(imp_file, name)
            if nodes:
                return ResolutionResult(
                    node_id=nodes[0].id,
                    tier="import_scoped",
                    confidence=IMPORT_SCOPED_CONFIDENCE,
                )

        # Tier 4: global
        nodes = self._table.lookup_global(name)
        if nodes:
            return ResolutionResult(
                node_id=nodes[0].id,
                tier="global",
                confidence=GLOBAL_CONFIDENCE,
            )

        return None
