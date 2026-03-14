"""Propagation analysis — dependency graph traversal for impact assessment.

Traces how changes propagate through module dependency graphs using BFS.
Calculates weighted impact based on propagation depth and fan-out.

Pure functions. Zero LLM calls. Cycle-safe.
"""

from __future__ import annotations

from collections import deque

from ai_architect_mcp._models.scoring import PropagationPath

MAX_DEFAULT_DEPTH = 5


def trace_propagation(
    source_module: str,
    dependency_graph: dict[str, list[str]],
    max_depth: int = MAX_DEFAULT_DEPTH,
) -> list[PropagationPath]:
    """Trace impact propagation paths through a dependency graph using BFS.

    Args:
        source_module: The module where the change originates.
        dependency_graph: Adjacency list of module dependencies.
        max_depth: Maximum propagation depth to trace.

    Returns:
        List of PropagationPath objects representing impact paths.
    """
    paths: list[PropagationPath] = []
    visited: set[str] = {source_module}
    queue: deque[tuple[str, list[str], int]] = deque()

    for neighbor in dependency_graph.get(source_module, []):
        if neighbor not in visited:
            queue.append((neighbor, [neighbor], 1))
            visited.add(neighbor)

    while queue:
        current, path_modules, depth = queue.popleft()

        propagation_type = "direct" if depth == 1 else "transitive"
        paths.append(
            PropagationPath(
                source_module=source_module,
                target_modules=list(path_modules),
                propagation_type=propagation_type,
                depth=depth,
            )
        )

        if depth < max_depth:
            for neighbor in dependency_graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(
                        (neighbor, path_modules + [neighbor], depth + 1)
                    )

    return paths


def calculate_propagation_impact(
    paths: list[PropagationPath],
) -> float:
    """Calculate overall propagation impact from traced paths.

    Impact is weighted by depth (1/depth) and fan-out (number of
    targets at each depth level).

    Args:
        paths: List of PropagationPath objects from trace_propagation.

    Returns:
        Normalized impact score (0.0-1.0).
    """
    if not paths:
        return 0.0

    total_impact = 0.0
    for path in paths:
        depth_weight = 1.0 / path.depth
        fan_out = len(path.target_modules)
        total_impact += depth_weight * fan_out

    max_theoretical = sum(1.0 / (d + 1) for d in range(len(paths)))
    if max_theoretical < 1e-10:
        return 0.0

    normalized = min(1.0, total_impact / max(max_theoretical, 1.0))
    return round(normalized, 6)
