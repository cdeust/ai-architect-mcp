"""In-memory graph storage — async test double for GraphStoragePort.

Uses typed GraphNode and GraphRelationship models. Supports neighbor
traversal with direction and type filtering.
"""

from __future__ import annotations

from typing import Any

from .._models.graph_types import GraphNode, GraphRelationship


class InMemoryGraphStorage:
    """Async in-memory graph storage for testing.

    Stores typed GraphNode and GraphRelationship models. Supports
    neighbor traversal, clear, and basic cypher stub.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._rels: list[GraphRelationship] = []
        self._embeddings: dict[str, list[float]] = {}
        self._embedding_model: str = ""

    async def initialize(self) -> None:
        """Initialize storage. No-op for in-memory backend."""

    async def store_nodes(self, nodes: list[GraphNode]) -> int:
        """Store nodes by ID. Idempotent.

        Args:
            nodes: GraphNode instances to store.

        Returns:
            Number of nodes stored.
        """
        for n in nodes:
            self._nodes[n.id] = n
        return len(nodes)

    async def store_relationships(self, relationships: list[GraphRelationship]) -> int:
        """Store relationships. Appends to list.

        Args:
            relationships: GraphRelationship instances to store.

        Returns:
            Number of relationships stored.
        """
        self._rels.extend(relationships)
        return len(relationships)

    async def get_node(self, node_id: str) -> GraphNode | None:
        """Retrieve a node by ID.

        Args:
            node_id: Node identifier.

        Returns:
            GraphNode if found, None otherwise.
        """
        return self._nodes.get(node_id)

    async def node_count(self) -> int:
        """Count stored nodes."""
        return len(self._nodes)

    async def relationship_count(self) -> int:
        """Count stored relationships."""
        return len(self._rels)

    async def get_neighbors(
        self,
        node_id: str,
        direction: str = "outgoing",
        relationship_type: str | None = None,
    ) -> list[tuple[GraphRelationship, GraphNode]]:
        """Get neighboring nodes with their connecting relationships.

        Args:
            node_id: Starting node ID.
            direction: "outgoing", "incoming", or "both".
            relationship_type: Optional filter by relationship type value.

        Returns:
            List of (relationship, neighbor_node) tuples.
        """
        results: list[tuple[GraphRelationship, GraphNode]] = []
        for rel in self._rels:
            neighbor_id = _match_direction(rel, node_id, direction)
            if neighbor_id is None:
                continue
            if relationship_type and rel.relationship_type.value != relationship_type:
                continue
            neighbor = self._nodes.get(neighbor_id)
            if neighbor:
                results.append((rel, neighbor))
        return results

    async def store_embeddings(
        self, embeddings: dict[str, list[float]], model_name: str,
    ) -> int:
        """Store embedding vectors.

        Args:
            embeddings: Mapping of node_id -> vector.
            model_name: Name of the embedding model used.

        Returns:
            Number of embeddings stored.
        """
        self._embeddings.update(embeddings)
        self._embedding_model = model_name
        return len(embeddings)

    async def clear(self) -> None:
        """Remove all nodes, relationships, and embeddings."""
        self._nodes.clear()
        self._rels.clear()
        self._embeddings.clear()
        self._embedding_model = ""

    async def query_cypher(self, query: str) -> Any:
        """Not supported for in-memory storage.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Cypher queries not supported in-memory")


def _match_direction(
    rel: GraphRelationship, node_id: str, direction: str,
) -> str | None:
    """Return the neighbor ID if the relationship matches the direction."""
    if direction == "outgoing" and rel.source_id == node_id:
        return rel.target_id
    if direction == "incoming" and rel.target_id == node_id:
        return rel.source_id
    if direction == "both":
        if rel.source_id == node_id:
            return rel.target_id
        if rel.target_id == node_id:
            return rel.source_id
    return None
