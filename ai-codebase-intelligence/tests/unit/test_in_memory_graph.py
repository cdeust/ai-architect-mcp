"""Tests for in-memory graph storage (test double for GraphStoragePort)."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)
from ai_codebase_intelligence._storage.in_memory_graph import InMemoryGraphStorage


@pytest.fixture
def storage() -> InMemoryGraphStorage:
    """Create a fresh in-memory storage instance."""
    return InMemoryGraphStorage()


def _make_node(node_id: str, name: str, label: NodeLabel = NodeLabel.FUNCTION) -> GraphNode:
    """Factory for test nodes."""
    return GraphNode(id=node_id, label=label, name=name, file_path="test.py")


def _make_rel(
    source: str,
    target: str,
    rel_type: RelationshipType = RelationshipType.CALLS,
) -> GraphRelationship:
    """Factory for test relationships."""
    return GraphRelationship(
        source_id=source, target_id=target, relationship_type=rel_type
    )


class TestStoreAndRetrieve:
    """Tests for basic store and retrieve operations."""

    @pytest.mark.asyncio
    async def test_store_nodes(self, storage: InMemoryGraphStorage) -> None:
        nodes = [_make_node("a", "func_a"), _make_node("b", "func_b")]
        count = await storage.store_nodes(nodes)
        assert count == 2
        assert await storage.node_count() == 2

    @pytest.mark.asyncio
    async def test_store_relationships(
        self, storage: InMemoryGraphStorage
    ) -> None:
        await storage.store_nodes([_make_node("a", "a"), _make_node("b", "b")])
        count = await storage.store_relationships([_make_rel("a", "b")])
        assert count == 1
        assert await storage.relationship_count() == 1

    @pytest.mark.asyncio
    async def test_get_node(self, storage: InMemoryGraphStorage) -> None:
        await storage.store_nodes([_make_node("a", "func_a")])
        node = await storage.get_node("a")
        assert node is not None
        assert node.name == "func_a"

    @pytest.mark.asyncio
    async def test_get_missing_node(
        self, storage: InMemoryGraphStorage
    ) -> None:
        assert await storage.get_node("nonexistent") is None


class TestNeighborTraversal:
    """Tests for get_neighbors with direction filtering."""

    @pytest.mark.asyncio
    async def test_outgoing_neighbors(
        self, storage: InMemoryGraphStorage
    ) -> None:
        await storage.store_nodes(
            [_make_node("a", "a"), _make_node("b", "b"), _make_node("c", "c")]
        )
        await storage.store_relationships(
            [_make_rel("a", "b"), _make_rel("a", "c")]
        )
        neighbors = await storage.get_neighbors("a", direction="outgoing")
        names = {n.name for _, n in neighbors}
        assert names == {"b", "c"}

    @pytest.mark.asyncio
    async def test_incoming_neighbors(
        self, storage: InMemoryGraphStorage
    ) -> None:
        await storage.store_nodes(
            [_make_node("a", "a"), _make_node("b", "b")]
        )
        await storage.store_relationships([_make_rel("a", "b")])
        neighbors = await storage.get_neighbors("b", direction="incoming")
        assert len(neighbors) == 1
        assert neighbors[0][1].name == "a"

    @pytest.mark.asyncio
    async def test_filter_by_type(
        self, storage: InMemoryGraphStorage
    ) -> None:
        await storage.store_nodes(
            [_make_node("a", "a"), _make_node("b", "b"), _make_node("c", "c")]
        )
        await storage.store_relationships([
            _make_rel("a", "b", RelationshipType.CALLS),
            _make_rel("a", "c", RelationshipType.IMPORTS),
        ])
        calls_only = await storage.get_neighbors(
            "a", relationship_type="CALLS", direction="outgoing"
        )
        assert len(calls_only) == 1
        assert calls_only[0][1].name == "b"


class TestClearAndCypher:
    """Tests for clear and cypher operations."""

    @pytest.mark.asyncio
    async def test_clear(self, storage: InMemoryGraphStorage) -> None:
        await storage.store_nodes([_make_node("a", "a")])
        await storage.clear()
        assert await storage.node_count() == 0
        assert await storage.relationship_count() == 0

    @pytest.mark.asyncio
    async def test_cypher_not_supported(
        self, storage: InMemoryGraphStorage
    ) -> None:
        with pytest.raises(NotImplementedError):
            await storage.query_cypher("MATCH (n) RETURN n")
