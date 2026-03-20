"""Tests for community detection via Leiden algorithm."""

from __future__ import annotations

from ai_codebase_intelligence._analysis.community_processor import (
    CommunityResult,
    detect_communities,
)
from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)


def _fn(node_id: str, name: str = "") -> GraphNode:
    """Create a Function node for testing."""
    return GraphNode(
        id=node_id,
        label=NodeLabel.FUNCTION,
        name=name or node_id,
        file_path=f"{node_id}.py",
    )


def _call(src: str, tgt: str) -> GraphRelationship:
    """Create a CALLS relationship for testing."""
    return GraphRelationship(
        source_id=src,
        target_id=tgt,
        relationship_type=RelationshipType.CALLS,
    )


class TestCommunityDetection:
    """Tests for detect_communities."""

    def test_triangle_forms_single_community(self) -> None:
        """Three nodes all connected should form 1 community."""
        nodes = [_fn("a"), _fn("b"), _fn("c")]
        rels = [_call("a", "b"), _call("b", "c"), _call("c", "a")]

        result = detect_communities(nodes, rels)

        assert isinstance(result, CommunityResult)
        assert len(result.communities) >= 1
        all_members = []
        for members in result.communities.values():
            all_members.extend(members)
        assert set(all_members) == {"a", "b", "c"}
        assert len(result.node_community) == 3

    def test_two_disconnected_cliques(self) -> None:
        """Two separate triangles should form 2 communities."""
        nodes = [
            _fn("a1"), _fn("a2"), _fn("a3"),
            _fn("b1"), _fn("b2"), _fn("b3"),
        ]
        rels = [
            _call("a1", "a2"), _call("a2", "a3"), _call("a3", "a1"),
            _call("b1", "b2"), _call("b2", "b3"), _call("b3", "b1"),
        ]

        result = detect_communities(nodes, rels)

        assert len(result.communities) == 2
        community_sets = [
            set(members) for members in result.communities.values()
        ]
        assert {"a1", "a2", "a3"} in community_sets
        assert {"b1", "b2", "b3"} in community_sets

    def test_empty_graph(self) -> None:
        """Empty graph should return single community with no members."""
        result = detect_communities([], [])

        assert len(result.communities) == 1
        comm_id = list(result.communities.keys())[0]
        assert result.communities[comm_id] == []
        assert result.modularity == 0.0

    def test_single_node(self) -> None:
        """Single node should get single-community fallback."""
        nodes = [_fn("solo")]
        result = detect_communities(nodes, [])

        assert len(result.communities) == 1
        assert "solo" in list(result.communities.values())[0]

    def test_non_callable_nodes_filtered(self) -> None:
        """File/Folder nodes should be filtered out."""
        nodes = [
            GraphNode(
                id="file1", label=NodeLabel.FILE,
                name="file1.py", file_path="file1.py",
            ),
            _fn("func1"),
        ]
        rels = []

        result = detect_communities(nodes, rels)

        all_members = []
        for members in result.communities.values():
            all_members.extend(members)
        assert "file1" not in all_members

    def test_only_calls_relationships_used(self) -> None:
        """Non-CALLS relationships should be ignored for graph building."""
        nodes = [_fn("a"), _fn("b"), _fn("c")]
        rels = [
            _call("a", "b"),
            GraphRelationship(
                source_id="b", target_id="c",
                relationship_type=RelationshipType.IMPORTS,
            ),
        ]

        result = detect_communities(nodes, rels)

        assert isinstance(result, CommunityResult)
        assert len(result.node_community) == 3
