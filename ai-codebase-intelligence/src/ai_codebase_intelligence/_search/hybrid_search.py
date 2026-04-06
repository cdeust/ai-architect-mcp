"""Reciprocal Rank Fusion for hybrid search.

Implements RRF (Cormack et al. 2009) to combine BM25 text scores
with process-membership rankings into a single fused score.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .._models.search_types import BM25Result

RRF_K: int = 60
"""RRF smoothing constant (Cormack et al. 2009, Section 3)."""


class RankedItem(BaseModel):
    """A ranked search item with position and metadata.

    Args:
        rank: 0-based rank position.
        score: Original retriever score.
        metadata: Extra data from the source result.
    """

    rank: int = Field(description="0-based rank position")
    score: float = Field(default=0.0, description="Original score")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Source result metadata",
    )


def _build_ranked_items(bm25_results: list[BM25Result]) -> dict[str, RankedItem]:
    """Convert BM25 results into ranked items keyed by node ID.

    Results are ranked by descending score. Each item stores its
    0-based rank and metadata extracted from the BM25 result.

    Args:
        bm25_results: BM25 search results sorted by score descending.

    Returns:
        Mapping of node_id to RankedItem.
    """
    sorted_results = sorted(bm25_results, key=lambda r: r.score, reverse=True)
    ranked: dict[str, RankedItem] = {}
    for rank, result in enumerate(sorted_results):
        metadata: dict[str, Any] = {}
        if result.snippet:
            metadata["name"] = result.snippet
        if result.table_name:
            metadata["table_name"] = result.table_name
        ranked[result.node_id] = RankedItem(
            rank=rank,
            score=result.score,
            metadata=metadata if metadata else None,
        )
    return ranked


def _compute_rrf(ranked: dict[str, RankedItem]) -> dict[str, float]:
    """Compute RRF scores from ranked items.

    Formula: score(d) = 1 / (K + rank + 1) for each document d.

    Args:
        ranked: Mapping of node_id to RankedItem.

    Returns:
        Mapping of node_id to RRF score.
    """
    scores: dict[str, float] = {}
    for node_id, item in ranked.items():
        scores[node_id] = 1.0 / (RRF_K + item.rank + 1)
    return scores
