from __future__ import annotations

import tree_sitter

from ...lib.utils import generate_id
from ..tree_sitter.parser_loader import load_language
from .language_queries import LANGUAGE_QUERIES
from .utils import find_sibling_child, get_language_from_filename
from .framework_detection import detect_framework_from_ast
from ..graph.graph import KnowledgeGraph
from .symbol_table import SymbolTable
from .ast_cache import ASTCache

DEFINITION_CAPTURE_KEYS = [
    "definition.function",
    "definition.class",
    "definition.interface",
    "definition.method",
    "definition.struct",
    "definition.enum",
    "definition.namespace",
    "definition.module",
    "definition.trait",
    "definition.impl",
    "definition.type",
    "definition.const",
    "definition.static",
    "definition.typedef",
    "definition.macro",
    "definition.union",
    "definition.property",
    "definition.record",
    "definition.delegate",
    "definition.annotation",
    "definition.constructor",
    "definition.template",
]

CAPTURE_TO_LABEL: dict[str, str] = {
    "definition.function": "Function",
    "definition.class": "Class",
    "definition.interface": "Interface",
    "definition.method": "Method",
    "definition.struct": "Struct",
    "definition.enum": "Enum",
    "definition.namespace": "Namespace",
    "definition.module": "Module",
    "definition.trait": "Trait",
    "definition.impl": "Impl",
    "definition.type": "TypeAlias",
    "definition.const": "Const",
    "definition.static": "Static",
    "definition.typedef": "Typedef",
    "definition.macro": "Macro",
    "definition.union": "Union",
    "definition.property": "Property",
    "definition.record": "Record",
    "definition.delegate": "Delegate",
    "definition.annotation": "Annotation",
    "definition.constructor": "Constructor",
    "definition.template": "Template",
}


def _get_definition_node(capture_map: dict[str, object]) -> object | None:
    for key in DEFINITION_CAPTURE_KEYS:
        if key in capture_map:
            return capture_map[key]
    return None


def _get_label(capture_map: dict[str, object]) -> str:
    for key, label in CAPTURE_TO_LABEL.items():
        if key in capture_map:
            return label
    return "CodeElement"


def is_node_exported(node: object, name: str, language: str) -> bool:
    current = node
    if language in ("javascript", "typescript"):
        while current is not None:
            t = current.type
            if t == "export_statement" or t == "export_specifier":
                return True
            if (t == "lexical_declaration"
                    and current.parent is not None
                    and current.parent.type == "export_statement"):
                return True
            text = current.text
            if text is not None and text.decode("utf-8", errors="replace").startswith("export "):
                return True
            current = current.parent
        return False
    if language == "python":
        return not name.startswith("_")
    if language == "java":
        while current is not None:
            if current.parent is not None:
                parent = current.parent
                for i in range(parent.child_count):
                    child = parent.child(i)
                    if (child is not None and child.type == "modifiers"
                            and child.text is not None
                            and b"public" in child.text):
                        return True
                if parent.type in ("method_declaration", "constructor_declaration"):
                    if (parent.text is not None
                            and parent.text.lstrip().startswith(b"public")):
                        return True
            current = current.parent
        return False
    if language == "csharp":
        while current is not None:
            if current.type in ("modifier", "modifiers"):
                if current.text is not None and b"public" in current.text:
                    return True
            current = current.parent
        return False
    if language == "go":
        if not name:
            return False
        return name[0].isupper()
    if language == "rust":
        while current is not None:
            if current.type == "visibility_modifier":
                if current.text is not None and b"pub" in current.text:
                    return True
            current = current.parent
        return False
    if language == "kotlin":
        while current is not None:
            if current.parent is not None:
                vis_mod = find_sibling_child(current.parent, "modifiers", "visibility_modifier")
                if vis_mod is not None:
                    text = vis_mod.text.decode("utf-8", errors="replace") if vis_mod.text else ""
                    if text in ("private", "internal", "protected"):
                        return False
                    if text == "public":
                        return True
            current = current.parent
        return True  # Kotlin default = public
    if language in ("c", "cpp"):
        return False
    if language == "swift":
        while current is not None:
            if current.type in ("modifiers", "visibility_modifier"):
                text = current.text.decode("utf-8", errors="replace") if current.text else ""
                if "public" in text or "open" in text:
                    return True
            current = current.parent
        return False
    if language == "php":
        while current is not None:
            if current.type in ("class_declaration", "interface_declaration",
                                "trait_declaration", "enum_declaration"):
                return True
            if current.type == "visibility_modifier":
                return current.text == b"public"
            current = current.parent
        return True  # Top-level functions are globally accessible
    return False
