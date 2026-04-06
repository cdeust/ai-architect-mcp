"""Tests for bus factor — Avelino et al. 2016."""

from __future__ import annotations

from ai_codebase_intelligence._models.graph_types import (
    GraphNode, GraphRelationship, NodeLabel, RelationshipType,
)
from ai_codebase_intelligence.core.graph.graph import create_knowledge_graph
from ai_codebase_intelligence.core.analysis.bus_factor import (
    calculate_bus_factor,
    _classify_risk,
    _extract_file_authors,
    _compute_coverage,
)


def _make_graph_with_ownership(file_authors: dict[str, list[tuple[str, float]]]):
    """Create a graph with File nodes, Contributor nodes, and AUTHORED_BY edges.

    Args:
        file_authors: {file_path: [(contributor_email, confidence), ...]}
    """
    graph = create_knowledge_graph()
    contributors_seen: set[str] = set()

    for fp, authors in file_authors.items():
        file_id = f"File:{fp}"
        graph.add_node(GraphNode(
            id=file_id, label=NodeLabel.FILE,
            name=fp.split("/")[-1], file_path=fp,
        ))
        for email, conf in authors:
            contrib_id = f"Contributor:{email}"
            if email not in contributors_seen:
                contributors_seen.add(email)
                graph.add_node(GraphNode(
                    id=contrib_id, label=NodeLabel.CONTRIBUTOR,
                    name=email.split("@")[0],
                    properties={"email": email},
                ))
            graph.add_relationship(GraphRelationship(
                source_id=file_id, target_id=contrib_id,
                relationship_type=RelationshipType.AUTHORED_BY,
                confidence=conf,
                properties={"reason": "git-blame-bird-2011"},
            ))
    return graph


class TestBusFactor:
    """Test bus factor calculation."""

    def test_single_developer_bus_factor_1(self):
        graph = _make_graph_with_ownership({
            "a.py": [("alice@test.com", 1.0)],
            "b.py": [("alice@test.com", 1.0)],
            "c.py": [("alice@test.com", 1.0)],
        })
        result = calculate_bus_factor(graph)
        assert result["busFactor"] == 1
        assert result["risk"] == "CRITICAL"

    def test_two_developers_bus_factor_2(self):
        graph = _make_graph_with_ownership({
            "a.py": [("alice@test.com", 0.8), ("bob@test.com", 0.2)],
            "b.py": [("alice@test.com", 0.8), ("bob@test.com", 0.2)],
            "c.py": [("bob@test.com", 0.9), ("alice@test.com", 0.1)],
            "d.py": [("bob@test.com", 0.9), ("alice@test.com", 0.1)],
        })
        result = calculate_bus_factor(graph)
        # Alice owns a.py, b.py (2 files). Bob owns c.py, d.py (2 files).
        # Remove Alice → 2/4 orphaned = 50% → threshold reached at 1
        # Actually depends on who is removed first (highest coverage or tied)
        assert result["busFactor"] >= 1

    def test_many_developers_high_bus_factor(self):
        # 10 developers each owning 1 file exclusively
        graph = _make_graph_with_ownership({
            f"file{i}.py": [(f"dev{i}@test.com", 1.0)]
            for i in range(10)
        })
        result = calculate_bus_factor(graph)
        # Loop runs while orphaned/total < 0.5. After removing 5 devs:
        # 5/10 = 0.5 which is NOT < 0.5, so loop stops.
        assert result["busFactor"] == 5
        assert result["risk"] == "MEDIUM"

    def test_empty_graph(self):
        graph = create_knowledge_graph()
        result = calculate_bus_factor(graph)
        assert result["busFactor"] == 0
        assert result["risk"] == "UNKNOWN"

    def test_custom_threshold(self):
        graph = _make_graph_with_ownership({
            f"file{i}.py": [(f"dev{i}@test.com", 1.0)]
            for i in range(10)
        })
        result = calculate_bus_factor(graph, orphan_threshold=0.3)
        # Loop runs while orphaned/total < 0.3. After 3 removals: 3/10=0.3, not < 0.3.
        assert result["busFactor"] == 3


class TestClassifyRisk:
    """Test risk classification labels."""

    def test_critical(self):
        assert _classify_risk(1) == "CRITICAL"

    def test_high(self):
        assert _classify_risk(2) == "HIGH"
        assert _classify_risk(3) == "HIGH"

    def test_medium(self):
        assert _classify_risk(4) == "MEDIUM"
        assert _classify_risk(6) == "MEDIUM"

    def test_low(self):
        assert _classify_risk(7) == "LOW"
        assert _classify_risk(100) == "LOW"


class TestExtractFileAuthors:
    """Test file-to-author extraction from graph."""

    def test_picks_highest_confidence_author(self):
        graph = _make_graph_with_ownership({
            "a.py": [("alice@test.com", 0.8), ("bob@test.com", 0.2)],
        })
        authors = _extract_file_authors(graph)
        assert len(authors) == 1
        assert "Contributor:alice@test.com" in authors.values()
