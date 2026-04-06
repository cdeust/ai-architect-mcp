"""Tree-sitter parser loader with caching.

Provides a simple interface to obtain tree-sitter parsers for
supported languages. Parsers are cached by (language, grammar)
key to avoid repeated initialization.
"""

from __future__ import annotations

import importlib
from typing import Any

import tree_sitter

from ai_codebase_intelligence._config.supported_languages import (
    SupportedLanguage,
    get_grammar_name,
)

_parser_cache: dict[str, Any] = {}

_GRAMMAR_MODULES: dict[str, str] = {
    "python": "tree_sitter_python",
    "typescript": "tree_sitter_typescript",
    "tsx": "tree_sitter_typescript",
    "javascript": "tree_sitter_javascript",
    "java": "tree_sitter_java",
    "c": "tree_sitter_c",
    "cpp": "tree_sitter_cpp",
    "c_sharp": "tree_sitter_c_sharp",
    "go": "tree_sitter_go",
    "rust": "tree_sitter_rust",
    "php": "tree_sitter_php",
    "kotlin": "tree_sitter_kotlin",
    "swift": "tree_sitter_swift",
    "ruby": "tree_sitter_ruby",
}

_GRAMMAR_ATTR: dict[str, str] = {
    "typescript": "language_typescript",
    "tsx": "language_tsx",
}


def _load_language(grammar_name: str) -> tree_sitter.Language:
    """Load a tree-sitter Language object for the given grammar.

    Args:
        grammar_name: The tree-sitter grammar name (e.g. "python").

    Returns:
        A tree_sitter.Language instance.

    Raises:
        ImportError: If the grammar module is not installed.
    """
    module_name = _GRAMMAR_MODULES.get(grammar_name, f"tree_sitter_{grammar_name}")
    mod = importlib.import_module(module_name)
    attr = _GRAMMAR_ATTR.get(grammar_name, "language")
    lang_fn = getattr(mod, attr)
    return tree_sitter.Language(lang_fn())


def get_parser(
    language: SupportedLanguage,
    file_path: str = "",
) -> tree_sitter.Parser:
    """Get a tree-sitter parser for the given language.

    Parsers are cached by grammar name. Calling with the same
    language returns the same parser instance.

    Args:
        language: The target programming language.
        file_path: Optional file path for grammar selection
            (e.g., TSX vs TypeScript).

    Returns:
        A configured tree_sitter.Parser.

    Raises:
        ImportError: If the grammar package is not installed.
    """
    grammar_name = get_grammar_name(language, file_path)
    if grammar_name in _parser_cache:
        return _parser_cache[grammar_name]

    lang = _load_language(grammar_name)
    parser = tree_sitter.Parser(lang)
    _parser_cache[grammar_name] = parser
    return parser


def clear_parser_cache() -> None:
    """Remove all cached parsers.

    Useful in tests to ensure a clean state between test methods.
    """
    _parser_cache.clear()
