"""Heritage processor."""
from __future__ import annotations

from typing import Any, Callable

import tree_sitter

from ..._models.graph_types import GraphRelationship, RelationshipType
from ...lib.utils import generate_id
from ..tree_sitter.parser_loader import load_language
from .language_queries import LANGUAGE_QUERIES

_query_cache: dict[str, object] = {}
from .utils import get_language_from_filename
from ..graph.graph import KnowledgeGraph
from .symbol_table import SymbolTable
from .ast_cache import ASTCache


def process_heritage(
    graph: KnowledgeGraph,
    files: list[dict[str, str]],
    ast_cache: ASTCache,
    symbol_table: SymbolTable,
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    for i, file in enumerate(files):
        if on_progress is not None:
            on_progress(i + 1, len(files))

        language = get_language_from_filename(file["path"])
        if language is None:
            continue
        query_str = LANGUAGE_QUERIES.get(language)
        if not query_str:
            continue

        try:
            parser = load_language(language, file["path"])
        except Exception:
            continue

        tree = ast_cache.get(file["path"])
        if tree is None:
            try:
                tree = parser.parse(file["content"].encode("utf-8"))
            except Exception:
                continue
            ast_cache.set(file["path"], tree)

        try:
            cache_key = f"heritage:{language}"
            if cache_key not in _query_cache:
                _query_cache[cache_key] = parser.language.query(query_str)
            query = _query_cache[cache_key]
            matches = query.matches(tree.root_node)
        except Exception:
            continue

        for _pattern_idx, capture_dict in matches:
            cm: dict[str, Any] = {}
            for cname, nodes_list in capture_dict.items():
                if nodes_list:
                    cm[cname] = nodes_list[0]

            # EXTENDS
            if "heritage.class" in cm and "heritage.extends" in cm:
                class_name = cm["heritage.class"].text.decode("utf-8", errors="replace") if cm["heritage.class"].text else ""
                parent_name = cm["heritage.extends"].text.decode("utf-8", errors="replace") if cm["heritage.extends"].text else ""

                child_id = (
                    symbol_table.lookup_exact(file["path"], class_name)
                    or (symbol_table.lookup_fuzzy(class_name) or [{}])[0].get("nodeId")
                    or generate_id("Class", f"{file['path']}:{class_name}")
                )
                parent_id = (
                    (symbol_table.lookup_fuzzy(parent_name) or [{}])[0].get("nodeId")
                    or generate_id("Class", parent_name)
                )

                if child_id and parent_id and child_id != parent_id:
                    graph.add_relationship(GraphRelationship(
                        source_id=child_id, target_id=parent_id,
                        relationship_type=RelationshipType.EXTENDS,
                        confidence=1.0,
                    ))

            # IMPLEMENTS
            if "heritage.class" in cm and "heritage.implements" in cm:
                class_name = cm["heritage.class"].text.decode("utf-8", errors="replace") if cm["heritage.class"].text else ""
                iface_name = cm["heritage.implements"].text.decode("utf-8", errors="replace") if cm["heritage.implements"].text else ""

                class_id = (
                    symbol_table.lookup_exact(file["path"], class_name)
                    or (symbol_table.lookup_fuzzy(class_name) or [{}])[0].get("nodeId")
                    or generate_id("Class", f"{file['path']}:{class_name}")
                )
                iface_id = (
                    (symbol_table.lookup_fuzzy(iface_name) or [{}])[0].get("nodeId")
                    or generate_id("Interface", iface_name)
                )

                if class_id and iface_id:
                    graph.add_relationship(GraphRelationship(
                        source_id=class_id, target_id=iface_id,
                        relationship_type=RelationshipType.IMPLEMENTS,
                        confidence=1.0,
                    ))

            # Rust trait impl
            if "heritage.trait" in cm and "heritage.class" in cm:
                struct_name = cm["heritage.class"].text.decode("utf-8", errors="replace") if cm["heritage.class"].text else ""
                trait_name = cm["heritage.trait"].text.decode("utf-8", errors="replace") if cm["heritage.trait"].text else ""

                struct_id = (
                    symbol_table.lookup_exact(file["path"], struct_name)
                    or (symbol_table.lookup_fuzzy(struct_name) or [{}])[0].get("nodeId")
                    or generate_id("Struct", f"{file['path']}:{struct_name}")
                )
                trait_id = (
                    (symbol_table.lookup_fuzzy(trait_name) or [{}])[0].get("nodeId")
                    or generate_id("Trait", trait_name)
                )

                if struct_id and trait_id:
                    graph.add_relationship(GraphRelationship(
                        source_id=struct_id, target_id=trait_id,
                        relationship_type=RelationshipType.IMPLEMENTS,
                        confidence=1.0,
                        properties={"reason": "trait-impl"},
                    ))


def process_heritage_from_extracted(
    graph: KnowledgeGraph,
    extracted_heritage: list[dict[str, str]],
    symbol_table: SymbolTable,
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    total = len(extracted_heritage)
    for i, h in enumerate(extracted_heritage):
        if i % 500 == 0 and on_progress is not None:
            on_progress(i, total)

        if h["kind"] == "extends":
            child_id = (
                symbol_table.lookup_exact(h["filePath"], h["className"])
                or (symbol_table.lookup_fuzzy(h["className"]) or [{}])[0].get("nodeId")
                or generate_id("Class", f"{h['filePath']}:{h['className']}")
            )
            parent_id = (
                (symbol_table.lookup_fuzzy(h["parentName"]) or [{}])[0].get("nodeId")
                or generate_id("Class", h["parentName"])
            )
            if child_id and parent_id and child_id != parent_id:
                graph.add_relationship(GraphRelationship(
                    source_id=child_id, target_id=parent_id,
                    relationship_type=RelationshipType.EXTENDS,
                    confidence=1.0,
                ))

        elif h["kind"] == "implements":
            class_id = (
                symbol_table.lookup_exact(h["filePath"], h["className"])
                or (symbol_table.lookup_fuzzy(h["className"]) or [{}])[0].get("nodeId")
                or generate_id("Class", f"{h['filePath']}:{h['className']}")
            )
            iface_id = (
                (symbol_table.lookup_fuzzy(h["parentName"]) or [{}])[0].get("nodeId")
                or generate_id("Interface", h["parentName"])
            )
            if class_id and iface_id:
                graph.add_relationship(GraphRelationship(
                    source_id=class_id, target_id=iface_id,
                    relationship_type=RelationshipType.IMPLEMENTS,
                    confidence=1.0,
                ))

        elif h["kind"] == "trait-impl":
            struct_id = (
                symbol_table.lookup_exact(h["filePath"], h["className"])
                or (symbol_table.lookup_fuzzy(h["className"]) or [{}])[0].get("nodeId")
                or generate_id("Struct", f"{h['filePath']}:{h['className']}")
            )
            trait_id = (
                (symbol_table.lookup_fuzzy(h["parentName"]) or [{}])[0].get("nodeId")
                or generate_id("Trait", h["parentName"])
            )
            if struct_id and trait_id:
                graph.add_relationship(GraphRelationship(
                    source_id=struct_id, target_id=trait_id,
                    relationship_type=RelationshipType.IMPLEMENTS,
                    confidence=1.0,
                    properties={"reason": "trait-impl"},
                ))

    if on_progress is not None:
        on_progress(total, total)
