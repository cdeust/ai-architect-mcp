from __future__ import annotations

from ...config.supported_languages import SupportedLanguages
from .tree_sitter_queries import (
    TYPESCRIPT_QUERIES,
    JAVASCRIPT_QUERIES,
    PYTHON_QUERIES,
    JAVA_QUERIES,
    C_QUERIES,
    GO_QUERIES,
)
from .tree_sitter_queries_ext import (
    CPP_QUERIES,
    CSHARP_QUERIES,
    RUST_QUERIES,
    PHP_QUERIES,
    KOTLIN_QUERIES,
    SWIFT_QUERIES,
)

LANGUAGE_QUERIES: dict[str, str] = {
    SupportedLanguages.TypeScript: TYPESCRIPT_QUERIES,
    SupportedLanguages.JavaScript: JAVASCRIPT_QUERIES,
    SupportedLanguages.Python: PYTHON_QUERIES,
    SupportedLanguages.Java: JAVA_QUERIES,
    SupportedLanguages.C: C_QUERIES,
    SupportedLanguages.Go: GO_QUERIES,
    SupportedLanguages.CPlusPlus: CPP_QUERIES,
    SupportedLanguages.CSharp: CSHARP_QUERIES,
    SupportedLanguages.Rust: RUST_QUERIES,
    SupportedLanguages.PHP: PHP_QUERIES,
    SupportedLanguages.Kotlin: KOTLIN_QUERIES,
    SupportedLanguages.Swift: SWIFT_QUERIES,
}
