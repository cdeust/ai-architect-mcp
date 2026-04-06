"""In-memory BM25-like text search over graph nodes.

Scores nodes by matching query terms against name, signature, and
docstring fields with configurable weights.
"""

from __future__ import annotations

from .._models.graph_types import GraphNode
from .._models.search_types import BM25Result

_NAME_WEIGHT: float = 3.0
_NAME_EXACT_BONUS: float = 5.0
_SIGNATURE_WEIGHT: float = 2.0
_DOCSTRING_WEIGHT: float = 1.0

_DEFAULT_LIMIT: int = 50


def search_nodes(
    query: str,
    nodes: dict[str, GraphNode],
    limit: int = _DEFAULT_LIMIT,
) -> list[BM25Result]:
    """Search nodes by matching query against name, signature, docstring.

    Scoring: exact name match gets a bonus. Partial name match, signature
    match, and docstring match each contribute weighted scores.

    Args:
        query: Search query string.
        nodes: Node dict keyed by node ID.
        limit: Maximum number of results to return.

    Returns:
        BM25Result list sorted by score descending.
    """
    if not query or not nodes:
        return []

    query_lower = query.lower()
    results: list[BM25Result] = []

    for node_id, node in nodes.items():
        score = 0.0
        matched_field = ""

        name_lower = node.name.lower()
        if query_lower in name_lower:
            score += _NAME_WEIGHT
            matched_field = "name"
            if name_lower == query_lower:
                score += _NAME_EXACT_BONUS

        sig_lower = node.signature.lower()
        if sig_lower and query_lower in sig_lower:
            score += _SIGNATURE_WEIGHT
            if not matched_field:
                matched_field = "signature"

        doc_lower = node.docstring.lower()
        if doc_lower and query_lower in doc_lower:
            score += _DOCSTRING_WEIGHT
            if not matched_field:
                matched_field = "docstring"

        if score > 0.0:
            results.append(BM25Result(
                node_id=node_id,
                score=score,
                matched_field=matched_field,
                snippet=node.name,
                table_name=node.label.value,
            ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
