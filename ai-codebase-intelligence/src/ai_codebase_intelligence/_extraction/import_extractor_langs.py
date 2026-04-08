"""Language-specific import extraction from tree-sitter ASTs.

Extraction functions for Python, TypeScript/JavaScript, and Go
import statements.
"""

from __future__ import annotations

from ai_codebase_intelligence._extraction.import_extractor import ImportInfo


def extract_python_import(
    node: object,
    file_path: str,
    out: list[ImportInfo],
) -> None:
    """Extract a Python ``import X`` statement.

    Args:
        node: A tree-sitter import_statement node.
        file_path: Source file path.
        out: Accumulator for import records.
    """
    line = node.start_point[0] + 1  # type: ignore[union-attr]
    for child in node.named_children:  # type: ignore[union-attr]
        if child.type in ("dotted_name", "aliased_import"):
            if child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                module_name = (
                    name_node.text.decode("utf-8", errors="replace")
                    if name_node
                    else child.text.decode("utf-8", errors="replace")
                )
            else:
                module_name = child.text.decode("utf-8", errors="replace")
            out.append(
                ImportInfo(
                    source_module=module_name,
                    imported_names=[],
                    is_wildcard=False,
                    file_path=file_path,
                    line=line,
                )
            )


def extract_python_from_import(
    node: object,
    file_path: str,
    out: list[ImportInfo],
) -> None:
    """Extract a Python ``from X import Y`` statement.

    Args:
        node: A tree-sitter import_from_statement node.
        file_path: Source file path.
        out: Accumulator for import records.
    """
    line = node.start_point[0] + 1  # type: ignore[union-attr]
    module_name = ""
    imported_names: list[str] = []
    is_wildcard = False

    module_node = node.child_by_field_name("module_name")  # type: ignore[union-attr]
    if module_node is not None:
        module_name = module_node.text.decode("utf-8", errors="replace")

    # Handle relative imports: look for "." or ".." tokens
    text = node.text.decode("utf-8", errors="replace")  # type: ignore[union-attr]
    if "from ." in text or "from .." in text:
        # Extract the dot prefix
        parts = text.split("import")[0].strip()
        # Remove "from " prefix
        if parts.startswith("from"):
            parts = parts[4:].strip()
        if module_name and not parts.startswith("."):
            pass
        elif parts.startswith("."):
            module_name = parts

    for child in node.named_children:  # type: ignore[union-attr]
        if child.type == "wildcard_import":
            is_wildcard = True
        elif child.type == "dotted_name" and child != module_node:
            imported_names.append(child.text.decode("utf-8", errors="replace"))
        elif child.type == "aliased_import":
            name_node = child.child_by_field_name("name")
            if name_node is not None:
                imported_names.append(name_node.text.decode("utf-8", errors="replace"))

    out.append(
        ImportInfo(
            source_module=module_name,
            imported_names=imported_names,
            is_wildcard=is_wildcard,
            file_path=file_path,
            line=line,
        )
    )


def extract_ts_import(
    node: object,
    file_path: str,
    out: list[ImportInfo],
) -> None:
    """Extract a TypeScript/JavaScript import statement.

    Args:
        node: A tree-sitter import_statement node.
        file_path: Source file path.
        out: Accumulator for import records.
    """
    line = node.start_point[0] + 1  # type: ignore[union-attr]
    source_module = ""
    imported_names: list[str] = []

    source_node = node.child_by_field_name("source")  # type: ignore[union-attr]
    if source_node is not None:
        raw = source_node.text.decode("utf-8", errors="replace")
        source_module = raw.strip("'\"")

    for child in node.named_children:  # type: ignore[union-attr]
        if child.type == "import_clause":
            _collect_ts_import_names(child, imported_names)
        elif child.type == "identifier":
            imported_names.append(child.text.decode("utf-8", errors="replace"))

    out.append(
        ImportInfo(
            source_module=source_module,
            imported_names=imported_names,
            is_wildcard=False,
            file_path=file_path,
            line=line,
        )
    )


def _collect_ts_import_names(
    node: object,
    names: list[str],
) -> None:
    """Collect imported names from a TS import clause.

    Args:
        node: A tree-sitter import_clause node.
        names: Accumulator for imported names.
    """
    for child in node.named_children:  # type: ignore[union-attr]
        if child.type == "identifier":
            names.append(child.text.decode("utf-8", errors="replace"))
        elif child.type == "named_imports":
            for spec in child.named_children:
                if spec.type == "import_specifier":
                    name_node = spec.child_by_field_name("name")
                    if name_node is not None:
                        names.append(name_node.text.decode("utf-8", errors="replace"))
                elif spec.type == "identifier":
                    names.append(spec.text.decode("utf-8", errors="replace"))
        elif child.type == "namespace_import":
            alias = child.child_by_field_name("alias")
            if alias:
                names.append(alias.text.decode("utf-8", errors="replace"))
        else:
            _collect_ts_import_names(child, names)


def extract_go_import(
    node: object,
    file_path: str,
    out: list[ImportInfo],
) -> None:
    """Extract Go import declarations.

    Args:
        node: A tree-sitter import_declaration node.
        file_path: Source file path.
        out: Accumulator for import records.
    """
    line = node.start_point[0] + 1  # type: ignore[union-attr]

    for child in node.named_children:  # type: ignore[union-attr]
        if child.type == "import_spec_list":
            for spec in child.named_children:
                _extract_go_import_spec(spec, file_path, out)
        elif child.type == "import_spec":
            _extract_go_import_spec(child, file_path, out)
        elif child.type == "interpreted_string_literal":
            module = child.text.decode("utf-8", errors="replace").strip('"')
            out.append(
                ImportInfo(
                    source_module=module,
                    imported_names=[],
                    is_wildcard=False,
                    file_path=file_path,
                    line=line,
                )
            )


def _extract_go_import_spec(
    spec_node: object,
    file_path: str,
    out: list[ImportInfo],
) -> None:
    """Extract a single Go import spec.

    Args:
        spec_node: A tree-sitter import_spec node.
        file_path: Source file path.
        out: Accumulator for import records.
    """
    line = spec_node.start_point[0] + 1  # type: ignore[union-attr]
    path_node = spec_node.child_by_field_name("path")  # type: ignore[union-attr]
    if path_node is not None:
        module = path_node.text.decode("utf-8", errors="replace").strip('"')
    else:
        # Fallback: look for string literal child
        for child in spec_node.named_children:  # type: ignore[union-attr]
            if child.type == "interpreted_string_literal":
                module = child.text.decode("utf-8", errors="replace").strip('"')
                break
        else:
            module = spec_node.text.decode("utf-8", errors="replace").strip('"')

    out.append(
        ImportInfo(
            source_module=module,
            imported_names=[],
            is_wildcard=False,
            file_path=file_path,
            line=line,
        )
    )
