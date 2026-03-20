"""Tests for the _resolution package: SymbolTable, ResolutionContext, TypeEnvironment."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel
from ai_codebase_intelligence._resolution.symbol_table import SymbolTable
from ai_codebase_intelligence._resolution.resolution_context import (
    CACHE_MAX_SIZE,
    GLOBAL_CONFIDENCE,
    IMPORT_SCOPED_CONFIDENCE,
    NAMED_IMPORT_CONFIDENCE,
    SAME_FILE_CONFIDENCE,
    ResolutionContext,
)
from ai_codebase_intelligence._resolution.type_env import TypeEnvironment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(
    node_id: str,
    name: str,
    file_path: str,
    label: NodeLabel = NodeLabel.FUNCTION,
) -> GraphNode:
    return GraphNode(id=node_id, label=label, name=name, file_path=file_path)


# ===========================================================================
# SymbolTable
# ===========================================================================


class TestSymbolTableRegister:
    def test_register_and_lookup_in_file(self) -> None:
        st = SymbolTable()
        node = _make_node("a.py:foo:fn", "foo", "a.py")
        st.register(node)
        result = st.lookup_in_file("a.py", "foo")
        assert len(result) == 1
        assert result[0].id == "a.py:foo:fn"

    def test_register_duplicate_is_idempotent(self) -> None:
        st = SymbolTable()
        node = _make_node("a.py:foo:fn", "foo", "a.py")
        st.register(node)
        st.register(node)
        assert len(st.lookup_in_file("a.py", "foo")) == 1
        assert len(st.lookup_global("foo")) == 1

    def test_lookup_in_file_returns_empty_for_missing(self) -> None:
        st = SymbolTable()
        assert st.lookup_in_file("a.py", "missing") == []

    def test_lookup_global(self) -> None:
        st = SymbolTable()
        st.register(_make_node("a.py:foo:fn", "foo", "a.py"))
        st.register(_make_node("b.py:foo:fn", "foo", "b.py"))
        result = st.lookup_global("foo")
        assert len(result) == 2
        ids = {n.id for n in result}
        assert ids == {"a.py:foo:fn", "b.py:foo:fn"}

    def test_lookup_global_returns_empty_for_missing(self) -> None:
        st = SymbolTable()
        assert st.lookup_global("missing") == []

    def test_all_nodes(self) -> None:
        st = SymbolTable()
        st.register(_make_node("a.py:foo:fn", "foo", "a.py"))
        st.register(_make_node("b.py:bar:fn", "bar", "b.py"))
        assert len(st.all_nodes()) == 2

    def test_clear(self) -> None:
        st = SymbolTable()
        st.register(_make_node("a.py:foo:fn", "foo", "a.py"))
        st.clear()
        assert st.all_nodes() == []
        assert st.lookup_global("foo") == []


# ===========================================================================
# ResolutionContext
# ===========================================================================


class TestResolutionTiers:
    def _build_context(self) -> ResolutionContext:
        st = SymbolTable()
        st.register(_make_node("a.py:Foo:cls", "Foo", "a.py"))
        st.register(_make_node("b.py:Bar:cls", "Bar", "b.py"))
        st.register(_make_node("c.py:Baz:cls", "Baz", "c.py"))
        st.register(_make_node("d.py:Qux:cls", "Qux", "d.py"))
        return ResolutionContext(
            symbol_table=st,
            import_map={"a.py": ["b.py"]},
            named_imports={"a.py": {"Bar": "b.py"}},
        )

    def test_tier1_same_file(self) -> None:
        ctx = self._build_context()
        result = ctx.resolve("Foo", "a.py")
        assert result is not None
        assert result.tier == "same_file"
        assert result.confidence == SAME_FILE_CONFIDENCE

    def test_tier2_named_import(self) -> None:
        ctx = self._build_context()
        result = ctx.resolve("Bar", "a.py")
        assert result is not None
        assert result.tier == "named_import"
        assert result.confidence == NAMED_IMPORT_CONFIDENCE

    def test_tier3_import_scoped(self) -> None:
        """Bar is also in import_map for a.py, but named_import wins.
        Use Baz via import_map to test tier 3."""
        st = SymbolTable()
        st.register(_make_node("a.py:Local:cls", "Local", "a.py"))
        st.register(_make_node("b.py:Imported:cls", "Imported", "b.py"))
        ctx = ResolutionContext(
            symbol_table=st,
            import_map={"a.py": ["b.py"]},
            named_imports={},
        )
        result = ctx.resolve("Imported", "a.py")
        assert result is not None
        assert result.tier == "import_scoped"
        assert result.confidence == IMPORT_SCOPED_CONFIDENCE

    def test_tier4_global(self) -> None:
        ctx = self._build_context()
        # Qux is in d.py which is not imported by a.py
        result = ctx.resolve("Qux", "a.py")
        assert result is not None
        assert result.tier == "global"
        assert result.confidence == GLOBAL_CONFIDENCE

    def test_unresolved_returns_none(self) -> None:
        ctx = self._build_context()
        assert ctx.resolve("NonExistent", "a.py") is None


class TestResolutionCache:
    def test_cache_hit(self) -> None:
        st = SymbolTable()
        st.register(_make_node("a.py:X:cls", "X", "a.py"))
        ctx = ResolutionContext(symbol_table=st)
        r1 = ctx.resolve("X", "a.py")
        r2 = ctx.resolve("X", "a.py")
        assert r1 is r2  # Same object from cache

    def test_cache_stores_none(self) -> None:
        st = SymbolTable()
        ctx = ResolutionContext(symbol_table=st)
        assert ctx.resolve("Missing", "a.py") is None
        # Second call should still return None from cache
        assert ctx.resolve("Missing", "a.py") is None
        assert ("a.py", "Missing") in ctx._cache

    def test_cache_eviction_at_max_size(self) -> None:
        st = SymbolTable()
        for i in range(CACHE_MAX_SIZE + 50):
            st.register(
                _make_node(f"f.py:sym{i}:fn", f"sym{i}", "f.py")
            )
        ctx = ResolutionContext(symbol_table=st)
        for i in range(CACHE_MAX_SIZE + 50):
            ctx.resolve(f"sym{i}", "f.py")
        assert len(ctx._cache) == CACHE_MAX_SIZE

    def test_clear_cache(self) -> None:
        st = SymbolTable()
        st.register(_make_node("a.py:X:cls", "X", "a.py"))
        ctx = ResolutionContext(symbol_table=st)
        ctx.resolve("X", "a.py")
        assert len(ctx._cache) == 1
        ctx.clear_cache()
        assert len(ctx._cache) == 0


# ===========================================================================
# TypeEnvironment
# ===========================================================================


class TestTypeEnvironmentBind:
    def test_bind_and_resolve(self) -> None:
        env = TypeEnvironment()
        env.bind("x", "int", "function", "a.py")
        assert env.resolve_type("x", "function", "a.py") == "int"

    def test_resolve_missing_returns_none(self) -> None:
        env = TypeEnvironment()
        assert env.resolve_type("x", "function", "a.py") is None

    def test_invalid_scope_raises(self) -> None:
        env = TypeEnvironment()
        with pytest.raises(ValueError, match="Invalid scope"):
            env.bind("x", "int", "invalid_scope", "a.py")


class TestTypeEnvironmentScopePriority:
    def test_function_scope_over_file_scope(self) -> None:
        env = TypeEnvironment()
        env.bind("x", "str", "file", "a.py")
        env.bind("x", "int", "function", "a.py")
        assert env.resolve_type("x", "function", "a.py") == "int"

    def test_file_scope_when_function_not_requested(self) -> None:
        """When querying at file scope, function bindings are excluded."""
        env = TypeEnvironment()
        env.bind("x", "str", "file", "a.py")
        env.bind("x", "int", "function", "a.py")
        assert env.resolve_type("x", "file", "a.py") == "str"

    def test_class_scope_between_function_and_file(self) -> None:
        env = TypeEnvironment()
        env.bind("x", "str", "file", "a.py")
        env.bind("x", "list", "class", "a.py")
        env.bind("x", "int", "function", "a.py")
        # At class scope, function is excluded, class wins over file
        assert env.resolve_type("x", "class", "a.py") == "list"

    def test_different_files_are_isolated(self) -> None:
        env = TypeEnvironment()
        env.bind("x", "int", "function", "a.py")
        assert env.resolve_type("x", "function", "b.py") is None


class TestTypeEnvironmentSelfResolution:
    def test_resolve_self_in_class(self) -> None:
        env = TypeEnvironment()
        classes = {"MyClass": (10, 50)}
        assert env.resolve_self("a.py", 25, classes) == "MyClass"

    def test_resolve_self_outside_class(self) -> None:
        env = TypeEnvironment()
        classes = {"MyClass": (10, 50)}
        assert env.resolve_self("a.py", 5, classes) is None

    def test_resolve_self_innermost_class(self) -> None:
        env = TypeEnvironment()
        classes = {
            "Outer": (1, 100),
            "Inner": (20, 40),
        }
        assert env.resolve_self("a.py", 30, classes) == "Inner"

    def test_resolve_self_no_classes(self) -> None:
        env = TypeEnvironment()
        assert env.resolve_self("a.py", 10, {}) is None


class TestTypeEnvironmentClear:
    def test_clear(self) -> None:
        env = TypeEnvironment()
        env.bind("x", "int", "function", "a.py")
        env.clear()
        assert env.resolve_type("x", "function", "a.py") is None
