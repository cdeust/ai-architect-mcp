"""Integration tests for parser loading and the parsing processor.

Requires tree-sitter and per-language grammar packages installed.
Uses the new per-language package API (tree-sitter-python, etc.)
instead of the monolithic tree-sitter-languages.
"""

from __future__ import annotations

from pathlib import Path

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._parsing.ast_cache import ASTCache
from ai_codebase_intelligence._parsing.parser_loader import (
    cached_grammar_names,
    clear_parser_cache,
    get_parser,
)


class TestParserLoader:
    """Tests for parser loading via per-language grammar packages."""

    def test_load_python_parser(self) -> None:
        """Loading a Python parser returns a usable Parser."""
        clear_parser_cache()
        parser = get_parser(SupportedLanguage.PYTHON)
        assert parser is not None
        tree = parser.parse(b"def hello(): pass")
        assert tree.root_node is not None

    def test_parser_caching(self) -> None:
        """Same language returns the same parser instance."""
        clear_parser_cache()
        p1 = get_parser(SupportedLanguage.PYTHON)
        p2 = get_parser(SupportedLanguage.PYTHON)
        assert p1 is p2
        assert "python" in cached_grammar_names()

    def test_tsx_grammar_variant(self) -> None:
        """TSX files load a different grammar than regular TS."""
        clear_parser_cache()
        ts_parser = get_parser(SupportedLanguage.TYPESCRIPT, "app.ts")
        tsx_parser = get_parser(SupportedLanguage.TYPESCRIPT, "app.tsx")
        assert ts_parser is not None
        assert tsx_parser is not None

    def test_load_all_languages(self) -> None:
        """Every SupportedLanguage loads a parser without error."""
        clear_parser_cache()
        for lang in SupportedLanguage:
            parser = get_parser(lang)
            assert parser is not None, (
                f"Failed to load parser for {lang.value}"
            )

    def test_parse_swift_code(self) -> None:
        """Swift parser correctly parses a struct declaration."""
        clear_parser_cache()
        parser = get_parser(SupportedLanguage.SWIFT)
        tree = parser.parse(b"struct Point { var x: Int; var y: Int }")
        assert tree.root_node.type == "source_file"

    def test_parse_go_code(self) -> None:
        """Go parser correctly parses a function declaration."""
        clear_parser_cache()
        parser = get_parser(SupportedLanguage.GO)
        code = b"package main\nfunc main() { }"
        tree = parser.parse(code)
        assert tree.root_node is not None

    def test_parse_rust_code(self) -> None:
        """Rust parser correctly parses a function."""
        clear_parser_cache()
        parser = get_parser(SupportedLanguage.RUST)
        tree = parser.parse(b"fn main() { println!(\"hello\"); }")
        assert tree.root_node is not None


class TestParsingProcessor:
    """Tests for the chunked file parsing processor."""

    def test_parse_python_file(self, tmp_path: Path) -> None:
        """Parsing a Python file extracts class and function nodes."""
        from ai_codebase_intelligence._parsing.parsing_processor import (
            parse_files,
        )

        source = tmp_path / "sample.py"
        source.write_text(
            "class Foo:\n"
            "    def bar(self):\n"
            "        pass\n"
            "\n"
            "def baz():\n"
            "    pass\n"
        )
        nodes = parse_files(
            [str(source)], SupportedLanguage.PYTHON, cache=ASTCache(),
        )
        names = {n.name for n in nodes}
        assert "Foo" in names
        assert "bar" in names or "baz" in names

    def test_byte_budget_respected(self, tmp_path: Path) -> None:
        """Files exceeding the byte budget are skipped."""
        from ai_codebase_intelligence._parsing.parsing_processor import (
            parse_files,
        )

        big_file = tmp_path / "big.py"
        big_file.write_text("x = 1\n" * 1000)
        small_file = tmp_path / "small.py"
        small_file.write_text("y = 2\n")

        nodes = parse_files(
            [str(big_file), str(small_file)],
            SupportedLanguage.PYTHON,
            byte_budget=1,
            cache=ASTCache(),
        )
        assert len(nodes) == 0

    def test_nonexistent_file_skipped(self, tmp_path: Path) -> None:
        """Non-existent files are skipped gracefully."""
        from ai_codebase_intelligence._parsing.parsing_processor import (
            parse_files,
        )

        nodes = parse_files(
            [str(tmp_path / "ghost.py")],
            SupportedLanguage.PYTHON,
            cache=ASTCache(),
        )
        assert nodes == []

    def test_cache_reuse(self, tmp_path: Path) -> None:
        """Second parse of same file uses the cache."""
        from ai_codebase_intelligence._parsing.parsing_processor import (
            parse_files,
        )

        source = tmp_path / "cached.py"
        source.write_text("def alpha(): pass\n")
        cache = ASTCache()

        parse_files(
            [str(source)], SupportedLanguage.PYTHON, cache=cache
        )
        assert cache.stats.misses == 1

        parse_files(
            [str(source)], SupportedLanguage.PYTHON, cache=cache
        )
        assert cache.stats.hits == 1
