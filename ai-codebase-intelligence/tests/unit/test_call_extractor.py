"""Tests for AST-based call extraction."""

from __future__ import annotations

import tree_sitter
import tree_sitter_python

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.call_extractor import (
    extract_calls_from_tree,
)
from ai_codebase_intelligence._extraction.call_routing import CallForm
from ai_codebase_intelligence._extraction.enclosing_scope import (
    find_enclosing_function,
)
from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel


def _parse_python(source: str) -> object:
    """Parse Python source and return the root node."""
    lang = tree_sitter.Language(tree_sitter_python.language())
    parser = tree_sitter.Parser(lang)
    tree = parser.parse(source.encode("utf-8"))
    return tree.root_node


def _make_func_node(
    name: str,
    start_line: int,
    end_line: int,
    file_path: str = "test.py",
    label: NodeLabel = NodeLabel.FUNCTION,
) -> GraphNode:
    """Create a GraphNode for a function/method."""
    return GraphNode(
        id=f"{file_path}:{name}:{label.value}",
        label=label,
        name=name,
        qualified_name=f"{file_path}:{name}",
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        language="python",
    )


class TestPythonFreeCallExtraction:
    """Test extraction of free function calls in Python."""

    def test_simple_free_call(self) -> None:
        """Extract a simple free function call like foo()."""
        source = "def main():\n    foo()\n"
        root = _parse_python(source)
        nodes = [_make_func_node("main", 1, 2)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        assert len(calls) == 1
        assert calls[0].name == "foo"
        assert calls[0].receiver == ""
        assert calls[0].form == CallForm.FREE

    def test_free_call_with_args(self) -> None:
        """Extract a free call with arguments and count them."""
        source = "def main():\n    print(x, y, z)\n"
        root = _parse_python(source)
        nodes = [_make_func_node("main", 1, 2)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        assert len(calls) == 1
        assert calls[0].name == "print"
        assert calls[0].arguments_count == 3

    def test_multiple_free_calls(self) -> None:
        """Extract multiple calls from one function."""
        source = "def main():\n    foo()\n    bar()\n    baz()\n"
        root = _parse_python(source)
        nodes = [_make_func_node("main", 1, 4)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        assert len(calls) == 3
        names = {c.name for c in calls}
        assert names == {"foo", "bar", "baz"}


class TestPythonMemberCallExtraction:
    """Test extraction of member method calls in Python."""

    def test_self_method_call(self) -> None:
        """Extract self.bar() as a member call."""
        source = "def process(self):\n    self.bar()\n"
        root = _parse_python(source)
        nodes = [_make_func_node("process", 1, 2)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        assert len(calls) == 1
        assert calls[0].name == "bar"
        assert calls[0].receiver == "self"
        assert calls[0].form == CallForm.MEMBER

    def test_object_method_call(self) -> None:
        """Extract obj.method() as a member call."""
        source = "def process():\n    obj.method()\n"
        root = _parse_python(source)
        nodes = [_make_func_node("process", 1, 2)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        assert len(calls) == 1
        assert calls[0].name == "method"
        assert calls[0].receiver == "obj"


class TestPythonConstructorCallExtraction:
    """Test extraction of constructor / class calls in Python."""

    def test_class_instantiation(self) -> None:
        """Extract MyClass() as a constructor call."""
        source = "def main():\n    MyClass()\n"
        root = _parse_python(source)
        nodes = [_make_func_node("main", 1, 2)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        assert len(calls) == 1
        assert calls[0].name == "MyClass"
        assert calls[0].receiver == ""

    def test_super_init_call(self) -> None:
        """Extract super().__init__() call chain."""
        source = "def __init__(self):\n    super().__init__()\n"
        root = _parse_python(source)
        nodes = [_make_func_node("__init__", 1, 2)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        # There are two calls: super() and super().__init__()
        assert len(calls) >= 1
        names = {c.name for c in calls}
        assert "super" in names or "__init__" in names


class TestPythonModuleLevelCalls:
    """Test extraction of calls at module level (no enclosing function)."""

    def test_module_level_call(self) -> None:
        """Module-level call has no enclosing function."""
        source = "foo()\n"
        root = _parse_python(source)

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, []
        )

        assert len(calls) == 1
        assert calls[0].name == "foo"
        assert calls[0].line == 1


class TestEnclosingFunction:
    """Test finding the enclosing function for a call site."""

    def test_find_enclosing_for_call(self) -> None:
        """Call inside a function should find that function."""
        source = "def outer():\n    foo()\n"
        root = _parse_python(source)
        func_node = _make_func_node("outer", 1, 2)

        # Walk to find the call node
        call_node = _find_call_node(root)
        assert call_node is not None

        result = find_enclosing_function(call_node, [func_node])
        assert result == func_node.id

    def test_no_enclosing_at_module_level(self) -> None:
        """Module-level call has no enclosing function."""
        source = "foo()\n"
        root = _parse_python(source)

        call_node = _find_call_node(root)
        assert call_node is not None

        result = find_enclosing_function(call_node, [])
        assert result is None

    def test_nested_functions_finds_inner(self) -> None:
        """Call in inner function should find the inner, not outer."""
        source = (
            "def outer():\n"
            "    def inner():\n"
            "        foo()\n"
        )
        root = _parse_python(source)
        outer_node = _make_func_node("outer", 1, 3)
        inner_node = _make_func_node("inner", 2, 3)

        call_node = _find_call_node(root)
        assert call_node is not None

        result = find_enclosing_function(call_node, [outer_node, inner_node])
        assert result == inner_node.id


class TestCallLineNumbers:
    """Test that extracted calls have correct line numbers."""

    def test_line_numbers(self) -> None:
        """Each call should have the correct 1-based line number."""
        source = (
            "def main():\n"
            "    a()\n"
            "    b()\n"
            "    c()\n"
        )
        root = _parse_python(source)
        nodes = [_make_func_node("main", 1, 4)]

        calls = extract_calls_from_tree(
            root, "test.py", SupportedLanguage.PYTHON, nodes
        )

        lines = sorted(c.line for c in calls)
        assert lines == [2, 3, 4]


def _find_call_node(node: object) -> object | None:
    """Find the first 'call' node in the AST by DFS."""
    if node.type == "call":
        return node
    for child in node.named_children:
        found = _find_call_node(child)
        if found is not None:
            return found
    return None
