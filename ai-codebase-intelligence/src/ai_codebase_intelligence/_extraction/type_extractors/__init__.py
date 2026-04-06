"""Language-specific type extractors.

Each extractor is a callable that takes a type annotation string and
returns a TypeInfo describing its structure (base type, generics,
nullability, array-ness).
"""

from __future__ import annotations

from typing import Callable

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage
from ai_codebase_intelligence._extraction.type_extractors.extractors import (
    c_cpp_extractor,
    go_extractor,
    jvm_extractor,
    python_extractor,
    rust_extractor,
    swift_extractor,
    typescript_extractor,
)
from ai_codebase_intelligence._extraction.type_extractors.type_info import TypeInfo

TypeExtractor = Callable[[str], "TypeInfo"]

_REGISTRY: dict[SupportedLanguage, TypeExtractor] = {
    SupportedLanguage.PYTHON: python_extractor,
    SupportedLanguage.TYPESCRIPT: typescript_extractor,
    SupportedLanguage.JAVASCRIPT: typescript_extractor,
    SupportedLanguage.JAVA: jvm_extractor,
    SupportedLanguage.KOTLIN: jvm_extractor,
    SupportedLanguage.SWIFT: swift_extractor,
    SupportedLanguage.GO: go_extractor,
    SupportedLanguage.RUST: rust_extractor,
    SupportedLanguage.C: c_cpp_extractor,
    SupportedLanguage.CPP: c_cpp_extractor,
    SupportedLanguage.CSHARP: jvm_extractor,
    SupportedLanguage.PHP: jvm_extractor,
    SupportedLanguage.RUBY: python_extractor,
}


def get_type_extractor(language: SupportedLanguage) -> TypeExtractor:
    """Get the type extractor for a given language.

    Args:
        language: The target programming language.

    Returns:
        A callable that takes a type string and returns TypeInfo.

    Raises:
        KeyError: If no extractor is registered for the language.
    """
    return _REGISTRY[language]


__all__ = [
    "TypeExtractor",
    "TypeInfo",
    "get_type_extractor",
]
