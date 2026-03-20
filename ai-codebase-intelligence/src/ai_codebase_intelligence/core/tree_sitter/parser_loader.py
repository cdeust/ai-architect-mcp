"""tree-sitter parser loader — uses tree-sitter 0.23 API.

0.23 has working Query.matches()/captures(). 0.25 removed them.
API: Parser() + parser.language = Language(ptr)
"""
from __future__ import annotations

import importlib

import tree_sitter

from ...config.supported_languages import SupportedLanguages

# Cache: language key -> (Parser, Language)
_cache: dict[str, tuple[tree_sitter.Parser, tree_sitter.Language]] = {}

_GRAMMAR_MODULES: dict[str, str] = {
    SupportedLanguages.JavaScript: "tree_sitter_javascript",
    SupportedLanguages.TypeScript: "tree_sitter_typescript",
    "typescript:tsx": "tree_sitter_typescript",
    SupportedLanguages.Python: "tree_sitter_python",
    SupportedLanguages.Java: "tree_sitter_java",
    SupportedLanguages.C: "tree_sitter_c",
    SupportedLanguages.CPlusPlus: "tree_sitter_cpp",
    SupportedLanguages.CSharp: "tree_sitter_c_sharp",
    SupportedLanguages.Go: "tree_sitter_go",
    SupportedLanguages.Rust: "tree_sitter_rust",
    SupportedLanguages.Kotlin: "tree_sitter_kotlin",
    SupportedLanguages.PHP: "tree_sitter_php",
    SupportedLanguages.Swift: "tree_sitter_swift",
}

_GRAMMAR_ATTR: dict[str, str] = {
    SupportedLanguages.TypeScript: "language_typescript",
    "typescript:tsx": "language_tsx",
    SupportedLanguages.PHP: "language_php",
}


def is_language_available(language: str) -> bool:
    return language in _GRAMMAR_MODULES


def load_language(language: str, file_path: str = "") -> tree_sitter.Parser:
    key = (
        f"{language}:tsx"
        if language == SupportedLanguages.TypeScript and file_path.endswith(".tsx")
        else language
    )

    if key in _cache:
        return _cache[key][0]

    module_name = _GRAMMAR_MODULES.get(key)
    if module_name is None:
        raise ValueError(f"Unsupported language: {language}")

    mod = importlib.import_module(module_name)
    attr_name = _GRAMMAR_ATTR.get(key, "language")
    lang_fn = getattr(mod, attr_name)
    lang = tree_sitter.Language(lang_fn())

    parser = tree_sitter.Parser()
    parser.language = lang

    _cache[key] = (parser, lang)
    return parser
