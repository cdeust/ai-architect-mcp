"""In-memory graph index for fast traversal.

Built from KnowledgeGraph. Provides O(1) neighbor lookup,
BFS traversal, and typed edge filtering. Uses GraphNode and
GraphRelationship typed models internally.
"""

from __future__ import annotations

from typing import Any

from ..._models.graph_types import GraphNode, GraphRelationship
from ..graph.graph import KnowledgeGraph


class GraphIndex:
    """Fast adjacency-list index over a KnowledgeGraph."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph
        self._nodes: dict[str, GraphNode] = {}
        self._out: dict[str, list[tuple[str, GraphRelationship]]] = {}
        self._in: dict[str, list[tuple[str, GraphRelationship]]] = {}
        self._by_name: dict[str, list[str]] = {}
        self._by_file: dict[str, list[str]] = {}
        self._build()

    def _build(self) -> None:
        """Build all indexes from the graph."""
        for node in self._graph.iter_nodes():
            self._nodes[node.id] = node
            if node.name:
                self._by_name.setdefault(node.name, []).append(node.id)
            if node.file_path:
                self._by_file.setdefault(node.file_path, []).append(node.id)

        for rel in self._graph.iter_relationships():
            self._out.setdefault(rel.source_id, []).append((rel.target_id, rel))
            self._in.setdefault(rel.target_id, []).append((rel.source_id, rel))

    def get_node(self, node_id: str) -> GraphNode | None:
        """O(1) node lookup."""
        return self._nodes.get(node_id)

    def find_by_name(self, name: str) -> list[GraphNode]:
        """Find all nodes with a given name."""
        return [
            self._nodes[nid]
            for nid in self._by_name.get(name, [])
            if nid in self._nodes
        ]

    def find_by_file(self, file_path: str) -> list[GraphNode]:
        """Find all nodes in a file."""
        return [
            self._nodes[nid]
            for nid in self._by_file.get(file_path, [])
            if nid in self._nodes
        ]

    def outgoing(
        self, node_id: str, rel_type: str | None = None,
    ) -> list[tuple[GraphNode, GraphRelationship]]:
        """Get outgoing (node, rel) pairs. Optionally filter by type."""
        results: list[tuple[GraphNode, GraphRelationship]] = []
        for tgt_id, rel in self._out.get(node_id, []):
            if rel_type and rel.relationship_type.value != rel_type:
                continue
            tgt = self._nodes.get(tgt_id)
            if tgt:
                results.append((tgt, rel))
        return results

    def incoming(
        self, node_id: str, rel_type: str | None = None,
    ) -> list[tuple[GraphNode, GraphRelationship]]:
        """Get incoming (node, rel) pairs. Optionally filter by type."""
        results: list[tuple[GraphNode, GraphRelationship]] = []
        for src_id, rel in self._in.get(node_id, []):
            if rel_type and rel.relationship_type.value != rel_type:
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

        Returns list of {depth, id, name, label, filePath, relationType, confidence}.
        """
        visited: set[str] = {start_id}
        frontier = [start_id]
        results: list[dict[str, Any]] = []

        for depth in range(1, max_depth + 1):
            if not frontier:
                break
            next_frontier: list[str] = []
            for nid in frontier:
                edges = self._edges_for(nid, direction)
                for other_id, rel in edges:
                    rtype = rel.relationship_type.value
                    if rel_types and rtype not in rel_types:
                        continue
                    if rel.confidence < min_confidence:
                        continue
                    if other_id in visited:
                        continue
                    visited.add(other_id)
                    next_frontier.append(other_id)
                    node = self._nodes.get(other_id)
                    results.append({
                        "depth": depth,
                        "id": other_id,
                        "name": node.name if node else "",
                        "label": node.label.value if node else "",
                        "filePath": node.file_path if node else "",
                        "relationType": rtype,
                        "confidence": rel.confidence,
                    })
            frontier = next_frontier
        return results

    def _edges_for(
        self, node_id: str, direction: str,
    ) -> list[tuple[str, GraphRelationship]]:
        """Get edges for a node in a given direction."""
        if direction == "outgoing":
            return self._out.get(node_id, [])
        if direction == "incoming":
            return self._in.get(node_id, [])
        return self._out.get(node_id, []) + self._in.get(node_id, [])

    def caller_count(self, node_id: str) -> int:
        """Count incoming CALLS edges."""
        return sum(
            1 for _, r in self._in.get(node_id, [])
            if r.relationship_type.value == "CALLS"
        )

    def callee_count(self, node_id: str) -> int:
        """Count outgoing CALLS edges."""
        return sum(
            1 for _, r in self._out.get(node_id, [])
            if r.relationship_type.value == "CALLS"
        )

    def get_processes_for_node(self, node_id: str) -> list[dict[str, Any]]:
        """Get processes a node participates in via STEP_IN_PROCESS."""
        results: list[dict[str, Any]] = []
        for proc_id, rel in self._out.get(node_id, []):
            if rel.relationship_type.value != "STEP_IN_PROCESS":
                continue
            proc = self._nodes.get(proc_id)
            if not proc:
                continue
            results.append({
                "id": proc_id,
                "label": proc.properties.get("heuristicLabel", proc.name),
                "step": rel.properties.get("step", 0),
                "stepCount": proc.properties.get("stepCount", 0),
            })
        return results

    def get_community_for_node(self, node_id: str) -> dict[str, Any] | None:
        """Get the community a node belongs to via MEMBER_OF."""
        for comm_id, rel in self._out.get(node_id, []):
            if rel.relationship_type.value != "MEMBER_OF":
                continue
            comm = self._nodes.get(comm_id)
            if not comm:
                continue
            return {
                "id": comm_id,
                "label": comm.properties.get("heuristicLabel", comm.name),
                "cohesion": comm.properties.get("cohesion", 0),
            }
        return None

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def relationship_count(self) -> int:
        return sum(len(edges) for edges in self._out.values())
