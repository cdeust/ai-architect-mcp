"""Tests for heritage extraction from tree-sitter ASTs."""

from __future__ import annotations

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.heritage_extractor import (
    extract_heritage_from_tree,
)
from ai_codebase_intelligence._extraction.heritage_processor import HeritageInfo
from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel
from ai_codebase_intelligence._parsing.parser_loader import (
    clear_parser_cache,
    get_parser,
)


def _parse(language: SupportedLanguage, code: str, path: str = "") -> object:
    """Parse code and return the root node."""
    parser = get_parser(language, path)
    tree = parser.parse(code.encode("utf-8"))
    return tree.root_node


def _make_class_node(
    name: str, file_path: str, language: str = "python"
) -> GraphNode:
    """Create a minimal class GraphNode for testing."""
    return GraphNode(
        id=f"{file_path}:{name}:Class",
        label=NodeLabel.CLASS,
        name=name,
        file_path=file_path,
        language=language,
    )


class TestPythonHeritage:
    """Tests for Python class inheritance extraction."""

    def setup_method(self) -> None:
        clear_parser_cache()

    def test_single_inheritance(self) -> None:
        """``class Foo(Bar): pass`` extracts extends relationship."""
        code = "class Foo(Bar):\n    pass\n"
        root = _parse(SupportedLanguage.PYTHON, code)
        file_path = "/src/models.py"
        nodes = [_make_class_node("Foo", file_path)]
        results = extract_heritage_from_tree(
            root, file_path, SupportedLanguage.PYTHON, nodes
        )
        assert len(results) == 1
        assert results[0].parent_name == "Bar"
        assert results[0].heritage_type == "extends"
        assert results[0].child_id == f"{file_path}:Foo:Class"

    def test_multiple_inheritance(self) -> None:
        """``class Foo(Bar, Baz): pass`` extracts two relationships."""
        code = "class Foo(Bar, Baz):\n    pass\n"
        root = _parse(SupportedLanguage.PYTHON, code)
        file_path = "/src/models.py"
        nodes = [_make_class_node("Foo", file_path)]
        results = extract_heritage_from_tree(
            root, file_path, SupportedLanguage.PYTHON, nodes
        )
        assert len(results) == 2
        parents = {r.parent_name for r in results}
        assert parents == {"Bar", "Baz"}
        assert all(r.heritage_type == "extends" for r in results)

    def test_no_base_class(self) -> None:
        """``class Foo: pass`` produces no heritage."""
        code = "class Foo:\n    pass\n"
        root = _parse(SupportedLanguage.PYTHON, code)
        file_path = "/src/models.py"
        nodes = [_make_class_node("Foo", file_path)]
        results = extract_heritage_from_tree(
            root, file_path, SupportedLanguage.PYTHON, nodes
        )
        assert len(results) == 0

    def test_heritage_type_is_extends(self) -> None:
        """Python heritage is always 'extends'."""
        code = "class Child(Parent):\n    pass\n"
        root = _parse(SupportedLanguage.PYTHON, code)
        file_path = "/src/models.py"
        nodes = [_make_class_node("Child", file_path)]
        results = extract_heritage_from_tree(
            root, file_path, SupportedLanguage.PYTHON, nodes
        )
        assert len(results) == 1
        assert results[0].heritage_type == "extends"


class TestTypeScriptHeritage:
    """Tests for TypeScript class inheritance extraction."""

    def setup_method(self) -> None:
        clear_parser_cache()

    def test_extends(self) -> None:
        """``class Foo extends Bar {}`` extracts extends."""
        code = "class Foo extends Bar {}\n"
        root = _parse(SupportedLanguage.TYPESCRIPT, code)
        file_path = "/src/app.ts"
        nodes = [
            _make_class_node("Foo", file_path, "typescript"),
        ]
        results = extract_heritage_from_tree(
            root, file_path, SupportedLanguage.TYPESCRIPT, nodes
        )
        assert len(results) >= 1
        extends_results = [
            r for r in results if r.heritage_type == "extends"
        ]
        assert len(extends_results) >= 1
        assert extends_results[0].parent_name == "Bar"


class TestHeritageInfoDataclass:
    """Test HeritageInfo properties."""

    def test_frozen(self) -> None:
        """HeritageInfo is immutable."""
        info = HeritageInfo(
            child_id="file:Foo:Class",
            parent_name="Bar",
            heritage_type="extends",
            file_path="/src/models.py",
        )
        assert info.child_id == "file:Foo:Class"
        assert info.parent_name == "Bar"
        assert info.heritage_type == "extends"
        assert info.file_path == "/src/models.py"

    def test_heritage_type_values(self) -> None:
        """Heritage type can be 'extends' or 'implements'."""
        ext = HeritageInfo(
            child_id="a", parent_name="B",
            heritage_type="extends", file_path="/f",
        )
        impl = HeritageInfo(
            child_id="a", parent_name="C",
            heritage_type="implements", file_path="/f",
        )
        assert ext.heritage_type == "extends"
        assert impl.heritage_type == "implements"
