"""Typed graph query functions for wiki generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class GraphStorage(Protocol):
    """Port for graph storage backends."""

    async def query_cypher(
        self, query: str, params: dict[str, object] | None = None,
    ) -> list[dict[str, object]]: ...


@dataclass
class ModuleNode:
    """A node in the module tree."""

    node_id: str
    name: str
    file_path: str
    children: list[ModuleNode] = field(default_factory=list)


@dataclass
class SymbolInfo:
    """Information about a symbol within a module."""

    node_id: str
    name: str
    kind: str
    signature: str = ""
    docstring: str = ""
    start_line: int = 0
    end_line: int = 0
    is_exported: bool = False


@dataclass
class DependencyEdge:
    """A dependency relationship between modules."""

    source_module: str
    target_module: str
    relationship_type: str
    count: int


async def get_module_tree(storage: GraphStorage) -> list[ModuleNode]:
    """Query the graph for the module tree structure.

    Args:
        storage: Graph storage backend.

    Returns:
        List of top-level module nodes with children populated.
    """
    rows = await storage.query_cypher(
        "MATCH (p:Folder)-[:CONTAINS]->(c:File) "
        "RETURN p.id AS parent_id, p.name AS parent_name, "
        "c.id AS child_id, c.name AS child_name, c.filePath AS file_path"
    )
    if not rows:
        return []

    parent_map: dict[str, ModuleNode] = {}
    for row in rows:
        pid = str(row.get("parent_id", ""))
        pname = str(row.get("parent_name", ""))
        cid = str(row.get("child_id", ""))
        cname = str(row.get("child_name", ""))
        fpath = str(row.get("file_path", ""))

        if pid not in parent_map:
            parent_map[pid] = ModuleNode(
                node_id=pid, name=pname, file_path="",
            )
        child = ModuleNode(node_id=cid, name=cname, file_path=fpath)
        parent_map[pid].children.append(child)

    return list(parent_map.values())


async def get_module_symbols(
    storage: GraphStorage, module_id: str,
) -> list[SymbolInfo]:
    """Query the graph for symbols in a module.

    Args:
        storage: Graph storage backend.
        module_id: Identifier of the module to query.

    Returns:
        List of symbols found in the module.
    """
    rows = await storage.query_cypher(
        "MATCH (m)-[:DEFINES]->(s) WHERE m.id = $mid "
        "RETURN s.id AS node_id, s.name AS name, s.kind AS kind, "
        "s.signature AS signature, s.docstring AS docstring, "
        "s.startLine AS start_line, s.endLine AS end_line, "
        "s.isExported AS is_exported",
        {"mid": module_id},
    )
    return [
        SymbolInfo(
            node_id=str(r.get("node_id", "")),
            name=str(r.get("name", "")),
            kind=str(r.get("kind", "")),
            signature=str(r.get("signature", "")),
            docstring=str(r.get("docstring", "")),
            start_line=int(r.get("start_line", 0)),
            end_line=int(r.get("end_line", 0)),
            is_exported=bool(r.get("is_exported", False)),
        )
        for r in rows
    ]


async def get_module_dependencies(
    storage: GraphStorage, module_id: str,
) -> list[DependencyEdge]:
    """Query the graph for a module's dependency edges.

    Args:
        storage: Graph storage backend.
        module_id: Identifier of the module to query.

    Returns:
        List of dependency edges originating from the module.
    """
    rows = await storage.query_cypher(
        "MATCH (a)-[r]->(b) WHERE a.id = $mid AND type(r) <> 'DEFINES' "
        "RETURN a.id AS source_module, b.id AS target_module, "
        "type(r) AS relationship_type, count(*) AS cnt",
        {"mid": module_id},
    )
    return [
        DependencyEdge(
            source_module=str(r.get("source_module", "")),
            target_module=str(r.get("target_module", "")),
            relationship_type=str(r.get("relationship_type", "")),
            count=int(r.get("cnt", 0)),
        )
        for r in rows
    ]
