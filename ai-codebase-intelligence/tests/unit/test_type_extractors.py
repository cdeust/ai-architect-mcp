"""Tests for type extraction across all supported languages."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.type_extractors import get_type_extractor
from ai_codebase_intelligence._extraction.type_extractors.shared import (
    extract_generic_type_args,
    extract_simple_type_name,
    strip_nullable,
)

# ── Shared utilities ─────────────────────────────────────────────────────


class TestExtractSimpleTypeName:
    """Tests for extract_simple_type_name."""

    def test_dot_namespace(self) -> None:
        assert extract_simple_type_name("java.util.List") == "List"

    def test_cpp_namespace(self) -> None:
        assert extract_simple_type_name("std::vector") == "vector"

    def test_no_namespace(self) -> None:
        assert extract_simple_type_name("String") == "String"


class TestStripNullable:
    """Tests for strip_nullable."""

    def test_optional_wrapper(self) -> None:
        inner, opt = strip_nullable("Optional[int]")
        assert inner == "int"
        assert opt is True

    def test_trailing_question(self) -> None:
        inner, opt = strip_nullable("String?")
        assert inner == "String"
        assert opt is True

    def test_leading_question(self) -> None:
        inner, opt = strip_nullable("?string")
        assert inner == "string"
        assert opt is True

    def test_not_nullable(self) -> None:
        inner, opt = strip_nullable("int")
        assert inner == "int"
        assert opt is False


class TestExtractGenericArgs:
    """Tests for extract_generic_type_args."""

    def test_square_brackets(self) -> None:
        assert extract_generic_type_args("Dict[str, int]") == ["str", "int"]

    def test_angle_brackets(self) -> None:
        assert extract_generic_type_args("Map<K, V>") == ["K", "V"]

    def test_no_generics(self) -> None:
        assert extract_generic_type_args("int") == []

    def test_nested_generics(self) -> None:
        result = extract_generic_type_args("Map<String, List<Int>>")
        assert result == ["String", "List<Int>"]


# ── Python extractor ─────────────────────────────────────────────────────


class TestPythonExtractor:
    """Tests for the Python type extractor."""

    extract = staticmethod(get_type_extractor(SupportedLanguage.PYTHON))

    def test_optional(self) -> None:
        info = self.extract("Optional[int]")
        assert info.base == "int"
        assert info.is_optional is True

    def test_union_none(self) -> None:
        info = self.extract("Union[str, None]")
        assert info.base == "str"
        assert info.is_optional is True

    def test_pipe_none(self) -> None:
        info = self.extract("str | None")
        assert info.base == "str"
        assert info.is_optional is True

    def test_list(self) -> None:
        info = self.extract("list[str]")
        assert info.base == "list"
        assert info.generic_args == ["str"]
        assert info.is_array is True

    def test_dict(self) -> None:
        info = self.extract("Dict[str, int]")
        assert info.base == "Dict"
        assert info.generic_args == ["str", "int"]

    def test_simple(self) -> None:
        info = self.extract("int")
        assert info.base == "int"
        assert info.is_optional is False


# ── TypeScript extractor ─────────────────────────────────────────────────


class TestTypescriptExtractor:
    """Tests for the TypeScript type extractor."""

    extract = staticmethod(get_type_extractor(SupportedLanguage.TYPESCRIPT))

    def test_array_generic(self) -> None:
        info = self.extract("Array<string>")
        assert info.base == "Array"
        assert info.generic_args == ["string"]
        assert info.is_array is True

    def test_union_null(self) -> None:
        info = self.extract("string | null")
        assert info.base == "string"
        assert info.is_optional is True

    def test_union_undefined(self) -> None:
        info = self.extract("number | undefined")
        assert info.base == "number"
        assert info.is_optional is True

    def test_promise(self) -> None:
        info = self.extract("Promise<void>")
        assert info.base == "Promise"
        assert info.generic_args == ["void"]

    def test_array_suffix(self) -> None:
        info = self.extract("number[]")
        assert info.base == "Array"
        assert info.is_array is True
        assert info.generic_args == ["number"]


# ── Swift extractor ──────────────────────────────────────────────────────


class TestSwiftExtractor:
    """Tests for the Swift type extractor."""

    extract = staticmethod(get_type_extractor(SupportedLanguage.SWIFT))

    def test_optional(self) -> None:
        info = self.extract("String?")
        assert info.base == "String"
        assert info.is_optional is True

    def test_array_literal(self) -> None:
        info = self.extract("[Int]")
        assert info.base == "Array"
        assert info.generic_args == ["Int"]
        assert info.is_array is True

    def test_dictionary_generic(self) -> None:
        info = self.extract("Dictionary<String, Any>")
        assert info.base == "Dictionary"
        assert info.generic_args == ["String", "Any"]

    def test_dictionary_literal(self) -> None:
        info = self.extract("[String: Any]")
        assert info.base == "Dictionary"
        assert info.generic_args == ["String", "Any"]


# ── Go extractor ─────────────────────────────────────────────────────────


class TestGoExtractor:
    """Tests for the Go type extractor."""

    extract = staticmethod(get_type_extractor(SupportedLanguage.GO))

    def test_slice(self) -> None:
        info = self.extract("[]string")
        assert info.base == "string"
        assert info.is_array is True

    def test_pointer(self) -> None:
        info = self.extract("*http.Request")
        assert info.base == "Request"
        assert info.is_optional is True

    def test_map(self) -> None:
        info = self.extract("map[string]int")
        assert info.base == "map"
        assert info.generic_args == ["string", "int"]

    def test_simple(self) -> None:
        info = self.extract("int")
        assert info.base == "int"


# ── Rust extractor ───────────────────────────────────────────────────────


class TestRustExtractor:
    """Tests for the Rust type extractor."""

    extract = staticmethod(get_type_extractor(SupportedLanguage.RUST))

    def test_option(self) -> None:
        info = self.extract("Option<String>")
        assert info.base == "String"
        assert info.is_optional is True

    def test_vec(self) -> None:
        info = self.extract("Vec<u32>")
        assert info.base == "Vec"
        assert info.generic_args == ["u32"]
        assert info.is_array is True

    def test_result(self) -> None:
        info = self.extract("Result<T, E>")
        assert info.base == "Result"
        assert info.generic_args == ["T", "E"]

    def test_simple(self) -> None:
        info = self.extract("i32")
        assert info.base == "i32"


# ── JVM (Java / Kotlin) extractor ───────────────────────────────────────


class TestJvmExtractor:
    """Tests for the Java/Kotlin type extractor."""

    extract = staticmethod(get_type_extractor(SupportedLanguage.JAVA))

    def test_list(self) -> None:
        info = self.extract("List<String>")
        assert info.base == "List"
        assert info.generic_args == ["String"]
        assert info.is_array is True

    def test_map(self) -> None:
        info = self.extract("Map<String, Integer>")
        assert info.base == "Map"
        assert info.generic_args == ["String", "Integer"]

    def test_kotlin_nullable(self) -> None:
        kt = get_type_extractor(SupportedLanguage.KOTLIN)
        info = kt("String?")
        assert info.base == "String"
        assert info.is_optional is True

    def test_qualified(self) -> None:
        info = self.extract("java.util.List<String>")
        assert info.base == "List"
        assert info.generic_args == ["String"]


# ── Registry dispatch ────────────────────────────────────────────────────


class TestRegistry:
    """Tests for the language-to-extractor registry."""

    @pytest.mark.parametrize(
        "language",
        list(SupportedLanguage),
    )
    def test_all_languages_have_extractors(
        self, language: SupportedLanguage
    ) -> None:
        extractor = get_type_extractor(language)
        assert callable(extractor)

    def test_javascript_uses_typescript(self) -> None:
        ts = get_type_extractor(SupportedLanguage.TYPESCRIPT)
        js = get_type_extractor(SupportedLanguage.JAVASCRIPT)
        assert ts is js

    def test_c_and_cpp_share_extractor(self) -> None:
        c = get_type_extractor(SupportedLanguage.C)
        cpp = get_type_extractor(SupportedLanguage.CPP)
        assert c is cpp
