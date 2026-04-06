"""Symbol table for name-to-node resolution.

Maintains file-scoped and global indexes for fast symbol lookup
during the resolution phase of the ingestion pipeline.
"""

from __future__ import annotations

from collections import defaultdict

from .._models.graph_types import GraphNode


class SymbolTable:
    """Bidirectional symbol index: name -> nodes, (file, name) -> nodes.

    Supports register, lookup by file, lookup globally, and clear.
    Duplicate registrations (same node ID) are idempotent.

    Args: None — constructed empty, populated via register().
    """

    def __init__(self) -> None:
        self._by_file: dict[str, dict[str, list[GraphNode]]] = defaultdict(
            lambda: defaultdict(list),
        )
        self._by_name: dict[str, list[GraphNode]] = defaultdict(list)
        self._seen_ids: set[str] = set()

    def register(self, node: GraphNode) -> None:
        """Register a node in both file-scoped and global indexes.

        Duplicate node IDs are silently ignored (idempotent).

        Args:
            node: The graph node to register.
        """
        if node.id in self._seen_ids:
            return
        self._seen_ids.add(node.id)
        self._by_file[node.file_path][node.name].append(node)
        self._by_name[node.name].append(node)

    def lookup_in_file(self, file_path: str, name: str) -> list[GraphNode]:
        """Find nodes by name within a specific file.

        Args:
            file_path: Source file path.
            name: Symbol name to look up.

        Returns:
            List of matching GraphNode instances (empty if none).
        """
        return list(self._by_file.get(file_path, {}).get(name, []))

    def lookup_global(self, name: str) -> list[GraphNode]:
        """Find all nodes matching a name across all files.

        Args:
            name: Symbol name to look up.

        Returns:
            List of matching GraphNode instances (empty if none).
        """
        return list(self._by_name.get(name, []))

    def all_nodes(self) -> list[GraphNode]:
        """Return all registered nodes.

        Returns:
            Flat list of every registered GraphNode.
        """
        result: list[GraphNode] = []
        for nodes_by_name in self._by_name.values():
            result.extend(nodes_by_name)
        return result

    def clear(self) -> None:
        """Remove all entries from both indexes."""
        self._by_file.clear()
        self._by_name.clear()
        self._seen_ids.clear()
