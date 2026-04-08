"""Sequential parsing fallback."""
from __future__ import annotations

from typing import Any, Callable

import tree_sitter

from ...lib.utils import generate_id
from ..tree_sitter.parser_loader import load_language
from .language_queries import LANGUAGE_QUERIES
from .utils import get_language_from_filename
from .framework_detection import detect_framework_from_ast
from .parsing_processor import (
    _get_definition_node,
    _get_label,
    is_node_exported,
    CAPTURE_TO_LABEL,
)
from ..graph.graph import KnowledgeGraph
from .symbol_table import SymbolTable
from .ast_cache import ASTCache

# Cache compiled queries per language key
_query_cache: dict[str, object] = {}


def process_parsing_sequential(
    graph: KnowledgeGraph,
    files: list[dict[str, str]],
    symbol_table: SymbolTable,
    ast_cache: ASTCache,
    on_file_progress: Callable[[int, int, str], None] | None = None,
) -> None:
    total = len(files)
    for i, file in enumerate(files):
        if on_file_progress is not None:
            on_file_progress(i + 1, total, file["path"])

        language = get_language_from_filename(file["path"])
        if language is None:
            continue

        content = file.get("content", "")
        if len(content) > 512 * 1024:
            continue

        try:
            parser = load_language(language, file["path"])
        except Exception:
            continue

        try:
            tree = parser.parse(content.encode("utf-8"))
        except Exception:
            continue

        ast_cache.set(file["path"], tree)

        query_string = LANGUAGE_QUERIES.get(language)
        if not query_string:
            continue

        try:
            cache_key = language + (":tsx" if file["path"].endswith(".tsx") else "")
            if cache_key not in _query_cache:
                _query_cache[cache_key] = parser.language.query(query_string)
            query = _query_cache[cache_key]
            matches = query.matches(tree.root_node)
        except Exception:
            continue

        for _pattern_idx, capture_dict in matches:
            capture_map: dict[str, Any] = {}
            for capture_name, nodes_list in capture_dict.items():
                if nodes_list:
                    capture_map[capture_name] = nodes_list[0]

            if "import" in capture_map:
                continue
            if "call" in capture_map:
                continue

            name_node = capture_map.get("name")
            if name_node is None and "definition.constructor" not in capture_map:
                continue

            node_name = name_node.text.decode("utf-8", errors="replace") if name_node and name_node.text else "init"
            node_label = _get_label(capture_map)

            definition_node = _get_definition_node(capture_map)
            start_line = (definition_node.start_point[0] if definition_node
                          else (name_node.start_point[0] if name_node else 0))

            node_id = generate_id(node_label, f"{file['path']}:{node_name}:{start_line}")

            framework_hint = None
            if definition_node is not None:
                text_snippet = definition_node.text.decode("utf-8", errors="replace")[:300] if definition_node.text else ""
                framework_hint = detect_framework_from_ast(language, text_snippet)

            props: dict[str, Any] = {
                "name": node_name,
                "filePath": file["path"],
                "startLine": definition_node.start_point[0] if definition_node else start_line,
                "endLine": definition_node.end_point[0] if definition_node else start_line,
                "language": language,
                "isExported": is_node_exported(
                    name_node or definition_node, node_name, language
                ),
            }
            if framework_hint is not None:
                props["astFrameworkMultiplier"] = framework_hint.get("entryPointMultiplier", 1.0)
                props["astFrameworkReason"] = framework_hint.get("reason", "")

            node = {"id": node_id, "label": node_label, "properties": props}
            graph.add_node(node)
            symbol_table.add(file["path"], node_name, node_id, node_label)

            file_id = generate_id("File", file["path"])
            rel_id = generate_id("DEFINES", f"{file_id}->{node_id}")
            relationship = {
                "id": rel_id,
                "sourceId": file_id,
                "targetId": node_id,
                "type": "DEFINES",
                "confidence": 1.0,
                "reason": "",
            }
            graph.add_relationship(relationship)


def process_parsing(
    graph: KnowledgeGraph,
    files: list[dict[str, str]],
    symbol_table: SymbolTable,
    ast_cache: ASTCache,
    on_file_progress: Callable[[int, int, str], None] | None = None,
) -> None:
    # No worker pool in Python — always sequential
    process_parsing_sequential(graph, files, symbol_table, ast_cache, on_file_progress)
