"""In-memory concrete adapter implementing GraphStoragePort.

Test double — no I/O, no dependencies. Used in unit tests to
verify pipeline logic without touching SQLite.
"""

from __future__ import annotations

from .ports import GraphStoragePort
from .._models.graph_types import GraphNode, GraphRelationship


class InMemoryGraphStorage(GraphStoragePort):
    """In-memory graph storage for testing."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._rels: list[GraphRelationship] = []

    def initialize(self) -> None:
        """No-op for in-memory storage."""

    def store_nodes(self, nodes: list[GraphNode]) -> int:
        for n in nodes:
            self._nodes[n.id] = n
        return len(nodes)

    def store_relationships(self, relationships: list[GraphRelationship]) -> int:
        self._rels.extend(relationships)
        return len(relationships)

    def load_all_nodes(self) -> list[GraphNode]:
        return list(self._nodes.values())

    def load_all_relationships(self) -> list[GraphRelationship]:
        return list(self._rels)

    def get_stats(self) -> dict[str, int]:
        return {"nodes": len(self._nodes), "edges": len(self._rels)}

    def close(self) -> None:
        self._nodes.clear()
        self._rels = []
