"""Unified search engine — BM25 + process boost + community cohesion.

Orchestrates in-memory text search, RRF fusion, process membership
boosting, and community cohesion scoring into a single search call.
"""

from __future__ import annotations

from typing import Any

from .._models.graph_types import GraphNode
from .._models.search_types import HybridSearchResult, SearchResultKind
from .._storage.in_memory_graph import InMemoryGraphStorage
from .hybrid_search import _build_ranked_items, _compute_rrf
from .in_memory_search import search_nodes

_DEFAULT_LIMIT: int = 20
_PROCESS_BOOST: float = 0.1


async def search(
    query: str,
    storage: InMemoryGraphStorage,
    nodes: dict[str, GraphNode] | None = None,
    process_members: dict[str, list[str]] | None = None,
    community_cohesion: dict[str, float] | None = None,
    node_community: dict[str, str] | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> list[HybridSearchResult]:
    """Run hybrid search combining BM25, process boost, and cohesion.

    Args:
        query: Search query string.
        storage: Graph storage instance (used for future embedding lookup).
        nodes: Node dict keyed by node ID. Falls back to storage if None.
        process_members: Mapping of process label to member node IDs.
        community_cohesion: Mapping of community ID to cohesion score.
        node_community: Mapping of node ID to community ID.
        limit: Maximum results to return.

    Returns:
        List of HybridSearchResult sorted by final score descending.
    """
    if not query:
        return []

    search_nodes_dict = nodes if nodes is not None else {}

    bm25_results = search_nodes(query, search_nodes_dict)
    if not bm25_results:
        return []

    ranked = _build_ranked_items(bm25_results)
    rrf_scores = _compute_rrf(ranked)

    bm25_by_id = {r.node_id: r for r in bm25_results}
    process_map = _build_process_map(process_members)

    results: list[HybridSearchResult] = []
    for node_id, rrf_score in rrf_scores.items():
        bm25 = bm25_by_id[node_id]
        node = search_nodes_dict.get(node_id)

        process_score = 0.0
        processes: list[str] = []
        if node_id in process_map:
            processes = process_map[node_id]
            process_score = len(processes) * _PROCESS_BOOST

        cohesion = 0.0
        community = ""
        if node_community and node_id in node_community:
            community = node_community[node_id]
            if community_cohesion and community in community_cohesion:
                cohesion = community_cohesion[community]

        results.append(HybridSearchResult(
            node_id=node_id,
            name=node.name if node else "",
            kind=SearchResultKind.SYMBOL,
            file_path=node.file_path if node else "",
            rrf_score=rrf_score,
            bm25_score=bm25.score,
            process_score=process_score,
            processes=processes,
            community=community,
            cohesion_score=cohesion,
        ))

    final_score = _final_sort_key(community_cohesion is not None)
    results.sort(key=final_score, reverse=True)
    return results[:limit]


def _build_process_map(
    process_members: dict[str, list[str]] | None,
) -> dict[str, list[str]]:
    """Invert process_members into a node_id -> [process_label] map.

    Args:
        process_members: Mapping of process label to member node IDs.

    Returns:
        Mapping of node_id to list of process labels it belongs to.
    """
    if not process_members:
        return {}
    result: dict[str, list[str]] = {}
    for label, members in process_members.items():
        for node_id in members:
            result.setdefault(node_id, []).append(label)
    return result


def _final_sort_key(
    use_cohesion: bool,
) -> Any:
    """Return a sort key function based on scoring mode.

    Args:
        use_cohesion: Whether to include cohesion in the sort key.

    Returns:
        Callable that extracts the sort key from a HybridSearchResult.
    """
    if use_cohesion:
        return lambda r: r.rrf_score + r.process_score + r.cohesion_score
    return lambda r: r.rrf_score + r.process_score
