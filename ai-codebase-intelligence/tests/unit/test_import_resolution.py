"""Tests for import resolution: suffix index, cache, and per-language resolvers."""

from __future__ import annotations

from ai_codebase_intelligence._resolution.resolvers.utils import (
    build_suffix_index,
)
from ai_codebase_intelligence._resolution.resolvers.standard import (
    ResolutionCache,
    StandardResolver,
)
from ai_codebase_intelligence._resolution.resolvers.go import GoResolver
from ai_codebase_intelligence._resolution.resolvers.ruby import RubyResolver
from ai_codebase_intelligence._resolution.resolvers.rust import RustResolver


# --- SuffixIndex building and lookup ---


class TestSuffixIndex:
    """Tests for build_suffix_index."""

    def test_bare_stem_lookup(self) -> None:
        """Bare filename stem is indexed."""
        index = build_suffix_index(["/src/models.py", "/src/views.py"])
        assert "models" in index
        assert index["models"] == ["/src/models.py"]

    def test_parent_stem_lookup(self) -> None:
        """parent/stem combo is indexed."""
        index = build_suffix_index(["/src/app/models.py"])
        assert "app/models" in index
        assert index["app/models"] == ["/src/app/models.py"]

    def test_grandparent_stem_lookup(self) -> None:
        """grandparent/parent/stem combo is indexed."""
        index = build_suffix_index(["/a/b/c/file.py"])
        assert "b/c/file" in index

    def test_multiple_files_same_stem(self) -> None:
        """Multiple files with the same stem are all indexed."""
        index = build_suffix_index(["/src/models.py", "/lib/models.py"])
        assert len(index["models"]) == 2

    def test_empty_input(self) -> None:
        """Empty file list produces empty index."""
        index = build_suffix_index([])
        assert index == {}

    def test_no_duplicates(self) -> None:
        """Same path added twice does not duplicate."""
        index = build_suffix_index(["/src/foo.py", "/src/foo.py"])
        assert len(index["foo"]) == 1


# --- ResolutionCache ---


class TestResolutionCache:
    """Tests for ResolutionCache LRU+FIFO behavior."""

    def test_put_and_get(self) -> None:
        """Basic put/get round-trip."""
        cache = ResolutionCache(max_size=10)
        cache.put("key1", "/path/to/file.py")
        hit, value = cache.get("key1")
        assert hit is True
        assert value == "/path/to/file.py"

    def test_miss_returns_false(self) -> None:
        """Missing key returns (False, None)."""
        cache = ResolutionCache(max_size=10)
        hit, value = cache.get("missing")
        assert hit is False
        assert value is None

    def test_none_value_is_cached(self) -> None:
        """None values are cached (negative caching)."""
        cache = ResolutionCache(max_size=10)
        cache.put("unresolved", None)
        hit, value = cache.get("unresolved")
        assert hit is True
        assert value is None

    def test_eviction_at_capacity(self) -> None:
        """Oldest 20% are evicted when cache is full."""
        cache = ResolutionCache(max_size=10)
        for i in range(10):
            cache.put(f"key{i}", f"val{i}")
        assert cache.size == 10

        cache.put("new_key", "new_val")
        # After eviction of 20% (2 items), size should be 9
        assert cache.size == 9

        # Oldest entries (key0, key1) should be evicted
        hit0, _ = cache.get("key0")
        hit1, _ = cache.get("key1")
        assert hit0 is False
        assert hit1 is False

        # Newer entries should still be present
        hit9, val9 = cache.get("key9")
        assert hit9 is True
        assert val9 == "val9"

    def test_update_existing_key(self) -> None:
        """Updating an existing key does not increase size."""
        cache = ResolutionCache(max_size=10)
        cache.put("key", "old")
        cache.put("key", "new")
        assert cache.size == 1
        _, value = cache.get("key")
        assert value == "new"


# --- StandardResolver ---


class TestStandardResolver:
    """Tests for StandardResolver with Python-like imports."""

    def test_python_dotted_import(self) -> None:
        """Dotted Python import resolves via suffix index."""
        index = build_suffix_index(["/src/utils.py"])
        resolver = StandardResolver(suffix_index=index)
        result = resolver.resolve("utils", "/src/main.py")
        assert result == "/src/utils.py"

    def test_python_package_import(self) -> None:
        """Package.module import resolves via parent/stem."""
        index = build_suffix_index(["/src/pkg/helpers.py"])
        resolver = StandardResolver(suffix_index=index)
        result = resolver.resolve("pkg.helpers", "/src/main.py")
        assert result == "/src/pkg/helpers.py"

    def test_typescript_relative_import(self) -> None:
        """TypeScript relative import with ./."""
        index = build_suffix_index(["/src/components/Button.tsx"])
        resolver = StandardResolver(suffix_index=index)
        result = resolver.resolve("./Button", "/src/components/App.tsx")
        assert result == "/src/components/Button.tsx"

    def test_cache_hit(self) -> None:
        """Second resolve of same import uses cache."""
        index = build_suffix_index(["/src/utils.py"])
        resolver = StandardResolver(suffix_index=index)
        first = resolver.resolve("utils", "/src/main.py")
        second = resolver.resolve("utils", "/src/main.py")
        assert first == second

    def test_unresolvable_returns_none(self) -> None:
        """Unresolvable import returns None."""
        index = build_suffix_index(["/src/utils.py"])
        resolver = StandardResolver(suffix_index=index)
        result = resolver.resolve("nonexistent", "/src/main.py")
        assert result is None


# --- Go resolver ---


class TestGoResolver:
    """Tests for Go module path stripping."""

    def test_strip_module_prefix(self) -> None:
        """Module prefix is stripped, local path resolved."""
        index = build_suffix_index(["/src/pkg/handler.go"])
        resolver = GoResolver(
            suffix_index=index,
            module_prefix="github.com/org/repo",
        )
        result = resolver.resolve("github.com/org/repo/pkg/handler", "")
        assert result == "/src/pkg/handler.go"

    def test_non_local_import_returns_none(self) -> None:
        """External import (different module) returns None."""
        index = build_suffix_index(["/src/main.go"])
        resolver = GoResolver(
            suffix_index=index,
            module_prefix="github.com/org/repo",
        )
        result = resolver.resolve("github.com/other/lib", "")
        assert result is None

    def test_no_module_prefix(self) -> None:
        """Without module prefix, import path is used directly."""
        index = build_suffix_index(["/src/internal/service.go"])
        resolver = GoResolver(suffix_index=index, module_prefix="")
        result = resolver.resolve("internal/service", "")
        assert result == "/src/internal/service.go"


# --- Ruby resolver ---


class TestRubyResolver:
    """Tests for Ruby require/require_relative."""

    def test_require_relative(self) -> None:
        """require_relative with ./ prefix resolves."""
        index = build_suffix_index(["/app/lib/helper.rb"])
        resolver = RubyResolver(suffix_index=index)
        result = resolver.resolve("./helper", "/app/lib/main.rb")
        assert result == "/app/lib/helper.rb"

    def test_stdlib_skipped(self) -> None:
        """Standard library modules return None."""
        index = build_suffix_index(["/app/json.rb"])
        resolver = RubyResolver(suffix_index=index)
        result = resolver.resolve("json", "/app/main.rb")
        assert result is None

    def test_absolute_require(self) -> None:
        """Non-stdlib absolute require resolves."""
        index = build_suffix_index(["/app/models/user.rb"])
        resolver = RubyResolver(suffix_index=index)
        result = resolver.resolve("models/user", "/app/main.rb")
        assert result == "/app/models/user.rb"


# --- Rust resolver ---


class TestRustResolver:
    """Tests for Rust crate/super/self resolution."""

    def test_crate_prefix(self) -> None:
        """crate:: prefix resolves from crate root."""
        index = build_suffix_index(["/src/handlers.rs"])
        resolver = RustResolver(suffix_index=index, crate_root="/src")
        result = resolver.resolve("crate::handlers", "/src/main.rs")
        assert result == "/src/handlers.rs"

    def test_super_prefix(self) -> None:
        """super:: prefix resolves from parent directory."""
        index = build_suffix_index(["/src/sibling.rs"])
        resolver = RustResolver(suffix_index=index, crate_root="/src")
        result = resolver.resolve("super::sibling", "/src/sub/child.rs")
        assert result == "/src/sibling.rs"

    def test_self_prefix(self) -> None:
        """self:: prefix resolves from current directory."""
        index = build_suffix_index(["/src/sub/helper.rs"])
        resolver = RustResolver(suffix_index=index, crate_root="/src")
        result = resolver.resolve("self::helper", "/src/sub/mod.rs")
        assert result == "/src/sub/helper.rs"

    def test_nested_crate_path(self) -> None:
        """crate:: with nested modules resolves first segment."""
        index = build_suffix_index(["/src/db.rs"])
        resolver = RustResolver(suffix_index=index, crate_root="/src")
        result = resolver.resolve("crate::db::Connection", "/src/main.rs")
        assert result == "/src/db.rs"

    def test_unresolvable_crate_path(self) -> None:
        """Unresolvable crate path returns None."""
        index = build_suffix_index(["/src/main.rs"])
        resolver = RustResolver(suffix_index=index, crate_root="/src")
        result = resolver.resolve("crate::nonexistent", "/src/main.rs")
        assert result is None
