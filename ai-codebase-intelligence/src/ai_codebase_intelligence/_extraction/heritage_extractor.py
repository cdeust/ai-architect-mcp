"""Heritage (inheritance) extraction from tree-sitter ASTs.

Walks the AST looking for class definitions and extracts their
parent classes / interfaces into HeritageInfo records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.heritage_processor import HeritageInfo

if TYPE_CHECKING:
    from ai_codebase_intelligence._models.graph_types import GraphNode


def extract_heritage_from_tree(
    root_node: object,
    file_path: str,
    language: SupportedLanguage,
    class_nodes: list[GraphNode],
) -> list[HeritageInfo]:
    """Extract inheritance relationships from a tree-sitter AST.

    Args:
        root_node: The root tree-sitter node.
        file_path: Path to the source file.
        language: The source language.
        class_nodes: Known class GraphNodes to match against.

    Returns:
        A list of HeritageInfo records.
    """
    results: list[HeritageInfo] = []
    node_map = {n.name: n for n in class_nodes}
    _walk_heritage(root_node, file_path, language, node_map, results)
    return results


def _walk_heritage(
    node: object,
    file_path: str,
    language: SupportedLanguage,
    node_map: dict[str, GraphNode],
    out: list[HeritageInfo],
) -> None:
    """Recursively walk AST collecting class heritage.

    Args:
        node: Current tree-sitter node.
        file_path: Source file path.
        language: Source language.
        node_map: Class name to GraphNode mapping.
        out: Accumulator for heritage records.
    """
    node_type = node.type  # type: ignore[union-attr]

    if node_type == "class_definition":
        _extract_python_heritage(node, file_path, node_map, out)
    elif node_type == "class_declaration":
        _extract_ts_heritage(node, file_path, language, node_map, out)

    for child in node.named_children:  # type: ignore[union-attr]
        _walk_heritage(child, file_path, language, node_map, out)


def _extract_python_heritage(
    node: object,
    file_path: str,
    node_map: dict[str, GraphNode],
    out: list[HeritageInfo],
) -> None:
    """Extract heritage from a Python class_definition node.

    Args:
        node: A tree-sitter class_definition node.
        file_path: Source file path.
        node_map: Class name to GraphNode mapping.
        out: Accumulator for heritage records.
    """
    name_node = node.child_by_field_name("name")  # type: ignore[union-attr]
    if name_node is None:
        return
    class_name = name_node.text.decode("utf-8")

    graph_node = node_map.get(class_name)
    if graph_node is None:
        return

    superclasses = node.child_by_field_name("superclasses")  # type: ignore[union-attr]
    if superclasses is None:
        return

    for child in superclasses.named_children:
        parent_name = child.text.decode("utf-8")
        if parent_name == "object":
            continue
        out.append(
            HeritageInfo(
                child_id=graph_node.id,
                parent_name=parent_name,
                heritage_type="extends",
                file_path=file_path,
            )
        )


def _extract_ts_heritage(
    node: object,
    file_path: str,
    language: SupportedLanguage,
    node_map: dict[str, GraphNode],
    out: list[HeritageInfo],
) -> None:
    """Extract heritage from a TS/Java class_declaration node.

    Args:
        node: A tree-sitter class_declaration node.
        file_path: Source file path.
        language: Source language.
        node_map: Class name to GraphNode mapping.
        out: Accumulator for heritage records.
    """
    name_node = node.child_by_field_name("name")  # type: ignore[union-attr]
    if name_node is None:
        return
    class_name = name_node.text.decode("utf-8")

    graph_node = node_map.get(class_name)
    if graph_node is None:
        return

    for child in node.named_children:  # type: ignore[union-attr]
        child_type = child.type
        if child_type == "class_heritage":
            _extract_heritage_clause(child, graph_node.id, file_path, out)
        elif child_type == "extends_type_clause":
            _extract_extends_clause(child, graph_node.id, file_path, out)
        elif child_type == "superclass":
            parent_text = child.text.decode("utf-8")
            out.append(
                HeritageInfo(
                    child_id=graph_node.id,
                    parent_name=parent_text,
                    heritage_type="extends",
                    file_path=file_path,
                )
            )


def _extract_heritage_clause(
    clause_node: object,
    child_id: str,
    file_path: str,
    out: list[HeritageInfo],
) -> None:
    """Extract from a TS class_heritage node.

    Args:
        clause_node: The class_heritage tree-sitter node.
        child_id: The graph node ID of the child class.
        file_path: Source file path.
        out: Accumulator for heritage records.
    """
    for child in clause_node.named_children:  # type: ignore[union-attr]
        child_type = child.type
        if child_type == "extends_clause":
            heritage_type = "extends"
        elif child_type == "implements_clause":
            heritage_type = "implements"
        else:
            continue

        for value_node in child.named_children:
            parent_text = value_node.text.decode("utf-8")
            out.append(
                HeritageInfo(
                    child_id=child_id,
                    parent_name=parent_text,
                    heritage_type=heritage_type,
                    file_path=file_path,
                )
            )


def _extract_extends_clause(
    clause_node: object,
    child_id: str,
    file_path: str,
    out: list[HeritageInfo],
) -> None:
    """Extract from an extends_type_clause node.

    Args:
        clause_node: The extends_type_clause tree-sitter node.
        child_id: The graph node ID of the child class.
        file_path: Source file path.
        out: Accumulator for heritage records.
    """
    for child in clause_node.named_children:  # type: ignore[union-attr]
        parent_text = child.text.decode("utf-8")
        out.append(
            HeritageInfo(
                child_id=child_id,
                parent_name=parent_text,
                heritage_type="extends",
                file_path=file_path,
            )
        )
