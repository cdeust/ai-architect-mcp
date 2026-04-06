"""Tests for graph type models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    KnowledgeGraph,
    NodeLabel,
    RelationshipType,
)


class TestGraphNode:
    """Tests for GraphNode model."""

    def test_create_minimal_node(self) -> None:
        node = GraphNode(
            id="src/main.py:main:Function",
            label=NodeLabel.FUNCTION,
            name="main",
            file_path="src/main.py",
        )
        assert node.id == "src/main.py:main:Function"
        assert node.label == NodeLabel.FUNCTION
        assert node.name == "main"
        assert node.start_line == 0
        assert node.is_exported is False
        assert node.properties == {}

    def test_create_full_node(self) -> None:
        node = GraphNode(
            id="src/app.swift:AppDelegate:Class",
            label=NodeLabel.CLASS,
            name="AppDelegate",
            qualified_name="MyApp.AppDelegate",
            file_path="src/app.swift",
            start_line=10,
            end_line=50,
            language="swift",
            signature="class AppDelegate: NSObject",
            docstring="Main app delegate.",
            is_exported=True,
            properties={"is_final": True},
        )
        assert node.qualified_name == "MyApp.AppDelegate"
        assert node.language == "swift"
        assert node.properties["is_final"] is True

    def test_node_requires_id(self) -> None:
        with pytest.raises(ValidationError):
            GraphNode(label=NodeLabel.CLASS, name="Foo", file_path="f.py")

    def test_all_node_labels(self) -> None:
        assert len(NodeLabel) == 29  # 27 original + CONTRIBUTOR + VARIABLE
        assert NodeLabel.FILE.value == "File"
        assert NodeLabel.PROCESS.value == "Process"
        assert NodeLabel.COMMUNITY.value == "Community"


class TestGraphRelationship:
    """Tests for GraphRelationship model."""

    def test_create_relationship(self) -> None:
        rel = GraphRelationship(
            source_id="a:b:Function",
            target_id="c:d:Class",
            relationship_type=RelationshipType.CALLS,
        )
        assert rel.confidence == 1.0
        assert rel.properties == {}

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            GraphRelationship(
                source_id="a",
                target_id="b",
                relationship_type=RelationshipType.CALLS,
                confidence=1.5,
            )

    def test_all_relationship_types(self) -> None:
        assert len(RelationshipType) == 19  # 14 original + git analytics + type system
        assert RelationshipType.CONTAINS.value == "CONTAINS"
        assert RelationshipType.DEFINES.value == "DEFINES"
        assert RelationshipType.EXPORTS.value == "EXPORTS"


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph model."""

    def test_empty_graph(self) -> None:
        graph = KnowledgeGraph(repo_path="/tmp/repo")
        assert graph.nodes == {}
        assert graph.relationships == []
        assert graph.commit_hash == ""

    def test_graph_with_nodes_and_edges(self) -> None:
        node_a = GraphNode(
            id="a", label=NodeLabel.FUNCTION, name="a", file_path="a.py"
        )
        node_b = GraphNode(
            id="b", label=NodeLabel.FUNCTION, name="b", file_path="b.py"
        )
        rel = GraphRelationship(
            source_id="a",
            target_id="b",
            relationship_type=RelationshipType.CALLS,
        )
        graph = KnowledgeGraph(
            nodes={"a": node_a, "b": node_b},
            relationships=[rel],
            repo_path="/tmp/repo",
            commit_hash="abc1234",
        )
        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
