"""Backend: bus factor analysis — Avelino et al. 2016."""

from __future__ import annotations

from typing import Any

from ...core.analysis.bus_factor import calculate_bus_factor
from ...core.storage.repo_store import get_store


async def bus_factor_tool(
    backend: Any,
    repo: dict[str, Any],
    params: dict[str, Any],
) -> Any:
    """Calculate bus factor for the repository.

    Args:
        backend: LocalBackend instance.
        repo: Resolved repo dict.
        params: Tool params with optional threshold.

    Returns:
        Bus factor result with removal sequence.
    """
    await backend.ensure_initialized(repo["id"])

    # Bus factor needs the full graph with AUTHORED_BY edges.
    # Load from the indexing session if available, otherwise rebuild.
    from ...core.storage.repo_store import get_index
    index = get_index(repo["id"])

    # Build a lightweight graph from the index for bus_factor calculation
    from ...core.graph.graph import create_knowledge_graph
    graph = create_knowledge_graph()

    for node_id, node in index._nodes.items():
        graph.add_node(node)
    for node_id, edges in index._out.items():
        for target_id, rel in edges:
            graph.add_relationship(rel)

    threshold = params.get("threshold", 0.5)
    return calculate_bus_factor(graph, orphan_threshold=threshold)
