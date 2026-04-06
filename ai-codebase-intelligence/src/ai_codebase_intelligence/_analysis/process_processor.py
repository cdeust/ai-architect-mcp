"""Process detection via BFS from scored entry points.

Traces call chains from high-scoring entry point nodes using
breadth-first search. Produces ProcessTrace objects with depth
maps and deduplication.
"""

from __future__ import annotations

from collections import deque

from pydantic import BaseModel, Field

from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)
from ai_codebase_intelligence._analysis.entry_point_scoring import (
    score_entry_point,
)

MAX_BFS_DEPTH = 10
MAX_BRANCHING = 4
MIN_ENTRY_SCORE = 1.5


class ProcessTrace(BaseModel):
    """A detected process trace from entry point through call chain.

    Args:
        entry_point_id: ID of the entry point node.
        entry_point_name: Name of the entry point node.
        members: All node IDs in the process trace.
        depth_map: Mapping of node_id to depth from entry.
        score: Entry point score for ranking.
    """

    entry_point_id: str = Field(description="Entry point node ID")
    entry_point_name: str = Field(description="Entry point node name")
    members: list[str] = Field(
        default_factory=list, description="All node IDs in trace",
    )
    depth_map: dict[str, int] = Field(
        default_factory=dict, description="node_id -> depth from entry",
    )
    score: float = Field(default=0.0, description="Entry point score")


def detect_processes(
    nodes: list[GraphNode],
    rels: list[GraphRelationship],
    call_counts: dict[str, tuple[int, int]],
) -> list[ProcessTrace]:
    """Detect processes by BFS from scored entry points.

    Args:
        nodes: All graph nodes.
        rels: All graph relationships.
        call_counts: {node_id: (caller_count, callee_count)}.

    Returns:
        List of ProcessTrace sorted by score descending, deduplicated.
    """
    if not nodes or not rels:
        return []

    node_map: dict[str, GraphNode] = {n.id: n for n in nodes}
    calls_adj = _build_calls_adjacency(rels)

    entry_candidates = _find_entry_points(
        nodes, call_counts, calls_adj,
    )

    traces: list[ProcessTrace] = []
    for node_id, ep_score in entry_candidates:
        node = node_map[node_id]
        trace = _bfs_trace(node_id, calls_adj)
        if len(trace.members) < 2:
            continue
        trace.entry_point_name = node.name
        trace.entry_point_id = node_id
        trace.score = ep_score
        traces.append(trace)

    traces.sort(key=lambda t: t.score, reverse=True)
    return _deduplicate(traces)


def _build_calls_adjacency(
    rels: list[GraphRelationship],
) -> dict[str, list[str]]:
    """Build forward call adjacency from CALLS relationships.

    Args:
        rels: All relationships.

    Returns:
        Dict mapping source_id to list of target_ids for CALLS edges.
    """
    adj: dict[str, list[str]] = {}
    for r in rels:
        if r.relationship_type == RelationshipType.CALLS:
            adj.setdefault(r.source_id, []).append(r.target_id)
    return adj


def _find_entry_points(
    nodes: list[GraphNode],
    call_counts: dict[str, tuple[int, int]],
    calls_adj: dict[str, list[str]],
) -> list[tuple[str, float]]:
    """Score and filter entry point candidates.

    Only FUNCTION nodes with outgoing calls and score >= MIN_ENTRY_SCORE
    are considered.

    Args:
        nodes: All graph nodes.
        call_counts: {node_id: (caller_count, callee_count)}.
        calls_adj: Forward call adjacency.

    Returns:
        List of (node_id, score) sorted by score descending.
    """
    candidates: list[tuple[str, float]] = []

    for node in nodes:
        if node.label != NodeLabel.FUNCTION:
            continue
        if node.id not in calls_adj:
            continue

        caller_count, callee_count = call_counts.get(node.id, (0, 0))
        if callee_count == 0:
            continue

        result = score_entry_point(node, caller_count, callee_count)
        if result.total_score >= MIN_ENTRY_SCORE:
            candidates.append((node.id, result.total_score))

    candidates.sort(key=lambda c: c[1], reverse=True)
    return candidates


def _bfs_trace(
    entry_id: str,
    calls_adj: dict[str, list[str]],
) -> ProcessTrace:
    """BFS from an entry point, respecting depth and branching limits.

    Args:
        entry_id: Starting node ID.
        calls_adj: Forward call adjacency.

    Returns:
        ProcessTrace with members and depth_map populated.
    """
    visited: set[str] = set()
    depth_map: dict[str, int] = {}
    members: list[str] = []

    queue: deque[tuple[str, int]] = deque([(entry_id, 0)])
    visited.add(entry_id)

    while queue:
        current, depth = queue.popleft()
        members.append(current)
        depth_map[current] = depth

        if depth >= MAX_BFS_DEPTH:
            continue

        callees = calls_adj.get(current, [])
        added = 0
        for callee in callees:
            if callee in visited:
                continue
            if added >= MAX_BRANCHING:
                break
            visited.add(callee)
            queue.append((callee, depth + 1))
            added += 1

    return ProcessTrace(
        entry_point_id=entry_id,
        entry_point_name="",
        members=members,
        depth_map=depth_map,
    )


def _deduplicate(traces: list[ProcessTrace]) -> list[ProcessTrace]:
    """Remove traces whose member set is a subset of another.

    Args:
        traces: Sorted traces (highest score first).

    Returns:
        Deduplicated list preserving order.
    """
    result: list[ProcessTrace] = []
    member_sets: list[set[str]] = []

    for trace in traces:
        current_set = set(trace.members)
        is_subset = any(current_set <= existing for existing in member_sets)
        if not is_subset:
            result.append(trace)
            member_sets.append(current_set)

    return result
