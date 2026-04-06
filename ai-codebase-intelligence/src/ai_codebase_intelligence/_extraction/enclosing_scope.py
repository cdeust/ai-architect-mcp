"""Enclosing scope resolution for call sites.

Given a tree-sitter AST node representing a call, determines which
function/method node (from a list of GraphNode candidates) encloses it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_codebase_intelligence._models.graph_types import GraphNode


def find_enclosing_function(
    call_node: object,
    function_nodes: list[GraphNode],
) -> str | None:
    """Find the GraphNode ID of the function enclosing a call site.

    Uses line-range containment: a call at line L is enclosed by a
    function spanning [start_line, end_line] if start_line <= L <= end_line.
    When multiple functions contain the call, the narrowest span wins
    (innermost function in nested definitions).

    Args:
        call_node: A tree-sitter node with a .start_point attribute
            providing (row, col) where row is 0-based.
        function_nodes: Candidate enclosing function GraphNodes with
            1-based start_line and end_line.

    Returns:
        The ID of the enclosing function, or None if the call is at
        module level (no enclosing function).
    """
    call_line = call_node.start_point[0] + 1  # type: ignore[union-attr]

    best_id: str | None = None
    best_span = float("inf")

    for node in function_nodes:
        if node.start_line <= call_line <= node.end_line:
            span = node.end_line - node.start_line
            if span < best_span:
                best_span = span
                best_id = node.id

    return best_id
