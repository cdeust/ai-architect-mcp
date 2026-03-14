"""Tests for propagation analysis — linear chain, diamond, cycle detection."""

from __future__ import annotations

import pytest

from ai_architect_mcp._scoring.propagation import (
    calculate_propagation_impact,
    trace_propagation,
)


class TestTracePropagation:
    """Test BFS propagation tracing."""

    def test_linear_chain(self) -> None:
        graph = {"A": ["B"], "B": ["C"], "C": ["D"]}
        paths = trace_propagation("A", graph)
        assert len(paths) == 3
        assert paths[0].depth == 1
        assert paths[0].propagation_type == "direct"
        assert paths[1].depth == 2
        assert paths[1].propagation_type == "transitive"

    def test_diamond(self) -> None:
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        paths = trace_propagation("A", graph)
        depths = [p.depth for p in paths]
        assert 1 in depths
        assert 2 in depths

    def test_cycle_safe(self) -> None:
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        paths = trace_propagation("A", graph)
        visited_modules = set()
        for p in paths:
            for m in p.target_modules:
                visited_modules.add(m)
        assert "A" not in visited_modules

    def test_no_neighbors(self) -> None:
        graph: dict[str, list[str]] = {"A": []}
        paths = trace_propagation("A", graph)
        assert len(paths) == 0

    def test_source_not_in_graph(self) -> None:
        graph: dict[str, list[str]] = {"B": ["C"]}
        paths = trace_propagation("A", graph)
        assert len(paths) == 0

    def test_max_depth_respected(self) -> None:
        graph = {"A": ["B"], "B": ["C"], "C": ["D"], "D": ["E"]}
        paths = trace_propagation("A", graph, max_depth=2)
        assert all(p.depth <= 2 for p in paths)

    def test_fan_out(self) -> None:
        graph = {"A": ["B", "C", "D"]}
        paths = trace_propagation("A", graph)
        assert len(paths) == 3
        assert all(p.depth == 1 for p in paths)


class TestCalculatePropagationImpact:
    """Test impact calculation from propagation paths."""

    def test_empty_paths(self) -> None:
        assert calculate_propagation_impact([]) == 0.0

    def test_single_direct_path(self) -> None:
        paths = trace_propagation("A", {"A": ["B"]})
        impact = calculate_propagation_impact(paths)
        assert impact > 0.0
        assert impact <= 1.0

    def test_deeper_paths_lower_impact(self) -> None:
        shallow_graph = {"A": ["B"]}
        deep_graph = {"A": ["B"], "B": ["C"], "C": ["D"]}
        shallow_paths = trace_propagation("A", shallow_graph)
        deep_paths = trace_propagation("A", deep_graph)
        shallow_impact = calculate_propagation_impact(shallow_paths)
        deep_impact = calculate_propagation_impact(deep_paths)
        assert shallow_impact > 0.0
        assert deep_impact > 0.0
