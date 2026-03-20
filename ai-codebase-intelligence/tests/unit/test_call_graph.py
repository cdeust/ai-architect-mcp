"""Tests for call graph extraction (Epic 6)."""

from __future__ import annotations

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.call_routing import (
    CallForm,
    CallInfo,
    classify_call,
)
from ai_codebase_intelligence._extraction.export_detection import is_exported


class TestCallClassification:
    """Tests for call form classification."""

    def test_free_function(self) -> None:
        result = classify_call("print", "", SupportedLanguage.PYTHON)
        assert result == CallForm.FREE

    def test_member_call(self) -> None:
        result = classify_call("process", "self", SupportedLanguage.PYTHON)
        assert result == CallForm.MEMBER

    def test_static_call(self) -> None:
        result = classify_call("create", "Factory", SupportedLanguage.JAVA)
        assert result == CallForm.STATIC

    def test_super_call(self) -> None:
        result = classify_call("init", "super", SupportedLanguage.SWIFT)
        assert result == CallForm.SUPER

    def test_swift_constructor(self) -> None:
        result = classify_call("MyClass", "", SupportedLanguage.SWIFT)
        assert result == CallForm.CONSTRUCTOR

    def test_python_init(self) -> None:
        result = classify_call("__init__", "", SupportedLanguage.PYTHON)
        assert result == CallForm.CONSTRUCTOR

    def test_ruby_member_call(self) -> None:
        result = classify_call("method", "obj", SupportedLanguage.RUBY)
        assert result == CallForm.MEMBER


class TestExportDetection:
    """Tests for per-language export checking."""

    def test_python_public(self) -> None:
        assert is_exported("my_func", SupportedLanguage.PYTHON) is True

    def test_python_private(self) -> None:
        assert is_exported("_internal", SupportedLanguage.PYTHON) is False

    def test_python_dunder(self) -> None:
        assert is_exported("__init__", SupportedLanguage.PYTHON) is False

    def test_go_uppercase(self) -> None:
        assert is_exported("ProcessData", SupportedLanguage.GO) is True

    def test_go_lowercase(self) -> None:
        assert is_exported("processData", SupportedLanguage.GO) is False

    def test_swift_public(self) -> None:
        assert is_exported("func", SupportedLanguage.SWIFT, ["public"]) is True

    def test_swift_private(self) -> None:
        assert is_exported("func", SupportedLanguage.SWIFT, ["private"]) is False

    def test_swift_default_internal(self) -> None:
        assert is_exported("func", SupportedLanguage.SWIFT) is False

    def test_kotlin_default_public(self) -> None:
        assert is_exported("func", SupportedLanguage.KOTLIN) is True

    def test_kotlin_private(self) -> None:
        assert is_exported("func", SupportedLanguage.KOTLIN, ["private"]) is False

    def test_rust_pub(self) -> None:
        assert is_exported("func", SupportedLanguage.RUST, ["pub"]) is True

    def test_rust_no_pub(self) -> None:
        assert is_exported("func", SupportedLanguage.RUST) is False

    def test_explicit_export_keyword(self) -> None:
        assert is_exported(
            "func", SupportedLanguage.TYPESCRIPT, has_export_keyword=True
        ) is True

    def test_ts_no_export(self) -> None:
        assert is_exported("func", SupportedLanguage.TYPESCRIPT) is False
