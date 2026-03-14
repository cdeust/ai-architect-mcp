"""Tests for graph models — construction, edge validation, orphan rejection."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ai_architect_mcp._models.graph import (
    ClaimGraphEdge,
    ClaimGraphNode,
    ClaimRelationshipGraph,
    NodeType,
    RelationshipType,
    ThoughtEdge,
    ThoughtGraph,
    ThoughtNode,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestClaimRelationshipGraph:
    """Test ClaimRelationshipGraph construction and validation."""

    def test_empty_graph(self) -> None:
        graph = ClaimRelationshipGraph()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_valid_graph(self) -> None:
        node_a_id = uuid4()
        node_b_id = uuid4()
        claim_id = uuid4()
        graph = ClaimRelationshipGraph(
            nodes=[
                ClaimGraphNode(node_id=node_a_id, claim_id=claim_id, label="Req A", node_type=NodeType.REQUIREMENT),
                ClaimGraphNode(node_id=node_b_id, claim_id=claim_id, label="Impl B", node_type=NodeType.IMPLEMENTATION),
            ],
            edges=[
                ClaimGraphEdge(source_id=node_a_id, target_id=node_b_id, relationship=RelationshipType.IMPLEMENTS, weight=0.9),
            ],
        )
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_orphan_edge_rejected(self) -> None:
        node_id = uuid4()
        claim_id = uuid4()
        orphan_id = uuid4()
        with pytest.raises(ValueError, match="does not reference any node"):
            ClaimRelationshipGraph(
                nodes=[
                    ClaimGraphNode(node_id=node_id, claim_id=claim_id, label="A", node_type=NodeType.REQUIREMENT),
                ],
                edges=[
                    ClaimGraphEdge(source_id=node_id, target_id=orphan_id, relationship=RelationshipType.IMPLIES, weight=0.5),
                ],
            )

    def test_all_node_types(self) -> None:
        assert len(NodeType) == 5

    def test_all_relationship_types(self) -> None:
        assert len(RelationshipType) == 6


class TestThoughtGraph:
    """Test ThoughtGraph construction and validation."""

    def test_valid_thought_graph(self) -> None:
        root_id = uuid4()
        child_id = uuid4()
        graph = ThoughtGraph(
            nodes=[
                ThoughtNode(node_id=root_id, content="Root thought", confidence=0.9, depth=0),
                ThoughtNode(node_id=child_id, content="Child thought", confidence=0.7, depth=1),
            ],
            edges=[
                ThoughtEdge(source_id=root_id, target_id=child_id, relationship="expansion", weight=0.8),
            ],
            root_id=root_id,
        )
        assert len(graph.nodes) == 2
        assert graph.root_id == root_id

    def test_invalid_root_rejected(self) -> None:
        node_id = uuid4()
        invalid_root = uuid4()
        with pytest.raises(ValueError, match="root_id"):
            ThoughtGraph(
                nodes=[ThoughtNode(node_id=node_id, content="test", confidence=0.5, depth=0)],
                edges=[],
                root_id=invalid_root,
            )

    def test_fixture_valid_dag(self) -> None:
        fixture_path = FIXTURES_DIR / "graph_valid_dag.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            graph = ClaimRelationshipGraph.model_validate(data)
            assert len(graph.nodes) > 0
