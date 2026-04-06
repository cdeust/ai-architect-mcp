"""Augmentation engine — enrich search results with graph data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

MAX_ENRICHMENT_BATCH = 100


class AugmentationStorage(Protocol):
    """Port for graph storage used by augmentation."""

    async def query_cypher(
        self, query: str, params: dict[str, object] | None = None,
    ) -> list[dict[str, object]]: ...


@dataclass
class GrepResult:
    """A single grep match."""

    file_path: str
    line_number: int
    line_content: str
    match_text: str = ""


@dataclass
class GlobResult:
    """A single glob match."""

    file_path: str
    file_name: str
    file_size: int


@dataclass
class EnrichedGrepResult:
    """A grep result enriched with symbol information."""

    file_path: str
    line_number: int
    line_content: str
    match_text: str
    symbol_name: str
    symbol_kind: str


@dataclass
class EnrichedGlobResult:
    """A glob result enriched with module statistics."""

    file_path: str
    file_name: str
    file_size: int
    symbol_count: int
    languages: list[str] = field(default_factory=list)


async def augment_grep_results(
    results: list[GrepResult],
    storage: AugmentationStorage,
) -> list[EnrichedGrepResult]:
    """Enrich grep results with symbol data from the graph.

    Args:
        results: Raw grep results.
        storage: Graph storage backend.

    Returns:
        Enriched results with symbol name and kind when available.
    """
    if not results:
        return []

    enriched: list[EnrichedGrepResult] = []
    for result in results:
        symbol_name = ""
        symbol_kind = ""

        if result.match_text:
            rows = await storage.query_cypher(
                "MATCH (s) WHERE s.name = $name "
                "RETURN s.name AS name, s.kind AS kind LIMIT 1",
                {"name": result.match_text},
            )
            if rows:
                symbol_name = str(rows[0].get("name", ""))
                symbol_kind = str(rows[0].get("kind", ""))

        enriched.append(EnrichedGrepResult(
            file_path=result.file_path,
            line_number=result.line_number,
            line_content=result.line_content,
            match_text=result.match_text,
            symbol_name=symbol_name,
            symbol_kind=symbol_kind,
        ))

    return enriched


async def augment_glob_results(
    results: list[GlobResult],
    storage: AugmentationStorage,
) -> list[EnrichedGlobResult]:
    """Enrich glob results with module statistics from the graph.

    Args:
        results: Raw glob results.
        storage: Graph storage backend.

    Returns:
        Enriched results with symbol count and language info.
    """
    if not results:
        return []

    enriched: list[EnrichedGlobResult] = []
    for result in results:
        rows = await storage.query_cypher(
            "MATCH (f:File {filePath: $fp})-[:DEFINES]->(s) "
            "RETURN count(s) AS cnt, collect(DISTINCT s.language) AS langs",
            {"fp": result.file_path},
        )
        symbol_count = 0
        languages: list[str] = []
        if rows:
            symbol_count = int(rows[0].get("cnt", 0))
            raw_langs = rows[0].get("langs", [])
            languages = list(raw_langs) if isinstance(raw_langs, list) else []

        enriched.append(EnrichedGlobResult(
            file_path=result.file_path,
            file_name=result.file_name,
            file_size=result.file_size,
            symbol_count=symbol_count,
            languages=languages,
        ))

    return enriched
