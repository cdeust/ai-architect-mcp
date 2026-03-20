"""In-memory graph index for fast traversal.

Built from KnowledgeGraph. Provides O(1) neighbor lookup,
BFS traversal, and typed edge filtering. This replaces
KuzuDB Cypher queries for all graph operations.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from ..graph.graph import KnowledgeGraph


class GraphIndex:
    """Fast adjacency-list index over a KnowledgeGraph."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph
        # node_id -> node dict
        self._nodes: dict[str, dict[str, Any]] = {}
        # outgoing: source_id -> [(target_id, rel)]
        self._out: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        # incoming: target_id -> [(source_id, rel)]
        self._in: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        # name -> [node_ids]  (for symbol lookup)
        self._by_name: dict[str, list[str]] = {}
        # filePath -> [node_ids]
        self._by_file: dict[str, list[str]] = {}

        self._build()

    def _build(self) -> None:
        """Build all indexes from the graph."""
        for node in self._graph.iter_nodes():
            nid = node["id"]
            self._nodes[nid] = node
            props = node.get("properties", {})
            name = props.get("name", "")
            if name:
                self._by_name.setdefault(name, []).append(nid)
            fp = props.get("filePath", "")
            if fp:
                self._by_file.setdefault(fp, []).append(nid)

        for rel in self._graph.iter_relationships():
            src = rel.get("sourceId", "")
            tgt = rel.get("targetId", "")
            self._out.setdefault(src, []).append((tgt, rel))
            self._in.setdefault(tgt, []).append((src, rel))

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """O(1) node lookup."""
        return self._nodes.get(node_id)

    def find_by_name(self, name: str) -> list[dict[str, Any]]:
        """Find all nodes with a given name."""
        return [self._nodes[nid] for nid in self._by_name.get(name, []) if nid in self._nodes]

    def find_by_file(self, file_path: str) -> list[dict[str, Any]]:
        """Find all nodes in a file."""
        return [self._nodes[nid] for nid in self._by_file.get(file_path, []) if nid in self._nodes]

    def outgoing(
        self, node_id: str, rel_type: str | None = None
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """Get outgoing (node, rel) pairs. Optionally filter by type."""
        results = []
        for tgt_id, rel in self._out.get(node_id, []):
            if rel_type and rel.get("type") != rel_type:
                continue
            tgt = self._nodes.get(tgt_id)
            if tgt:
                results.append((tgt, rel))
        return results

    def incoming(
        self, node_id: str, rel_type: str | None = None
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """Get incoming (node, rel) pairs. Optionally filter by type."""
        results = []
        for src_id, rel in self._in.get(node_id, []):
            if rel_type and rel.get("type") != rel_type:
                continue
            src = self._nodes.get(src_id)
            if src:
                results.append((src, rel))
        return results

    def bfs(
        self,
        start_id: str,
        direction: str = "outgoing",
        rel_types: list[str] | None = None,
        max_depth: int = 3,
        min_confidence: float = 0.0,
    ) -> list[dict[str, Any]]:
        """BFS traversal from a starting node.

        Returns list of {depth, id, name, filePath, relationType, confidence}.
        """
        visited: set[str] = {start_id}
        frontier = [start_id]
        results: list[dict[str, Any]] = []

        for depth in range(1, max_depth + 1):
            if not frontier:
                break
            next_frontier: list[str] = []
            for nid in frontier:
                edges = (
                    self._out.get(nid, []) if direction == "outgoing"
                    else self._in.get(nid, []) if direction == "incoming"
                    else self._out.get(nid, []) + self._in.get(nid, [])
                )
                for other_id, rel in edges:
                    # For incoming edges, other_id is the source
                    actual_id = other_id
                    if rel_types and rel.get("type") not in rel_types:
                        continue
                    if rel.get("confidence", 1.0) < min_confidence:
                        continue
                    if actual_id in visited:
                        continue
                    visited.add(actual_id)
                    next_frontier.append(actual_id)
                    node = self._nodes.get(actual_id, {})
                    props = node.get("properties", {})
                    results.append({
                        "depth": depth,
                        "id": actual_id,
                        "name": props.get("name", ""),
                        "label": node.get("label", ""),
                        "filePath": props.get("filePath", ""),
                        "relationType": rel.get("type", ""),
                        "confidence": rel.get("confidence", 1.0),
                    })
            frontier = next_frontier

        return results

    def caller_count(self, node_id: str) -> int:
        """Count incoming CALLS edges."""
        return sum(1 for _, r in self._in.get(node_id, []) if r.get("type") == "CALLS")

    def callee_count(self, node_id: str) -> int:
        """Count outgoing CALLS edges."""
        return sum(1 for _, r in self._out.get(node_id, []) if r.get("type") == "CALLS")

    def get_processes_for_node(self, node_id: str) -> list[dict[str, Any]]:
        """Get processes a node participates in via STEP_IN_PROCESS."""
        results = []
        for proc_id, rel in self._out.get(node_id, []):
            if rel.get("type") != "STEP_IN_PROCESS":
                continue
            proc = self._nodes.get(proc_id, {})
            props = proc.get("properties", {})
            results.append({
                "id": proc_id,
                "label": props.get("heuristicLabel", props.get("name", "")),
                "step": rel.get("step", 0),
                "stepCount": props.get("stepCount", 0),
            })
        return results

    def get_community_for_node(self, node_id: str) -> dict[str, Any] | None:
        """Get the community a node belongs to via MEMBER_OF."""
        for comm_id, rel in self._out.get(node_id, []):
            if rel.get("type") != "MEMBER_OF":
                continue
            comm = self._nodes.get(comm_id, {})
            props = comm.get("properties", {})
            return {
                "id": comm_id,
                "label": props.get("heuristicLabel", props.get("name", "")),
                "cohesion": props.get("cohesion", 0),
            }
        return None

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def relationship_count(self) -> int:
        return sum(len(edges) for edges in self._out.values())
