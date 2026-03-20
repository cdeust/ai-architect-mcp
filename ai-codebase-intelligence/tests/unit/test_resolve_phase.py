"""Tests for resolve phase: import extraction, resolver wiring, edge creation."""

from __future__ import annotations

from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)
from ai_codebase_intelligence._pipeline.resolve_phase import (
    _build_symbol_table,
    _group_nodes_by_file,
    resolve_symbols_and_edges,
)
from ai_codebase_intelligence._resolution.resolvers.standard import (
    StandardResolver,
)
from ai_codebase_intelligence._resolution.resolvers.utils import (
    build_suffix_index,
)
from ai_codebase_intelligence._extraction.import_processor import (
    process_imports,
)
from ai_codebase_intelligence._config.supported_languages import (
    SupportedLanguage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_node(
    node_id: str,
    name: str,
    file_path: str,
    label: NodeLabel = NodeLabel.FUNCTION,
    properties: dict | None = None,
) -> GraphNode:
    """Create a GraphNode for testing.

    Args:
        node_id: Unique node ID.
        name: Symbol name.
        file_path: Source file path.
        label: Node label.
        properties: Optional extra properties.

    Returns:
        A GraphNode instance.
    """
    return GraphNode(
        id=node_id,
        label=label,
        name=name,
        file_path=file_path,
        properties=properties or {},
    )


def _make_import_node(
    file_path: str,
    import_path: str,
    imported_names: list[str] | None = None,
) -> GraphNode:
    """Create an import GraphNode for testing.

    Args:
        file_path: Source file containing the import.
        import_path: The import path string.
        imported_names: Specific names imported.

    Returns:
        A GraphNode with is_import=True properties.
    """
    return GraphNode(
        id=f"{file_path}:import:{import_path}:1",
        label=NodeLabel.MODULE,
        name=import_path,
        file_path=file_path,
        properties={
            "is_import": True,
            "import_path": import_path,
            "imported_names": imported_names or [],
            "is_wildcard": False,
        },
    )


# ===========================================================================
# resolve_symbols_and_edges integration
# ===========================================================================


class TestResolveSymbolsAndEdges:
    """End-to-end tests for the resolve phase orchestrator."""

    def test_returns_three_tuple(self) -> None:
        """resolve_symbols_and_edges returns (rels, table, context)."""
        nodes = [_make_node("a.py:foo:fn", "foo", "a.py")]
        rels: list[GraphRelationship] = []
        result = resolve_symbols_and_edges(nodes, rels, repo_root="")
        assert len(result) == 3
        new_rels, symbol_table, resolution_ctx = result
        assert isinstance(new_rels, list)
        assert symbol_table is not None
        assert resolution_ctx is not None

    def test_symbol_table_populated(self) -> None:
        """Symbol table contains all nodes with file paths."""
        nodes = [
            _make_node("a.py:foo:fn", "foo", "a.py"),
            _make_node("b.py:bar:fn", "bar", "b.py"),
        ]
        _, symbol_table, _ = resolve_symbols_and_edges(nodes, [])
        assert len(symbol_table.all_nodes()) == 2

    def test_empty_input_produces_empty_output(self) -> None:
        """No nodes/rels produces empty results."""
        new_rels, table, ctx = resolve_symbols_and_edges([], [])
        assert new_rels == []
        assert table.all_nodes() == []
        assert ctx.import_map == {}


# ===========================================================================
# _build_symbol_table
# ===========================================================================


class TestBuildSymbolTable:
    """Tests for symbol table construction."""

    def test_registers_nodes_with_file_path(self) -> None:
        """Nodes with file_path are registered."""
        nodes = [_make_node("a.py:X:cls", "X", "a.py")]
        table = _build_symbol_table(nodes)
        assert len(table.lookup_global("X")) == 1

    def test_skips_nodes_without_file_path(self) -> None:
        """Nodes with empty file_path are skipped."""
        node = _make_node("no_file", "Y", "")
        table = _build_symbol_table([node])
        assert table.all_nodes() == []


# ===========================================================================
# _group_nodes_by_file
# ===========================================================================


class TestGroupNodesByFile:
    """Tests for file grouping."""

    def test_groups_by_file_path(self) -> None:
        """Nodes are grouped by their file_path."""
        nodes = [
            _make_node("a.py:X:cls", "X", "a.py"),
            _make_node("a.py:Y:fn", "Y", "a.py"),
            _make_node("b.py:Z:fn", "Z", "b.py"),
        ]
        groups = _group_nodes_by_file(nodes)
        assert len(groups["a.py"]) == 2
        assert len(groups["b.py"]) == 1

    def test_skips_empty_file_path(self) -> None:
        """Nodes with empty file_path are excluded."""
        nodes = [_make_node("no_file", "X", "")]
        groups = _group_nodes_by_file(nodes)
        assert groups == {}


# ===========================================================================
# process_imports with import nodes
# ===========================================================================


class TestProcessImportsWithResolvers:
    """Tests that process_imports creates IMPORTS edges via resolvers."""

    def test_creates_imports_edge_for_resolved_import(self) -> None:
        """An import node that resolves produces an IMPORTS edge."""
        index = build_suffix_index(["/src/utils.py", "/src/main.py"])
        resolver = StandardResolver(suffix_index=index)

        import_node = _make_import_node("/src/main.py", "utils")
        result = process_imports(
            nodes=[import_node],
            file_path="/src/main.py",
            language=SupportedLanguage.PYTHON,
            suffix_index=index,
            resolver=resolver,
        )
        assert len(result.relationships) == 1
        rel = result.relationships[0]
        assert rel.relationship_type == RelationshipType.IMPORTS
        assert rel.source_id == "/src/main.py:File"
        assert rel.target_id == "/src/utils.py:File"

    def test_import_map_populated(self) -> None:
        """Import map contains resolved file paths."""
        index = build_suffix_index(["/src/utils.py", "/src/main.py"])
        resolver = StandardResolver(suffix_index=index)

        import_node = _make_import_node("/src/main.py", "utils")
        result = process_imports(
            nodes=[import_node],
            file_path="/src/main.py",
            language=SupportedLanguage.PYTHON,
            suffix_index=index,
            resolver=resolver,
        )
        assert "/src/utils.py" in result.import_map["/src/main.py"]

    def test_unresolved_import_produces_no_edge(self) -> None:
        """An import that cannot resolve produces no edge."""
        index = build_suffix_index(["/src/main.py"])
        resolver = StandardResolver(suffix_index=index)

        import_node = _make_import_node("/src/main.py", "nonexistent")
        result = process_imports(
            nodes=[import_node],
            file_path="/src/main.py",
            language=SupportedLanguage.PYTHON,
            suffix_index=index,
            resolver=resolver,
        )
        assert result.relationships == []

    def test_non_import_nodes_are_filtered_out(self) -> None:
        """Regular symbol nodes are not treated as imports."""
        index = build_suffix_index(["/src/utils.py", "/src/main.py"])
        resolver = StandardResolver(suffix_index=index)

        regular_node = _make_node(
            "main.py:foo:fn", "foo", "/src/main.py"
        )
        result = process_imports(
            nodes=[regular_node],
            file_path="/src/main.py",
            language=SupportedLanguage.PYTHON,
            suffix_index=index,
            resolver=resolver,
        )
        assert result.relationships == []

    def test_python_from_import_creates_named_bindings(self) -> None:
        """'from utils import helper' produces named binding."""
        index = build_suffix_index(["/src/utils.py", "/src/main.py"])
        resolver = StandardResolver(suffix_index=index)

        import_node = _make_import_node(
            "/src/main.py", "utils", imported_names=["helper"]
        )
        result = process_imports(
            nodes=[import_node],
            file_path="/src/main.py",
            language=SupportedLanguage.PYTHON,
            suffix_index=index,
            resolver=resolver,
        )
        named = result.named_import_map.get("/src/main.py", {})
        assert named.get("helper") == "/src/utils.py"

    def test_multiple_imports_produce_multiple_edges(self) -> None:
        """Multiple import nodes create multiple IMPORTS edges."""
        index = build_suffix_index([
            "/src/a.py", "/src/b.py", "/src/main.py",
        ])
        resolver = StandardResolver(suffix_index=index)

        import_a = _make_import_node("/src/main.py", "a")
        import_b = _make_import_node("/src/main.py", "b")
        result = process_imports(
            nodes=[import_a, import_b],
            file_path="/src/main.py",
            language=SupportedLanguage.PYTHON,
            suffix_index=index,
            resolver=resolver,
        )
        assert len(result.relationships) == 2
        targets = {r.target_id for r in result.relationships}
        assert "/src/a.py:File" in targets
        assert "/src/b.py:File" in targets


# ===========================================================================
# Suffix index building
# ===========================================================================


class TestSuffixIndexInResolvePhase:
    """Tests that suffix index integrates correctly with resolve phase."""

    def test_suffix_index_enables_resolution(self) -> None:
        """Suffix index built from file paths enables resolver lookups."""
        index = build_suffix_index([
            "/repo/src/models.py",
            "/repo/src/views.py",
        ])
        resolver = StandardResolver(suffix_index=index)
        assert resolver.resolve("models", "/repo/src/app.py") == "/repo/src/models.py"
        assert resolver.resolve("views", "/repo/src/app.py") == "/repo/src/views.py"

    def test_suffix_index_parent_stem(self) -> None:
        """Parent/stem lookup works for package imports."""
        index = build_suffix_index(["/repo/src/pkg/utils.py"])
        resolver = StandardResolver(suffix_index=index)
        result = resolver.resolve("pkg.utils", "/repo/src/main.py")
        assert result == "/repo/src/pkg/utils.py"
