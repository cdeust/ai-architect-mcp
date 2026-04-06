"""Tests for ownership processor — Bird et al. 2011."""

from __future__ import annotations

from unittest.mock import patch

from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel
from ai_codebase_intelligence.core.graph.graph import create_knowledge_graph
from ai_codebase_intelligence.core.ingestion.ownership_processor import (
    process_ownership,
    _compute_file_ownership,
)


def _make_graph_with_files(file_paths: list[str]):
    """Create a graph with File nodes for testing."""
    graph = create_knowledge_graph()
    for fp in file_paths:
        graph.add_node(GraphNode(
            id=f"File:{fp}",
            label=NodeLabel.FILE,
            name=fp.split("/")[-1],
            file_path=fp,
        ))
    return graph


def _mock_blame_data():
    """Mock git blame output: Alice owns 80%, Bob 15%, Charlie 5%."""
    return [
        {"author": "Alice", "email": "alice@test.com", "line_count": 80},
        {"author": "Bob", "email": "bob@test.com", "line_count": 15},
        {"author": "Charlie", "email": "charlie@test.com", "line_count": 5},
    ]


class TestComputeFileOwnership:
    """Test the per-file ownership calculation."""

    def test_ownership_ratio_is_top_author_fraction(self):
        blame = _mock_blame_data()
        result = _compute_file_ownership("f1", "src/main.py", blame, 100, 0.05)
        assert result["ownershipRatio"] == 0.8
        assert result["topContributor"] == "Alice"

    def test_minor_contributors_below_threshold(self):
        blame = _mock_blame_data()
        result = _compute_file_ownership("f1", "src/main.py", blame, 100, 0.05)
        # Charlie has 5/100 = 0.05, which is NOT < 0.05, so only 0 minor
        assert result["minorContributors"] == 0

    def test_minor_contributors_with_higher_threshold(self):
        blame = _mock_blame_data()
        # Threshold at 0.10 → Charlie (5%) is minor
        result = _compute_file_ownership("f1", "src/main.py", blame, 100, 0.10)
        assert result["minorContributors"] == 1

    def test_single_author_full_ownership(self):
        blame = [{"author": "Alice", "email": "alice@test.com", "line_count": 100}]
        result = _compute_file_ownership("f1", "src/main.py", blame, 100, 0.05)
        assert result["ownershipRatio"] == 1.0
        assert result["minorContributors"] == 0
        assert result["authorCount"] == 1


class TestProcessOwnership:
    """Test the full ownership processor pipeline."""

    @patch("ai_codebase_intelligence.core.ingestion.ownership_processor.git_blame_file")
    def test_creates_contributor_nodes(self, mock_blame):
        mock_blame.return_value = _mock_blame_data()
        graph = _make_graph_with_files(["src/main.py"])

        result = process_ownership(graph, "/fake/repo")

        assert result["stats"]["contributorsFound"] == 3
        assert result["stats"]["filesAnalyzed"] == 1

        # Verify Contributor nodes were created
        contributors = [
            n for n in graph.iter_nodes() if n.label.value == "Contributor"
        ]
        assert len(contributors) == 3

    @patch("ai_codebase_intelligence.core.ingestion.ownership_processor.git_blame_file")
    def test_creates_authored_by_edges(self, mock_blame):
        mock_blame.return_value = _mock_blame_data()
        graph = _make_graph_with_files(["src/main.py"])

        process_ownership(graph, "/fake/repo")

        authored_by = [
            r for r in graph.iter_relationships()
            if r.relationship_type.value == "AUTHORED_BY"
        ]
        assert len(authored_by) == 3
        # Top author should have highest confidence
        top_edge = max(authored_by, key=lambda r: r.confidence)
        assert top_edge.confidence == 0.8

    @patch("ai_codebase_intelligence.core.ingestion.ownership_processor.git_blame_file")
    def test_handles_empty_blame(self, mock_blame):
        mock_blame.return_value = []
        graph = _make_graph_with_files(["src/main.py"])

        result = process_ownership(graph, "/fake/repo")

        assert result["stats"]["contributorsFound"] == 0
        assert result["stats"]["filesAnalyzed"] == 1

    @patch("ai_codebase_intelligence.core.ingestion.ownership_processor.git_blame_file")
    def test_deduplicates_contributors_across_files(self, mock_blame):
        mock_blame.return_value = [
            {"author": "Alice", "email": "alice@test.com", "line_count": 100},
        ]
        graph = _make_graph_with_files(["src/a.py", "src/b.py"])

        result = process_ownership(graph, "/fake/repo")

        # Same author across two files = 1 contributor
        assert result["stats"]["contributorsFound"] == 1
        contributors = [
            n for n in graph.iter_nodes() if n.label.value == "Contributor"
        ]
        assert len(contributors) == 1

    @patch("ai_codebase_intelligence.core.ingestion.ownership_processor.git_blame_file")
    def test_low_ownership_detection(self, mock_blame):
        # Many authors with roughly equal contribution
        mock_blame.return_value = [
            {"author": f"Dev{i}", "email": f"dev{i}@test.com", "line_count": 10}
            for i in range(10)
        ]
        graph = _make_graph_with_files(["src/main.py"])

        result = process_ownership(graph, "/fake/repo")

        assert result["stats"]["filesWithLowOwnership"] == 1
        ownership = result["ownerships"][0]
        assert ownership["ownershipRatio"] == 0.1  # 10/100
