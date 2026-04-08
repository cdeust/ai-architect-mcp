"""AST-based call site extraction.

Walks a tree-sitter AST to find all function/method calls and
classifies each one using the call_routing module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.call_routing import CallForm, classify_call
from ai_codebase_intelligence._extraction.enclosing_scope import (
    find_enclosing_function,
)

if TYPE_CHECKING:
    from ai_codebase_intelligence._models.graph_types import GraphNode


@dataclass(frozen=True, slots=True)
class ExtractedCall:
    """A call site extracted from a tree-sitter AST.

    Args:
        name: The function or method name being called.
        receiver: The receiver expression (e.g. "self", "obj"), or
            empty string for free calls.
        form: The classified call form.
        line: 1-based line number of the call site.
        arguments_count: Number of arguments at the call site.
        enclosing_function_id: ID of the enclosing function node, or
            None for module-level calls.
    """

    name: str
    receiver: str
    form: CallForm
    line: int
    arguments_count: int
    enclosing_function_id: str | None


def extract_calls_from_tree(
    root_node: object,
    file_path: str,
    language: SupportedLanguage,
    function_nodes: list[GraphNode],
) -> list[ExtractedCall]:
    """Extract all call sites from a tree-sitter AST.

    Args:
        root_node: The root tree-sitter node.
        file_path: Path to the source file (for context).
        language: The source language.
        function_nodes: Known function/method GraphNodes for
            enclosing-scope resolution.

    Returns:
        A list of ExtractedCall instances, one per call site.
    """
    calls: list[ExtractedCall] = []
    _walk_calls(root_node, file_path, language, function_nodes, calls)
    return calls


def _walk_calls(
    node: object,
    file_path: str,
    language: SupportedLanguage,
    function_nodes: list[GraphNode],
    out: list[ExtractedCall],
) -> None:
    """Recursively walk the AST collecting call nodes.

    Args:
        node: Current tree-sitter node.
        file_path: Source file path.
        language: Source language.
        function_nodes: Enclosing function candidates.
        out: Accumulator list for extracted calls.
    """
    if node.type == "call":  # type: ignore[union-attr]
        call = _extract_python_call(node, file_path, language, function_nodes)
        if call is not None:
            out.append(call)

    for child in node.named_children:  # type: ignore[union-attr]
        _walk_calls(child, file_path, language, function_nodes, out)


def _extract_python_call(
    node: object,
    file_path: str,
    language: SupportedLanguage,
    function_nodes: list[GraphNode],
) -> ExtractedCall | None:
    """Extract a single Python call node into an ExtractedCall.

    Args:
        node: A tree-sitter "call" node.
        file_path: Source file path.
        language: Source language.
        function_nodes: Enclosing function candidates.

    Returns:
        An ExtractedCall, or None if the call cannot be parsed.
    """
    func_node = node.child_by_field_name("function")  # type: ignore[union-attr]
    if func_node is None:
        return None

    name = ""
    receiver = ""

    if func_node.type == "identifier":
        name = func_node.text.decode("utf-8", errors="replace")
    elif func_node.type == "attribute":
        obj = func_node.child_by_field_name("object")
        attr = func_node.child_by_field_name("attribute")
        if attr is not None:
            name = attr.text.decode("utf-8", errors="replace")
        if obj is not None:
            receiver = obj.text.decode("utf-8", errors="replace")
    else:
        name = func_node.text.decode("utf-8", errors="replace")

    args_node = node.child_by_field_name("arguments")  # type: ignore[union-attr]
    arg_count = 0
    if args_node is not None:
        arg_count = len(args_node.named_children)

    line = node.start_point[0] + 1  # type: ignore[union-attr]
    form = classify_call(name, receiver, language)
    enclosing = find_enclosing_function(node, function_nodes)

    return ExtractedCall(
        name=name,
        receiver=receiver,
        form=form,
        line=line,
        arguments_count=arg_count,
        enclosing_function_id=enclosing,
    )
