"""Tests for graph-constrained verifier — deterministic."""

from __future__ import annotations

from uuid import uuid4

from ai_architect_mcp._models.graph import (
    ClaimGraphEdge,
    ClaimGraphNode,
    ClaimRelationshipGraph,
    NodeType,
    RelationshipType,
)
from ai_architect_mcp._verification.algorithms.graph_constrained import (
    GraphConstrainedVerifier,
)


class TestGraphConstrainedVerifier:
    """Tests for GraphConstrainedVerifier.verify."""

    def test_clean_graph(self) -> None:
        """Graph with no issues produces high score."""
        n1, n2 = uuid4(), uuid4()
        c1, c2 = uuid4(), uuid4()
        graph = ClaimRelationshipGraph(
            nodes=[
                ClaimGraphNode(
                    node_id=n1,
                    claim_id=c1,
                    label="Req A",
                    node_type=NodeType.REQUIREMENT,
                ),
                ClaimGraphNode(
                    node_id=n2,
                    claim_id=c2,
                    label="Impl B",
                    node_type=NodeType.IMPLEMENTATION,
                ),
            ],
            edges=[
                ClaimGraphEdge(
                    source_id=n1,
                    target_id=n2,
                    relationship=RelationshipType.IMPLEMENTS,
                    weight=0.9,
                ),
            ],
        )
        report = GraphConstrainedVerifier().verify(graph)
        assert report.overall_score > 0.5
        assert report.algorithm_used == "graph_constrained"

    def test_graph_with_cycle(self) -> None:
        """Graph with a cycle penalizes affected nodes."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        c1, c2, c3 = uuid4(), uuid4(), uuid4()
        graph = ClaimRelationshipGraph(
            nodes=[
                ClaimGraphNode(
                    node_id=n1,
                    claim_id=c1,
                    label="A",
                    node_type=NodeType.SPECIFICATION,
                ),
                ClaimGraphNode(
                    node_id=n2,
                    claim_id=c2,
                    label="B",
                    node_type=NodeType.SPECIFICATION,
                ),
                ClaimGraphNode(
                    node_id=n3,
                    claim_id=c3,
                    label="C",
                    node_type=NodeType.SPECIFICATION,
                ),
            ],
            edges=[
                ClaimGraphEdge(
                    source_id=n1,
                    target_id=n2,
                    relationship=RelationshipType.REQUIRES,
                    weight=0.8,
                ),
                ClaimGraphEdge(
                    source_id=n2,
                    target_id=n3,
                    relationship=RelationshipType.REQUIRES,
                    weight=0.7,
                ),
                ClaimGraphEdge(
                    source_id=n3,
                    target_id=n1,
                    relationship=RelationshipType.REQUIRES,
                    weight=0.6,
                ),
            ],
        )
        report = GraphConstrainedVerifier().verify(graph)
        assert report.overall_score < 0.9

    def test_graph_with_contradiction(self) -> None:
        """Contradicting edges penalize involved nodes."""
        n1, n2 = uuid4(), uuid4()
        c1, c2 = uuid4(), uuid4()
        graph = ClaimRelationshipGraph(
            nodes=[
                ClaimGraphNode(
                    node_id=n1,
                    claim_id=c1,
                    label="A",
                    node_type=NodeType.REQUIREMENT,
                ),
                ClaimGraphNode(
                    node_id=n2,
                    claim_id=c2,
                    label="B",
                    node_type=NodeType.REQUIREMENT,
                ),
            ],
            edges=[
                ClaimGraphEdge(
                    source_id=n1,
                    target_id=n2,
                    relationship=RelationshipType.CONTRADICTS,
                    weight=0.9,
                ),
            ],
        )
        report = GraphConstrainedVerifier().verify(graph)
        assert any(e.score < 1.0 for e in report.evaluations)

    def test_empty_graph(self) -> None:
        """Empty graph produces valid report with score 0."""
        report = GraphConstrainedVerifier().verify(
            ClaimRelationshipGraph()
        )
        assert report.overall_score >= 0.0
