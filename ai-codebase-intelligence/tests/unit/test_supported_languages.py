"""Tests for supported languages configuration."""

from __future__ import annotations

from ai_codebase_intelligence._config.supported_languages import (
    GRAMMAR_NAMES,
    LANGUAGE_EXTENSIONS,
    SupportedLanguage,
    detect_language,
    get_grammar_name,
)


class TestSupportedLanguage:
    """Tests for SupportedLanguage enum."""

    def test_has_13_languages(self) -> None:
        assert len(SupportedLanguage) == 13

    def test_all_languages_have_grammar(self) -> None:
        for lang in SupportedLanguage:
            assert lang in GRAMMAR_NAMES, f"Missing grammar for {lang}"


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_python(self) -> None:
        assert detect_language("main.py") == SupportedLanguage.PYTHON
        assert detect_language("types.pyi") == SupportedLanguage.PYTHON

    def test_typescript(self) -> None:
        assert detect_language("app.ts") == SupportedLanguage.TYPESCRIPT
        assert detect_language("App.tsx") == SupportedLanguage.TYPESCRIPT

    def test_swift(self) -> None:
        assert detect_language("ViewController.swift") == SupportedLanguage.SWIFT

    def test_go(self) -> None:
        assert detect_language("main.go") == SupportedLanguage.GO

    def test_rust(self) -> None:
        assert detect_language("lib.rs") == SupportedLanguage.RUST

    def test_cpp_variants(self) -> None:
        assert detect_language("main.cpp") == SupportedLanguage.CPP
        assert detect_language("util.cc") == SupportedLanguage.CPP
        assert detect_language("types.hpp") == SupportedLanguage.CPP

    def test_unsupported(self) -> None:
        assert detect_language("data.json") is None
        assert detect_language("README.md") is None
        assert detect_language("Makefile") is None


class TestGetGrammarName:
    """Tests for get_grammar_name function."""

    def test_standard_grammar(self) -> None:
        assert get_grammar_name(SupportedLanguage.PYTHON) == "python"
        assert get_grammar_name(SupportedLanguage.CSHARP) == "c_sharp"

    def test_tsx_detection(self) -> None:
        assert (
            get_grammar_name(SupportedLanguage.TYPESCRIPT, "App.tsx") == "tsx"
        )
        assert (
            get_grammar_name(SupportedLanguage.TYPESCRIPT, "app.ts") == "typescript"
        )
