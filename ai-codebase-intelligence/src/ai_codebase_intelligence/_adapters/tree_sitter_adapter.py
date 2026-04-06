"""Tree-sitter concrete adapter implementing ParserPort.

Uses tree-sitter 0.23.x — the last version with working Query.matches().
tree-sitter 0.25.x removed query execution from Python bindings.

OBSERVATION: tree-sitter 0.25.2 compiles queries but has no matches() method.
PROBLEM: All symbol extraction depends on tree-sitter query execution.
  Without it, parsing produces zero nodes — the entire pipeline fails.
SOLUTION: Pin tree-sitter==0.23.2 which has full Query.matches()/captures().
  Per-language grammar packages (tree-sitter-swift, etc.) are compatible.
VERIFICATION: 13 nodes extracted from AuditFlagEngine.swift with 0.23.2.
  0 nodes with 0.25.2 (matches() AttributeError).
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

import tree_sitter

from .ports import ParserPort
from .._config.models import IndexingSection
from .._models.graph_types import GraphNode, GraphRelationship, NodeLabel, RelationshipType

logger = logging.getLogger(__name__)

_GRAMMAR_MODULES: dict[str, str] = {
    "javascript": "tree_sitter_javascript",
    "typescript": "tree_sitter_typescript",
    "typescript:tsx": "tree_sitter_typescript",
    "python": "tree_sitter_python",
    "java": "tree_sitter_java",
    "c": "tree_sitter_c",
    "cpp": "tree_sitter_cpp",
    "csharp": "tree_sitter_c_sharp",
    "go": "tree_sitter_go",
    "rust": "tree_sitter_rust",
    "kotlin": "tree_sitter_kotlin",
    "php": "tree_sitter_php",
    "swift": "tree_sitter_swift",
}

_GRAMMAR_ATTR: dict[str, str] = {
    "typescript": "language_typescript",
    "typescript:tsx": "language_tsx",
    "php": "language_php",
}

_CAPTURE_TO_LABEL: dict[str, NodeLabel] = {
    "definition.function": NodeLabel.FUNCTION,
    "definition.class": NodeLabel.CLASS,
    "definition.interface": NodeLabel.INTERFACE,
    "definition.method": NodeLabel.METHOD,
    "definition.struct": NodeLabel.STRUCT,
    "definition.enum": NodeLabel.ENUM,
    "definition.namespace": NodeLabel.NAMESPACE,
    "definition.module": NodeLabel.MODULE,
    "definition.trait": NodeLabel.TRAIT,
    "definition.impl": NodeLabel.IMPL,
    "definition.type": NodeLabel.TYPE_ALIAS,
    "definition.const": NodeLabel.CONST,
    "definition.static": NodeLabel.STATIC,
    "definition.typedef": NodeLabel.TYPEDEF,
    "definition.macro": NodeLabel.MACRO,
    "definition.union": NodeLabel.UNION,
    "definition.property": NodeLabel.PROPERTY,
    "definition.record": NodeLabel.RECORD,
    "definition.delegate": NodeLabel.DELEGATE,
    "definition.annotation": NodeLabel.ANNOTATION,
    "definition.constructor": NodeLabel.CONSTRUCTOR,
    "definition.template": NodeLabel.TEMPLATE,
}


class TreeSitterParser(ParserPort):
    """Tree-sitter 0.23 parser with cached parsers and queries.

    Args:
        config: Indexing configuration section.
    """

    def __init__(self, config: IndexingSection | None = None) -> None:
        self._config = config
        self._parsers: dict[str, tree_sitter.Parser] = {}
        self._languages: dict[str, tree_sitter.Language] = {}
        self._queries: dict[str, Any] = {}

    def _get_parser(self, language: str, file_path: str = "") -> tuple[tree_sitter.Parser, tree_sitter.Language]:
        """Get or create a cached parser for a language."""
        key = f"{language}:tsx" if language == "typescript" and file_path.endswith(".tsx") else language

        if key in self._parsers:
            return self._parsers[key], self._languages[key]

        module_name = _GRAMMAR_MODULES.get(key)
        if not module_name:
            raise ValueError(f"Unsupported language: {language}")

        mod = importlib.import_module(module_name)
        attr = _GRAMMAR_ATTR.get(key, "language")
        lang = tree_sitter.Language(getattr(mod, attr)())

        parser = tree_sitter.Parser()
        parser.language = lang

        self._parsers[key] = parser
        self._languages[key] = lang
        return parser, lang

    def _get_query(self, language: str, lang_obj: tree_sitter.Language) -> Any | None:
        """Get or compile a cached query for a language."""
        if language in self._queries:
            return self._queries[language]

        from ..core.ingestion.language_queries import LANGUAGE_QUERIES
        query_str = LANGUAGE_QUERIES.get(language)
        if not query_str:
            return None

        try:
            query = lang_obj.query(query_str)
            self._queries[language] = query
            return query
        except Exception as exc:
            logger.debug("Query compile failed for %s: %s", language, exc)
            return None

    def parse_file(
        self, file_path: str, content: str, language: str
    ) -> list[GraphNode]:
        """Parse a file and extract symbol nodes."""
        max_size = self._config.max_file_size_bytes if self._config else 524288
        if len(content) > max_size:
            return []

        try:
            parser, lang = self._get_parser(language, file_path)
        except (ValueError, ImportError):
            return []

        try:
            tree = parser.parse(content.encode("utf-8"))
        except Exception:
            return []

        query = self._get_query(language, lang)
        if not query:
            return []

        try:
            matches = query.matches(tree.root_node)
        except Exception:
            return []

        nodes: list[GraphNode] = []
        for _pattern, capture_dict in matches:
            cm: dict[str, Any] = {}
            for cname, node_list in capture_dict.items():
                if node_list:
                    cm[cname] = node_list[0]

            if "import" in cm or "call" in cm:
                continue

            name_node = cm.get("name")
            if not name_node and "definition.constructor" not in cm:
                continue

            node_name = name_node.text.decode("utf-8") if name_node and name_node.text else "init"
            node_label = NodeLabel.VARIABLE
            for cap_key, label in _CAPTURE_TO_LABEL.items():
                if cap_key in cm:
                    node_label = label
                    break

            def_node = None
            for cap_key in _CAPTURE_TO_LABEL:
                if cap_key in cm:
                    def_node = cm[cap_key]
                    break

            sl = def_node.start_point[0] if def_node else (name_node.start_point[0] if name_node else 0)
            el = def_node.end_point[0] if def_node else sl
            nid = f"{node_label.value}:{file_path}:{node_name}:{sl}"

            nodes.append(GraphNode(
                id=nid, label=node_label, name=node_name,
                file_path=file_path, start_line=sl, end_line=el,
                language=language,
            ))

        return nodes

    def extract_calls(
        self, file_path: str, content: str, language: str
    ) -> list[GraphRelationship]:
        """Extract CALLS relationships from a file."""
        try:
            parser, lang = self._get_parser(language, file_path)
        except (ValueError, ImportError):
            return []

        try:
            tree = parser.parse(content.encode("utf-8"))
        except Exception:
            return []

        query = self._get_query(language, lang)
        if not query:
            return []

        try:
            matches = query.matches(tree.root_node)
        except Exception:
            return []

        calls: list[GraphRelationship] = []
        for _pattern, capture_dict in matches:
            cm: dict[str, Any] = {}
            for cname, node_list in capture_dict.items():
                if node_list:
                    cm[cname] = node_list[0]

            if "call" not in cm:
                continue
            call_name_node = cm.get("call.name")
            if not call_name_node:
                continue

            called_name = call_name_node.text.decode("utf-8") if call_name_node.text else ""
            if not called_name:
                continue

            calls.append(GraphRelationship(
                source_id=f"File:{file_path}",
                target_id=called_name,
                relationship_type=RelationshipType.CALLS,
                confidence=0.5,
                properties={"reason": "ast-call-site"},
            ))

        return calls

    def is_language_supported(self, language: str) -> bool:
        """Check if a language has a tree-sitter grammar available."""
        return language in _GRAMMAR_MODULES
