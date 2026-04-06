"""File/folder structure builder.

Converts a flat list of file paths into a hierarchy of Folder and
File GraphNodes connected by CONTAINS relationships.
"""

from __future__ import annotations

import os

from ai_codebase_intelligence._config.supported_languages import detect_language
from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)


def build_structure(
    file_paths: list[str],
    repo_root: str,
) -> tuple[list[GraphNode], list[GraphRelationship]]:
    """Build a file/folder hierarchy from a list of file paths.

    Args:
        file_paths: Absolute paths to source files.
        repo_root: Absolute path to the repository root.

    Returns:
        A tuple of (nodes, relationships) representing the
        folder/file hierarchy.
    """
    nodes: list[GraphNode] = []
    relationships: list[GraphRelationship] = []
    seen_folders: dict[str, str] = {}

    for file_path in file_paths:
        rel_path = os.path.relpath(file_path, repo_root)
        lang = detect_language(file_path)
        lang_str = lang.value if lang else ""

        file_id = f"{rel_path}:File"
        file_node = GraphNode(
            id=file_id,
            label=NodeLabel.FILE,
            name=os.path.basename(file_path),
            file_path=rel_path,
            language=lang_str,
        )
        nodes.append(file_node)

        _ensure_folders(
            rel_path, repo_root, nodes, relationships, seen_folders
        )

        parent_dir = os.path.dirname(rel_path)
        if parent_dir:
            folder_id = seen_folders[parent_dir]
            relationships.append(
                GraphRelationship(
                    source_id=folder_id,
                    target_id=file_id,
                    relationship_type=RelationshipType.CONTAINS,
                )
            )

    return nodes, relationships


def _ensure_folders(
    rel_path: str,
    repo_root: str,
    nodes: list[GraphNode],
    relationships: list[GraphRelationship],
    seen: dict[str, str],
) -> None:
    """Create folder nodes for all ancestor directories.

    Args:
        rel_path: Relative path from repo root.
        repo_root: The repository root path.
        nodes: Accumulator for graph nodes.
        relationships: Accumulator for graph relationships.
        seen: Already-created folder paths mapped to their node IDs.
    """
    parts = os.path.dirname(rel_path).split(os.sep)
    current = ""

    for part in parts:
        if not part:
            continue
        parent = current
        current = os.path.join(current, part) if current else part

        if current in seen:
            continue

        folder_id = f"{current}:Folder"
        seen[current] = folder_id
        nodes.append(
            GraphNode(
                id=folder_id,
                label=NodeLabel.FOLDER,
                name=part,
                file_path=current,
            )
        )

        if parent and parent in seen:
            relationships.append(
                GraphRelationship(
                    source_id=seen[parent],
                    target_id=folder_id,
                    relationship_type=RelationshipType.CONTAINS,
                )
            )
