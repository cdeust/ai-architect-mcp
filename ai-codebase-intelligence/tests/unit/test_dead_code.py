"""Tests for dead code detection — Grove et al. 1997 + Tip et al. 1999."""

from __future__ import annotations

from ai_codebase_intelligence._models.graph_types import (
    GraphNode, GraphRelationship, NodeLabel, RelationshipType,
)
from ai_codebase_intelligence.core.graph.graph import create_knowledge_graph
from ai_codebase_intelligence.core.storage.graph_index import GraphIndex
from ai_codebase_intelligence.core.analysis.dead_code import (
    detect_dead_code,
    _classify_confidence,
    _is_excluded,
)


def _make_index_with_calls(
    nodes: list[GraphNode],
    calls: list[tuple[str, str]],
) -> GraphIndex:
    """Build a GraphIndex with specified nodes and CALLS edges."""
    graph = create_knowledge_graph()
    for n in nodes:
        graph.add_node(n)
    for src, tgt in calls:
        graph.add_relationship(GraphRelationship(
            source_id=src, target_id=tgt,
            relationship_type=RelationshipType.CALLS,
            confidence=1.0,
            properties={"reason": "test"},
        ))
    return GraphIndex(graph)


def _func_node(node_id: str, name: str, exported: bool = False, lang: str = "java") -> GraphNode:
    """Create a Function node."""
    return GraphNode(
        id=node_id, label=NodeLabel.FUNCTION,
        name=name, file_path=f"src/{name}.java",
        start_line=1, end_line=10,
        is_exported=exported, language=lang,
    )


class TestDetectDeadCode:
    """Test reachability-based dead code detection."""

    def test_detects_unreachable_function(self):
        nodes = [
            _func_node("main", "main", exported=True),
            _func_node("helper", "helper"),
            _func_node("orphan", "orphan"),
        ]
        calls = [("main", "helper")]  # orphan is never called
        index = _make_index_with_calls(nodes, calls)

        result = detect_dead_code(index)

        names = [c["name"] for c in result["candidates"]]
        assert "orphan" in names
        assert "main" not in names
        assert "helper" not in names

    def test_reachable_chain_not_dead(self):
        nodes = [
            _func_node("entry", "entry", exported=True),
            _func_node("mid", "mid"),
            _func_node("leaf", "leaf"),
        ]
        calls = [("entry", "mid"), ("mid", "leaf")]
        index = _make_index_with_calls(nodes, calls)

        result = detect_dead_code(index)

        assert len(result["candidates"]) == 0
        assert result["stats"]["reachable"] == 3

    def test_all_reachable_no_dead_code(self):
        nodes = [_func_node("a", "a", exported=True), _func_node("b", "b")]
        calls = [("a", "b")]
        index = _make_index_with_calls(nodes, calls)

        result = detect_dead_code(index)

        assert result["stats"]["reported"] == 0

    def test_multiple_entry_points(self):
        nodes = [
            _func_node("entry1", "entry1", exported=True),
            _func_node("entry2", "entry2", exported=True),
            _func_node("shared", "shared"),
            _func_node("orphan", "orphan"),
        ]
        calls = [("entry1", "shared"), ("entry2", "shared")]
        index = _make_index_with_calls(nodes, calls)

        result = detect_dead_code(index)

        names = [c["name"] for c in result["candidates"]]
        assert "orphan" in names
        assert "shared" not in names

    def test_stats_correct(self):
        nodes = [
            _func_node("e", "e", exported=True),
            _func_node("used", "used"),
            _func_node("dead1", "dead1"),
            _func_node("dead2", "dead2"),
        ]
        calls = [("e", "used")]
        index = _make_index_with_calls(nodes, calls)

        result = detect_dead_code(index)

        assert result["stats"]["totalSymbols"] == 4
        assert result["stats"]["reachable"] == 2
        assert result["stats"]["unreachable"] == 2


class TestClassifyConfidence:
    """Test confidence classification."""

    def test_static_language_high_confidence(self):
        conf, reason = _classify_confidence({
            "name": "calculate", "language": "java", "isExported": False,
        })
        assert conf == 0.9
        assert reason == "static-unreachable"

    def test_dynamic_language_medium_confidence(self):
        conf, reason = _classify_confidence({
            "name": "calculate", "language": "python", "isExported": False,
        })
        assert conf == 0.6
        assert reason == "dynamic-language"

    def test_plugin_pattern_low_confidence(self):
        conf, reason = _classify_confidence({
            "name": "AuthPlugin", "language": "java", "isExported": False,
        })
        assert conf == 0.3
        assert reason == "dynamic-pattern-name"

    def test_exported_medium_confidence(self):
        conf, reason = _classify_confidence({
            "name": "calculate", "language": "go", "isExported": True,
        })
        assert conf == 0.6
        assert reason == "exported-but-unreachable"


class TestIsExcluded:
    """Test exclusion rules."""

    def test_dunder_excluded(self):
        assert _is_excluded({"name": "__init__"}) is True

    def test_private_not_excluded(self):
        assert _is_excluded({"name": "_helper"}) is False

    def test_regular_not_excluded(self):
        assert _is_excluded({"name": "calculate"}) is False
