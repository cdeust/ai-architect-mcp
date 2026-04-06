"""Import processor — resolves import nodes into IMPORTS edges.

Given a list of GraphNode objects (some flagged as imports via
properties.is_import), resolves each import to a target file path
and produces IMPORTS relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .._config.supported_languages import SupportedLanguage
from .._models.graph_types import GraphRelationship, GraphNode, RelationshipType
from .._resolution.resolvers.standard import StandardResolver


@dataclass
class ImportResult:
    """Result of import processing for a set of nodes.

    Args:
        relationships: IMPORTS edges created.
        import_map: file_path -> set of resolved target file paths.
        named_import_map: file_path -> {name: resolved_path}.
    """

    relationships: list[GraphRelationship] = field(default_factory=list)
    import_map: dict[str, set[str]] = field(default_factory=dict)
    named_import_map: dict[str, dict[str, str]] = field(
        default_factory=dict,
    )


def process_imports(
    nodes: list[GraphNode],
    file_path: str,
    language: SupportedLanguage,
    suffix_index: dict[str, list[str]],
    resolver: StandardResolver,
) -> ImportResult:
    """Process import nodes and create IMPORTS relationships.

    Filters *nodes* to those with ``properties.is_import == True``,
    resolves each import path via *resolver*, and builds edges
    from the containing file to the resolved target file.

    Args:
        nodes: GraphNode list (may include non-import nodes).
        file_path: Source file path containing the imports.
        language: Language of the source file.
        suffix_index: Pre-built suffix index for resolution.
        resolver: Import resolver instance.

    Returns:
        ImportResult with relationships and lookup maps.
    """
    result = ImportResult()

    for node in nodes:
        if not node.properties.get("is_import"):
            continue

        import_path = node.properties.get("import_path", "")
        if not import_path:
            continue

        resolved = resolver.resolve(str(import_path), file_path)
        if resolved is None:
            continue

        source_id = f"{file_path}:File"
        target_id = f"{resolved}:File"

        result.relationships.append(GraphRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=RelationshipType.IMPORTS,
        ))

        if file_path not in result.import_map:
            result.import_map[file_path] = set()
        result.import_map[file_path].add(resolved)

        imported_names = node.properties.get("imported_names", [])
        if imported_names:
            if file_path not in result.named_import_map:
                result.named_import_map[file_path] = {}
            for name in imported_names:
                result.named_import_map[file_path][str(name)] = resolved

    return result
