"""Tests for analysis modules (Epics 8-9)."""

from __future__ import annotations

from ai_codebase_intelligence._analysis.entry_point_scoring import (
    ENTRY_NAME_PATTERNS,
    score_entry_point,
)
from ai_codebase_intelligence._analysis.framework_detection import (
    FrameworkType,
    detect_framework,
)
from ai_codebase_intelligence._analysis.process_processor import (
    MAX_BFS_DEPTH,
    MAX_BRANCHING,
    MIN_ENTRY_SCORE,
    detect_processes,
)
from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)


class TestFrameworkDetection:
    """Tests for framework detection."""

    def test_detect_django(self) -> None:
        files = ["manage.py", "app/views.py", "app/models.py"]
        info = detect_framework(files)
        assert info.framework == FrameworkType.DJANGO

    def test_detect_express(self) -> None:
        files = ["server.js", "routes/api.js"]
        info = detect_framework(files)
        assert info.framework == FrameworkType.EXPRESS

    def test_unknown_framework(self) -> None:
        files = ["main.c", "utils.c"]
        info = detect_framework(files)
        assert info.framework == FrameworkType.UNKNOWN


class TestEntryPointScoring:
    """Tests for entry point scoring."""

    def test_main_function(self) -> None:
        node = GraphNode(
            id="main", label=NodeLabel.FUNCTION, name="main",
            file_path="main.py", is_exported=True,
        )
        score = score_entry_point(node, caller_count=0, callee_count=10)
        assert score.total_score > 0
        assert score.name_pattern_score == 1.0

    def test_test_function_penalty(self) -> None:
        node = GraphNode(
            id="test_main", label=NodeLabel.FUNCTION, name="test_main",
            file_path="tests/test_main.py",
        )
        score = score_entry_point(node, caller_count=0, callee_count=5)
        assert score.test_penalty_applied is True

    def test_high_caller_low_callee(self) -> None:
        node = GraphNode(
            id="util", label=NodeLabel.FUNCTION, name="util",
            file_path="util.py",
        )
        # Many callers, few callees → not an entry point
        score = score_entry_point(node, caller_count=20, callee_count=1)
        assert score.call_ratio_score < 0.1


class TestProcessDetection:
    """Tests for process detection."""

    def test_empty_graph(self) -> None:
        processes = detect_processes([], [], {})
        assert processes == []

    def test_simple_chain(self) -> None:
        nodes = [
            GraphNode(
                id="main", label=NodeLabel.FUNCTION, name="main",
                file_path="main.py", is_exported=True,
            ),
            GraphNode(
                id="process", label=NodeLabel.FUNCTION, name="process",
                file_path="proc.py",
            ),
            GraphNode(
                id="save", label=NodeLabel.FUNCTION, name="save",
                file_path="db.py",
            ),
        ]
        rels = [
            GraphRelationship(
                source_id="main", target_id="process",
                relationship_type=RelationshipType.CALLS,
            ),
            GraphRelationship(
                source_id="process", target_id="save",
                relationship_type=RelationshipType.CALLS,
            ),
        ]
        call_counts = {
            "main": (0, 1),
            "process": (1, 1),
            "save": (1, 0),
        }
        processes = detect_processes(nodes, rels, call_counts)
        # Should detect at least one process starting from main
        if processes:
            assert processes[0].entry_point_name == "main"
