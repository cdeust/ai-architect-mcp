"""Knowledge graph — typed in-memory graph.

Stores GraphNode and GraphRelationship typed models internally.
All callers must pass typed models directly.
"""

from __future__ import annotations

from typing import Callable, Iterator

from ..._models.graph_types import GraphNode, GraphRelationship


class KnowledgeGraph:
    """In-memory knowledge graph with typed storage.

    Internal storage uses GraphNode and GraphRelationship models.
    """

    def __init__(self) -> None:
        self._node_map: dict[str, GraphNode] = {}
        self._relationship_map: dict[str, GraphRelationship] = {}

    def add_node(self, node: GraphNode) -> None:
        """Add a node.

        Args:
            node: GraphNode instance.
        """
        if node.id not in self._node_map:
            self._node_map[node.id] = node

    def add_relationship(self, relationship: GraphRelationship) -> None:
        """Add a relationship.

        Args:
            relationship: GraphRelationship instance.
        """
        rel_id = f"{relationship.source_id}->{relationship.target_id}"
        if rel_id not in self._relationship_map:
            self._relationship_map[rel_id] = relationship

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its relationships."""
        if node_id not in self._node_map:
            return False
        del self._node_map[node_id]
        to_remove = [
            rel_id
            for rel_id, rel in self._relationship_map.items()
            if rel.source_id == node_id or rel.target_id == node_id
        ]
        for rel_id in to_remove:
            del self._relationship_map[rel_id]
        return True

    def remove_nodes_by_file(self, file_path: str) -> int:
        """Remove all nodes from a given file path."""
        node_ids = [
            nid for nid, node in self._node_map.items()
            if node.file_path == file_path
        ]
        for nid in node_ids:
            self.remove_node(nid)
        return len(node_ids)

    def iter_nodes(self) -> Iterator[GraphNode]:
        """Iterate over all nodes as typed GraphNode objects."""
        return iter(self._node_map.values())

    def iter_relationships(self) -> Iterator[GraphRelationship]:
        """Iterate over all relationships as typed objects."""
        return iter(self._relationship_map.values())

    def get_node(self, node_id: str) -> GraphNode | None:
        """O(1) node lookup by ID."""
        return self._node_map.get(node_id)

    def for_each_node(self, fn: Callable[[GraphNode], None]) -> None:
        """Apply a function to each node."""
        for node in self._node_map.values():
            fn(node)

    def for_each_relationship(self, fn: Callable[[GraphRelationship], None]) -> None:
        """Apply a function to each relationship."""
        for rel in self._relationship_map.values():
            fn(rel)

    @property
    def nodes(self) -> list[GraphNode]:
        """All nodes as a list."""
        return list(self._node_map.values())

    @property
    def relationships(self) -> list[GraphRelationship]:
        """All relationships as a list."""
        return list(self._relationship_map.values())

    @property
    def node_count(self) -> int:
        return len(self._node_map)

    @property
    def relationship_count(self) -> int:
        return len(self._relationship_map)


def create_knowledge_graph() -> KnowledgeGraph:
    """Factory for backward compatibility."""
    return KnowledgeGraph()
