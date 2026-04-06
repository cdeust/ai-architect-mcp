from __future__ import annotations

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage

_EXPORT_KEYWORD_LANGUAGES = frozenset({
    SupportedLanguage.TYPESCRIPT,
    SupportedLanguage.JAVASCRIPT,
})

_PUBLIC_BY_DEFAULT_LANGUAGES = frozenset({
    SupportedLanguage.KOTLIN,
    SupportedLanguage.RUBY,
    SupportedLanguage.JAVA,
    SupportedLanguage.C,
    SupportedLanguage.CPP,
    SupportedLanguage.CSHARP,
    SupportedLanguage.PHP,
})


def is_exported(
    name: str,
    language: SupportedLanguage,
    modifiers: list[str] | None = None,
    *,
    has_export_keyword: bool = False,
) -> bool:
    """Determine whether a symbol is exported/public in its language.

    Args:
        name: The symbol name.
        language: The source language.
        modifiers: Access modifiers present on the declaration
            (e.g. ["public"], ["private"], ["pub"]).
        has_export_keyword: Whether an explicit export keyword was found
            (relevant for TypeScript/JavaScript).

    Returns:
        True if the symbol is considered exported/public.
    """
    mods = modifiers or []

    if language == SupportedLanguage.PYTHON:
        return not name.startswith("_")

    if language == SupportedLanguage.GO:
        return len(name) > 0 and name[0].isupper()

    if language == SupportedLanguage.SWIFT:
        return "public" in mods

    if language == SupportedLanguage.RUST:
        return "pub" in mods

    if language in _EXPORT_KEYWORD_LANGUAGES:
        return has_export_keyword

    if language in _PUBLIC_BY_DEFAULT_LANGUAGES:
        if "private" in mods:
            return False
        if language == SupportedLanguage.CSHARP and "internal" in mods:
            return False
        return True

    return True
