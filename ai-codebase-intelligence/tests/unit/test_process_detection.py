"""Tests for process detection via entry point scoring + BFS."""

from __future__ import annotations

from ai_codebase_intelligence._analysis.process_processor import (
    MAX_BFS_DEPTH,
    ProcessTrace,
    detect_processes,
)
from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)


def _fn(node_id: str, name: str = "", exported: bool = False) -> GraphNode:
    """Create a Function node for testing."""
    return GraphNode(
        id=node_id,
        label=NodeLabel.FUNCTION,
        name=name or node_id,
        file_path=f"{node_id}.py",
        is_exported=exported,
    )


def _call(src: str, tgt: str) -> GraphRelationship:
    """Create a CALLS relationship for testing."""
    return GraphRelationship(
        source_id=src,
        target_id=tgt,
        relationship_type=RelationshipType.CALLS,
    )


class TestProcessDetection:
    """Tests for detect_processes."""

    def test_linear_chain_from_main(self) -> None:
        """main -> process -> save should detect 1 process from main."""
        nodes = [
            _fn("main", "main", exported=True),
            _fn("process", "process"),
            _fn("save", "save"),
        ]
        rels = [_call("main", "process"), _call("process", "save")]
        call_counts = {
            "main": (0, 1),
            "process": (1, 1),
            "save": (1, 0),
        }

        processes = detect_processes(nodes, rels, call_counts)

        assert len(processes) >= 1
        main_proc = next(
            (p for p in processes if p.entry_point_name == "main"), None
        )
        assert main_proc is not None
        assert "main" in main_proc.members
        assert "process" in main_proc.members
        assert "save" in main_proc.members

    def test_deduplication_removes_subset(self) -> None:
        """If process A contains all nodes of B, B is removed."""
        nodes = [
            _fn("handle", "handle", exported=True),
            _fn("validate", "validate"),
            _fn("save", "save"),
            _fn("process", "process", exported=True),
        ]
        rels = [
            _call("handle", "validate"),
            _call("validate", "save"),
            _call("process", "save"),
        ]
        call_counts = {
            "handle": (0, 1),
            "validate": (1, 1),
            "save": (2, 0),
            "process": (0, 1),
        }

        processes = detect_processes(nodes, rels, call_counts)

        member_sets = [set(p.members) for p in processes]
        for i, s1 in enumerate(member_sets):
            for j, s2 in enumerate(member_sets):
                if i != j:
                    assert not s1.issubset(s2), (
                        f"Process {i} is subset of {j} after dedup"
                    )

    def test_bfs_depth_limit(self) -> None:
        """Chain longer than MAX_BFS_DEPTH should be truncated."""
        chain_len = MAX_BFS_DEPTH + 5
        nodes = [
            _fn(f"n{i}", f"n{i}", exported=(i == 0))
            for i in range(chain_len)
        ]
        # Name n0 as 'main' to ensure it scores as entry point
        nodes[0] = _fn("n0", "main", exported=True)

        rels = [_call(f"n{i}", f"n{i+1}") for i in range(chain_len - 1)]
        call_counts = {"n0": (0, 1)}
        for i in range(1, chain_len - 1):
            call_counts[f"n{i}"] = (1, 1)
        call_counts[f"n{chain_len - 1}"] = (1, 0)

        processes = detect_processes(nodes, rels, call_counts)

        if processes:
            main_proc = processes[0]
            max_depth = max(main_proc.depth_map.values())
            assert max_depth <= MAX_BFS_DEPTH

    def test_empty_graph(self) -> None:
        """Empty graph should return no processes."""
        processes = detect_processes([], [], {})
        assert processes == []

    def test_processes_sorted_by_score(self) -> None:
        """Returned processes should be sorted by score descending."""
        nodes = [
            _fn("main", "main", exported=True),
            _fn("handler", "handler", exported=True),
            _fn("a", "a"),
            _fn("b", "b"),
        ]
        rels = [
            _call("main", "a"),
            _call("handler", "b"),
        ]
        call_counts = {
            "main": (0, 1),
            "handler": (0, 1),
            "a": (1, 0),
            "b": (1, 0),
        }

        processes = detect_processes(nodes, rels, call_counts)

        if len(processes) >= 2:
            for i in range(len(processes) - 1):
                assert processes[i].score >= processes[i + 1].score

    def test_non_function_nodes_skipped(self) -> None:
        """Class and Variable nodes should not be entry points."""
        nodes = [
            GraphNode(
                id="cls1", label=NodeLabel.CLASS,
                name="MyClass", file_path="cls.py",
            ),
            GraphNode(
                id="var1", label=NodeLabel.VARIABLE,
                name="config", file_path="config.py",
            ),
        ]
        rels = []
        call_counts = {}

        processes = detect_processes(nodes, rels, call_counts)
        assert processes == []
