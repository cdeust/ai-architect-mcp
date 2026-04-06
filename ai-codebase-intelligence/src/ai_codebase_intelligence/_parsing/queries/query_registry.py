"""Tree-sitter query registry — maps languages to S-expression queries.

Wraps the legacy LANGUAGE_QUERIES data into the new SupportedLanguage
enum namespace. Each language maps to a dict of query-name to
S-expression string.
"""

from __future__ import annotations

from ai_codebase_intelligence._config.supported_languages import (
    SupportedLanguage,
)
from ai_codebase_intelligence.core.ingestion.tree_sitter_queries import (
    C_QUERIES,
    GO_QUERIES,
    JAVA_QUERIES,
    JAVASCRIPT_QUERIES,
    PYTHON_QUERIES,
    TYPESCRIPT_QUERIES,
)
from ai_codebase_intelligence.core.ingestion.tree_sitter_queries_ext import (
    CPP_QUERIES,
    CSHARP_QUERIES,
    KOTLIN_QUERIES,
    PHP_QUERIES,
    RUST_QUERIES,
    SWIFT_QUERIES,
)

_LANGUAGE_QUERY_MAP: dict[SupportedLanguage, str] = {
    SupportedLanguage.PYTHON: PYTHON_QUERIES,
    SupportedLanguage.TYPESCRIPT: TYPESCRIPT_QUERIES,
    SupportedLanguage.JAVASCRIPT: JAVASCRIPT_QUERIES,
    SupportedLanguage.JAVA: JAVA_QUERIES,
    SupportedLanguage.C: C_QUERIES,
    SupportedLanguage.CPP: CPP_QUERIES,
    SupportedLanguage.CSHARP: CSHARP_QUERIES,
    SupportedLanguage.GO: GO_QUERIES,
    SupportedLanguage.RUST: RUST_QUERIES,
    SupportedLanguage.PHP: PHP_QUERIES,
    SupportedLanguage.KOTLIN: KOTLIN_QUERIES,
    SupportedLanguage.SWIFT: SWIFT_QUERIES,
}


def _split_queries(combined: str) -> dict[str, str]:
    """Split a combined S-expression string into named sections.

    Each section is a top-level parenthesized pattern. If the pattern
    ends with ``@definition.class``, ``@definition.function``, etc., the
    key is derived from the capture name (e.g. ``class_definition``).

    For languages whose combined query string cannot be cleanly split,
    the fallback is ``{"combined": combined}``.

    Args:
        combined: Multi-pattern S-expression string.

    Returns:
        Dict mapping query names to individual S-expression strings.
    """
    sections: dict[str, str] = {}
    current_lines: list[str] = []
    current_name: str | None = None

    for raw_line in combined.strip().splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue

        if line.startswith("(") and not current_lines:
            current_lines.append(raw_line)
            continue

        if current_lines:
            current_lines.append(raw_line)

            if "@definition." in line or "@import" in line or "@call" in line or "@heritage" in line:
                tag = line.rsplit("@", 1)[-1].strip().rstrip(")")
                parts = tag.split(".")
                if len(parts) == 2:
                    current_name = f"{parts[1]}_{parts[0]}"
                else:
                    current_name = tag.replace(".", "_")

            open_count = sum(l.count("(") for l in current_lines)
            close_count = sum(l.count(")") for l in current_lines)
            if open_count > 0 and close_count >= open_count:
                block = "\n".join(current_lines).strip()
                name = current_name or f"query_{len(sections)}"
                base = name
                counter = 2
                while name in sections:
                    name = f"{base}_{counter}"
                    counter += 1
                sections[name] = block
                current_lines = []
                current_name = None

    if not sections:
        return {"combined": combined.strip()}
    return sections


def get_queries_for_language(language: SupportedLanguage) -> dict[str, str]:
    """Return tree-sitter queries for *language*.

    Args:
        language: A SupportedLanguage enum member.

    Returns:
        Dict mapping query names to S-expression query strings. Every
        value starts with ``(``.
    """
    if language == SupportedLanguage.RUBY:
        return _ruby_queries()
    combined = _LANGUAGE_QUERY_MAP.get(language)
    if combined is None:
        return {"combined": _default_query()}
    return _split_queries(combined)


def _ruby_queries() -> dict[str, str]:
    """Minimal Ruby queries — no legacy data available."""
    return {
        "class_definition": (
            "(class\n"
            "  name: (constant) @name) @definition.class"
        ),
        "method_definition": (
            "(method\n"
            "  name: (identifier) @name) @definition.function"
        ),
    }


def _default_query() -> str:
    return "(identifier) @name"
