"""Resolve phase — builds symbol tables and resolves cross-file edges.

Orchestrates symbol table construction, file grouping, and import
resolution to produce IMPORTS relationships from parsed nodes.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .._models.graph_types import GraphNode, GraphRelationship


class SymbolTable:
    """Lookup table for graph symbols indexed by name.

    Supports global name lookup and retrieval of all registered nodes.
    """

    def __init__(self) -> None:
        self._by_name: dict[str, list[GraphNode]] = defaultdict(list)
        self._all: list[GraphNode] = []

    def register(self, node: GraphNode) -> None:
        """Register a node in the symbol table.

        Args:
            node: GraphNode to register.
        """
        self._by_name[node.name].append(node)
        self._all.append(node)

    def lookup_global(self, name: str) -> list[GraphNode]:
        """Look up nodes by symbol name.

        Args:
            name: Symbol name to search for.

        Returns:
            List of matching nodes (empty if none).
        """
        return list(self._by_name.get(name, []))

    def all_nodes(self) -> list[GraphNode]:
        """Return all registered nodes.

        Returns:
            List of all GraphNode instances in the table.
        """
        return list(self._all)


@dataclass
class ResolutionContext:
    """Context accumulated during symbol resolution.

    Args:
        import_map: file_path -> set of resolved import target paths.
    """

    import_map: dict[str, set[str]] = field(default_factory=dict)


def _build_symbol_table(nodes: list[GraphNode]) -> SymbolTable:
    """Build a symbol table from a list of nodes.

    Only nodes with a non-empty file_path are registered.

    Args:
        nodes: GraphNode instances to index.

    Returns:
        Populated SymbolTable.
    """
    table = SymbolTable()
    for node in nodes:
        if node.file_path:
            table.register(node)
    return table


def _group_nodes_by_file(
    nodes: list[GraphNode],
) -> dict[str, list[GraphNode]]:
    """Group nodes by their file_path.

    Nodes with empty file_path are excluded.

    Args:
        nodes: GraphNode instances to group.

    Returns:
        Dict mapping file_path to list of nodes in that file.
    """
    groups: dict[str, list[GraphNode]] = defaultdict(list)
    for node in nodes:
        if node.file_path:
            groups[node.file_path].append(node)
    return dict(groups)


def resolve_symbols_and_edges(
    nodes: list[GraphNode],
    rels: list[GraphRelationship],
    repo_root: str = "",
) -> tuple[list[GraphRelationship], SymbolTable, ResolutionContext]:
    """Resolve symbols and create cross-file edges.

    Builds a symbol table from *nodes*, groups by file, and resolves
    import nodes into IMPORTS relationships.

    Args:
        nodes: All parsed GraphNode instances.
        rels: Existing relationships (passed through).
        repo_root: Repository root path for resolution context.

    Returns:
        Tuple of (new_relationships, symbol_table, resolution_context).
    """
    table = _build_symbol_table(nodes)
    ctx = ResolutionContext()

    new_rels: list[GraphRelationship] = []

    if not nodes:
        return new_rels, table, ctx

    groups = _group_nodes_by_file(nodes)
    file_paths = list(groups.keys())

    from .._resolution.resolvers.utils import build_suffix_index
    from .._resolution.resolvers.standard import StandardResolver

    suffix_index = build_suffix_index(file_paths)
    resolver = StandardResolver(suffix_index=suffix_index)

    for file_path, file_nodes in groups.items():
        for node in file_nodes:
            if not node.properties.get("is_import"):
                continue

            import_path = node.properties.get("import_path", "")
            if not import_path:
                continue

            resolved = resolver.resolve(str(import_path), file_path)
            if resolved is None:
                continue

            new_rels.append(GraphRelationship(
                source_id=f"{file_path}:File",
                target_id=f"{resolved}:File",
                relationship_type=_imports_type(),
            ))

            if file_path not in ctx.import_map:
                ctx.import_map[file_path] = set()
            ctx.import_map[file_path].add(resolved)

    return new_rels, table, ctx


def _imports_type() -> object:
    """Return the IMPORTS relationship type.

    Returns:
        RelationshipType.IMPORTS enum member.
    """
    from .._models.graph_types import RelationshipType
    return RelationshipType.IMPORTS
