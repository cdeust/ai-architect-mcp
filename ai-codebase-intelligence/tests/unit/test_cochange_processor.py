"""Tests for co-change processor — Gall et al. 1998 + Zimmermann et al. 2005."""

from __future__ import annotations

from unittest.mock import patch

from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel
from ai_codebase_intelligence.core.graph.graph import create_knowledge_graph
from ai_codebase_intelligence.core.ingestion.cochange_processor import (
    process_cochange,
    _mine_cooccurrences,
    _filter_pairs,
)


def _make_graph_with_files(file_paths: list[str]):
    """Create a graph with File nodes."""
    graph = create_knowledge_graph()
    for fp in file_paths:
        graph.add_node(GraphNode(
            id=f"File:{fp}",
            label=NodeLabel.FILE,
            name=fp.split("/")[-1],
            file_path=fp,
        ))
    return graph


def _mock_commits():
    """Mock commit history with known co-change patterns."""
    return [
        {"sha": "c1", "author": "Alice", "email": "a@t.com", "date": "2026-01-01",
         "files": ["src/a.py", "src/b.py"]},
        {"sha": "c2", "author": "Bob", "email": "b@t.com", "date": "2026-01-02",
         "files": ["src/a.py", "src/b.py", "src/c.py"]},
        {"sha": "c3", "author": "Alice", "email": "a@t.com", "date": "2026-01-03",
         "files": ["src/a.py", "src/b.py"]},
        {"sha": "c4", "author": "Bob", "email": "b@t.com", "date": "2026-01-04",
         "files": ["src/c.py"]},
        {"sha": "c5", "author": "Alice", "email": "a@t.com", "date": "2026-01-05",
         "files": ["src/a.py"]},
    ]


class TestMineCooccurrences:
    """Test the commit mining algorithm."""

    def test_counts_file_commits(self):
        commits = _mock_commits()
        indexed = {"src/a.py": "f1", "src/b.py": "f2", "src/c.py": "f3"}
        file_commits, _ = _mine_cooccurrences(commits, indexed)

        assert file_commits["src/a.py"] == 4  # appears in c1, c2, c3, c5
        assert file_commits["src/b.py"] == 3  # appears in c1, c2, c3
        assert file_commits["src/c.py"] == 2  # appears in c2, c4

    def test_counts_pair_support(self):
        commits = _mock_commits()
        indexed = {"src/a.py": "f1", "src/b.py": "f2", "src/c.py": "f3"}
        _, pair_support = _mine_cooccurrences(commits, indexed)

        ab_key = ("src/a.py", "src/b.py")
        assert pair_support[ab_key] == 3  # c1, c2, c3

    def test_ignores_non_indexed_files(self):
        commits = [{"sha": "c1", "author": "A", "email": "", "date": "",
                     "files": ["src/a.py", "unknown.py"]}]
        indexed = {"src/a.py": "f1"}
        file_commits, pair_support = _mine_cooccurrences(commits, indexed)

        assert "unknown.py" not in file_commits
        assert len(pair_support) == 0


class TestFilterPairs:
    """Test support/confidence filtering."""

    def test_filters_by_min_support(self):
        pair_support = {("a", "b"): 5, ("a", "c"): 1}
        file_commits = {"a": 10, "b": 5, "c": 2}

        pairs = _filter_pairs(pair_support, file_commits, min_support=3, min_confidence=0.0)
        assert len(pairs) == 1
        assert pairs[0]["fileA"] == "a"

    def test_filters_by_min_confidence(self):
        pair_support = {("a", "b"): 5}
        file_commits = {"a": 100, "b": 5}

        # conf(a→b) = 5/100 = 0.05, conf(b→a) = 5/5 = 1.0
        # max_conf = 1.0 > 0.5 → passes
        pairs = _filter_pairs(pair_support, file_commits, min_support=1, min_confidence=0.5)
        assert len(pairs) == 1
        assert pairs[0]["confidenceBtoA"] == 1.0

    def test_computes_bidirectional_confidence(self):
        pair_support = {("a", "b"): 3}
        file_commits = {"a": 6, "b": 3}

        pairs = _filter_pairs(pair_support, file_commits, min_support=1, min_confidence=0.0)
        assert pairs[0]["confidenceAtoB"] == 0.5  # 3/6
        assert pairs[0]["confidenceBtoA"] == 1.0   # 3/3


class TestProcessCochange:
    """Test the full co-change processor."""

    @patch("ai_codebase_intelligence.core.ingestion.cochange_processor.git_log_commits")
    def test_creates_cochange_edges(self, mock_log):
        mock_log.return_value = _mock_commits()
        graph = _make_graph_with_files(["src/a.py", "src/b.py", "src/c.py"])

        result = process_cochange(graph, "/fake/repo", config={
            "cochange_min_support": 2,
            "cochange_min_confidence": 0.5,
        })

        assert result["stats"]["commitsAnalyzed"] == 5
        assert result["stats"]["pairsFound"] >= 1

        cochange_edges = [
            r for r in graph.iter_relationships()
            if r.relationship_type.value == "CO_CHANGES_WITH"
        ]
        assert len(cochange_edges) >= 1

    @patch("ai_codebase_intelligence.core.ingestion.cochange_processor.git_log_commits")
    def test_handles_no_commits(self, mock_log):
        mock_log.return_value = []
        graph = _make_graph_with_files(["src/a.py"])

        result = process_cochange(graph, "/fake/repo")

        assert result["stats"]["commitsAnalyzed"] == 0
        assert result["stats"]["pairsFound"] == 0
