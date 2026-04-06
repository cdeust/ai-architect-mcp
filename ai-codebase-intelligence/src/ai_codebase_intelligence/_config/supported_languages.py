from __future__ import annotations

import os
from enum import Enum


class SupportedLanguage(str, Enum):
    """Supported programming languages for codebase analysis."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    RUBY = "ruby"


GRAMMAR_NAMES: dict[SupportedLanguage, str] = {
    SupportedLanguage.PYTHON: "python",
    SupportedLanguage.TYPESCRIPT: "typescript",
    SupportedLanguage.JAVASCRIPT: "javascript",
    SupportedLanguage.JAVA: "java",
    SupportedLanguage.C: "c",
    SupportedLanguage.CPP: "cpp",
    SupportedLanguage.CSHARP: "c_sharp",
    SupportedLanguage.GO: "go",
    SupportedLanguage.RUST: "rust",
    SupportedLanguage.PHP: "php",
    SupportedLanguage.KOTLIN: "kotlin",
    SupportedLanguage.SWIFT: "swift",
    SupportedLanguage.RUBY: "ruby",
}

LANGUAGE_EXTENSIONS: dict[str, SupportedLanguage] = {
    ".py": SupportedLanguage.PYTHON,
    ".pyi": SupportedLanguage.PYTHON,
    ".ts": SupportedLanguage.TYPESCRIPT,
    ".tsx": SupportedLanguage.TYPESCRIPT,
    ".js": SupportedLanguage.JAVASCRIPT,
    ".jsx": SupportedLanguage.JAVASCRIPT,
    ".cjs": SupportedLanguage.JAVASCRIPT,
    ".mjs": SupportedLanguage.JAVASCRIPT,
    ".java": SupportedLanguage.JAVA,
    ".c": SupportedLanguage.C,
    ".h": SupportedLanguage.C,
    ".cpp": SupportedLanguage.CPP,
    ".cc": SupportedLanguage.CPP,
    ".cxx": SupportedLanguage.CPP,
    ".hpp": SupportedLanguage.CPP,
    ".hxx": SupportedLanguage.CPP,
    ".hh": SupportedLanguage.CPP,
    ".cs": SupportedLanguage.CSHARP,
    ".go": SupportedLanguage.GO,
    ".rs": SupportedLanguage.RUST,
    ".php": SupportedLanguage.PHP,
    ".phtml": SupportedLanguage.PHP,
    ".kt": SupportedLanguage.KOTLIN,
    ".kts": SupportedLanguage.KOTLIN,
    ".swift": SupportedLanguage.SWIFT,
    ".rb": SupportedLanguage.RUBY,
}


def detect_language(file_path: str) -> SupportedLanguage | None:
    """Detect the programming language from a file path.

    Args:
        file_path: Path or filename to detect language for.

    Returns:
        The detected language, or None if unsupported.
    """
    _, ext = os.path.splitext(file_path)
    if not ext:
        return None
    return LANGUAGE_EXTENSIONS.get(ext.lower())


def get_grammar_name(lang: SupportedLanguage, file_path: str = "") -> str:
    """Get the tree-sitter grammar name for a language.

    Args:
        lang: The supported language.
        file_path: Optional file path for context-sensitive grammar
            selection (e.g., TSX vs TypeScript).

    Returns:
        The tree-sitter grammar name string.
    """
    if lang == SupportedLanguage.TYPESCRIPT and file_path.endswith(".tsx"):
        return "tsx"
    return GRAMMAR_NAMES[lang]


__all__ = [
    "SupportedLanguage",
    "GRAMMAR_NAMES",
    "LANGUAGE_EXTENSIONS",
    "detect_language",
    "get_grammar_name",
]
