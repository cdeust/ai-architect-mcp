"""Convert graph nodes to text for embedding.

Pure functions that format GraphNode metadata into text strings
suitable for sentence-transformer encoding.
"""

from __future__ import annotations

from .._models.graph_types import GraphNode


def node_to_text(node: GraphNode) -> str:
    """Convert a single GraphNode to a text representation.

    Format: "{Label} {name} in {file_path}\\n{signature}\\n{docstring}"
    Empty signature/docstring lines are omitted.

    Args:
        node: The graph node to convert.

    Returns:
        Text string for embedding.
    """
    label_name = node.label.value
    parts = [f"{label_name} {node.name} in {node.file_path}"]

    if node.signature:
        parts.append(node.signature)
    if node.docstring:
        parts.append(node.docstring)

    return "\n".join(parts)


def nodes_to_texts(nodes: list[GraphNode]) -> list[tuple[str, str]]:
    """Batch-convert nodes to (id, text) pairs.

    Args:
        nodes: List of GraphNode instances.

    Returns:
        List of (node_id, text) tuples in input order.
    """
    return [(node.id, node_to_text(node)) for node in nodes]
