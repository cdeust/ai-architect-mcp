"""Import statement extraction from tree-sitter ASTs.

Extracts import statements for Python, TypeScript/JavaScript, and
Go from their respective AST node types.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_codebase_intelligence._config.supported_languages import SupportedLanguage


@dataclass(frozen=True, slots=True)
class ImportInfo:
    """A single import statement extracted from source code.

    Args:
        source_module: The module or package being imported.
        imported_names: Specific names imported (empty for bare imports).
        is_wildcard: Whether this is a wildcard/star import.
        file_path: The source file containing the import.
        line: 1-based line number of the import statement.
    """

    source_module: str
    imported_names: list[str] = field(default_factory=list)
    is_wildcard: bool = False
    file_path: str = ""
    line: int = 0


def extract_imports_from_tree(
    root_node: object,
    file_path: str,
    language: SupportedLanguage,
) -> list[ImportInfo]:
    """Extract all import statements from a tree-sitter AST.

    Args:
        root_node: The root tree-sitter node.
        file_path: Path to the source file.
        language: The source language.

    Returns:
        A list of ImportInfo records.
    """
    results: list[ImportInfo] = []
    _walk_imports(root_node, file_path, language, results)
    return results


def _walk_imports(
    node: object,
    file_path: str,
    language: SupportedLanguage,
    out: list[ImportInfo],
) -> None:
    """Recursively walk AST collecting import nodes.

    Args:
        node: Current tree-sitter node.
        file_path: Source file path.
        language: Source language.
        out: Accumulator for import records.
    """
    # Deferred import to avoid circular dependency at module level.
    from ai_codebase_intelligence._extraction.import_extractor_langs import (
        extract_go_import,
        extract_python_from_import,
        extract_python_import,
        extract_ts_import,
    )

    node_type = node.type  # type: ignore[union-attr]

    if language == SupportedLanguage.PYTHON:
        if node_type == "import_statement":
            extract_python_import(node, file_path, out)
            return
        if node_type == "import_from_statement":
            extract_python_from_import(node, file_path, out)
            return

    if language in (SupportedLanguage.TYPESCRIPT, SupportedLanguage.JAVASCRIPT):
        if node_type == "import_statement":
            extract_ts_import(node, file_path, out)
            return

    if language == SupportedLanguage.GO:
        if node_type == "import_declaration":
            extract_go_import(node, file_path, out)
            return

    for child in node.named_children:  # type: ignore[union-attr]
        _walk_imports(child, file_path, language, out)
