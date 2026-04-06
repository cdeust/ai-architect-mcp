from __future__ import annotations

from typing import Any, Callable

import tree_sitter

from ..._models.graph_types import GraphRelationship, RelationshipType
from ...lib.utils import generate_id
from ..tree_sitter.parser_loader import load_language
from .language_queries import LANGUAGE_QUERIES
from .utils import get_language_from_filename
from ..graph.graph import KnowledgeGraph
from .symbol_table import SymbolTable
from .ast_cache import ASTCache
from .call_processor import (
    BUILT_IN_NAMES,
    _find_enclosing_function,
    _resolve_call_target,
)

_query_cache: dict[str, object] = {}


def process_calls(
    graph: KnowledgeGraph,
    files: list[dict[str, str]],
    ast_cache: ASTCache,
    symbol_table: SymbolTable,
    import_map: dict[str, set[str]],
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
            cache_key = f"call:{language}"
            if cache_key not in _query_cache:
                _query_cache[cache_key] = parser.language.query(query_str)
            query = _query_cache[cache_key]
            matches = query.matches(tree.root_node)
        except Exception:
            continue

        for _pattern_idx, capture_dict in matches:
            capture_map: dict[str, Any] = {}
            for capture_name, nodes_list in capture_dict.items():
                if nodes_list:
                    capture_map[capture_name] = nodes_list[0]

            if "call" not in capture_map:
                continue

            name_node = capture_map.get("call.name")
            if name_node is None:
                continue

            called_name = name_node.text.decode("utf-8") if name_node.text else ""
            if called_name in BUILT_IN_NAMES:
                continue

            resolved = _resolve_call_target(
                called_name, file["path"], symbol_table, import_map
            )
            if resolved is None:
                continue

            call_node = capture_map["call"]
            enclosing_func_id = _find_enclosing_function(
                call_node, file["path"], symbol_table
            )
            source_id = enclosing_func_id or generate_id("File", file["path"])

            graph.add_relationship(GraphRelationship(
                source_id=source_id,
                target_id=resolved["nodeId"],
                relationship_type=RelationshipType.CALLS,
                confidence=resolved["confidence"],
                properties={"reason": resolved["reason"]},
            ))


def process_calls_from_extracted(
    graph: KnowledgeGraph,
    extracted_calls: list[dict[str, str]],
    symbol_table: SymbolTable,
    import_map: dict[str, set[str]],
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    by_file: dict[str, list[dict[str, str]]] = {}
    for call in extracted_calls:
        by_file.setdefault(call["filePath"], []).append(call)

    total_files = len(by_file)
    files_processed = 0
    for _file_path, calls in by_file.items():
        files_processed += 1
        if files_processed % 100 == 0 and on_progress is not None:
            on_progress(files_processed, total_files)

        for call in calls:
            resolved = _resolve_call_target(
                call["calledName"], call["filePath"],
                symbol_table, import_map,
            )
            if resolved is None:
                continue
            graph.add_relationship(GraphRelationship(
                source_id=call["sourceId"],
                target_id=resolved["nodeId"],
                relationship_type=RelationshipType.CALLS,
                confidence=resolved["confidence"],
                properties={"reason": resolved["reason"]},
            ))

    if on_progress is not None:
        on_progress(total_files, total_files)
