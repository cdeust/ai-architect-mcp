"""Incremental reindex — re-parses only changed files.

Given a list of changed file paths, reads and parses each file,
stores resulting nodes in the provided storage, and returns a
PipelineResult with counts and timing.
"""

from __future__ import annotations

import logging
import os
import time

from .._config.supported_languages import detect_language
from .._models.graph_types import GraphNode, NodeLabel
from .._models.pipeline_types import PipelineResult
from .._storage.in_memory_graph import InMemoryGraphStorage

logger = logging.getLogger(__name__)


async def incremental_reindex(
    repo_path: str,
    storage: InMemoryGraphStorage,
    changed_files: list[str],
) -> PipelineResult:
    """Re-index only the specified changed files.

    Reads each file, detects its language, parses symbols via
    tree-sitter (when available), and stores nodes in *storage*.

    Args:
        repo_path: Repository root path.
        storage: Graph storage backend.
        changed_files: Absolute paths to files that changed.

    Returns:
        PipelineResult with counts of files, nodes, relationships.
    """
    start = time.monotonic()

    if not changed_files:
        return PipelineResult(
            repo_path=repo_path,
            total_files=0,
            total_nodes=0,
            total_relationships=0,
            duration_seconds=0.0,
        )

    total_nodes = 0
    total_rels = 0
    files_processed = 0

    for file_path in changed_files:
        if not os.path.isfile(file_path):
            continue

        nodes = _parse_file_to_nodes(file_path, repo_path)
        if nodes:
            await storage.store_nodes(nodes)
            total_nodes += len(nodes)

        files_processed += 1

    elapsed = time.monotonic() - start

    return PipelineResult(
        repo_path=repo_path,
        total_files=files_processed,
        total_nodes=total_nodes,
        total_relationships=total_rels,
        duration_seconds=elapsed,
    )


def _parse_file_to_nodes(
    file_path: str,
    repo_path: str,
) -> list[GraphNode]:
    """Parse a single file into GraphNode objects.

    Uses tree-sitter when available for the detected language.
    Falls back to lightweight AST extraction for Python files.

    Args:
        file_path: Absolute path to the source file.
        repo_path: Repository root for computing relative paths.

    Returns:
        List of extracted GraphNode instances.
    """
    try:
        content = _read_file(file_path)
    except OSError:
        return []

    if not content.strip():
        return []

    lang = detect_language(file_path)
    rel_path = os.path.relpath(file_path, repo_path)

    nodes = _try_tree_sitter(file_path, content, lang, rel_path)
    if nodes is not None:
        return nodes

    if lang is not None and lang.value == "python":
        return _fallback_python_ast(content, rel_path)

    return [_file_node(rel_path)]


def _read_file(file_path: str) -> str:
    """Read file content as UTF-8 with fallback encoding.

    Args:
        file_path: Absolute path.

    Returns:
        File content string.

    Raises:
        OSError: If the file cannot be read.
    """
    with open(file_path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _try_tree_sitter(
    file_path: str,
    content: str,
    lang: object,
    rel_path: str,
) -> list[GraphNode] | None:
    """Attempt tree-sitter parsing. Returns None if unavailable.

    Args:
        file_path: Absolute path.
        content: File content.
        lang: Detected SupportedLanguage or None.
        rel_path: Relative path for node IDs.

    Returns:
        List of nodes if tree-sitter succeeded, None otherwise.
    """
    if lang is None:
        return None

    try:
        from .._adapters.tree_sitter_adapter import TreeSitterParser
        parser = TreeSitterParser()
        node_models = parser.parse_file(rel_path, content, lang.value)
    except (ImportError, Exception):
        return None

    if not node_models:
        return None

    nodes: list[GraphNode] = []
    for nm in node_models:
        try:
            label = NodeLabel(nm.label)
        except ValueError:
            label = NodeLabel.CODE_ELEMENT

        nodes.append(GraphNode(
            id=nm.id,
            label=label,
            name=nm.name,
            file_path=rel_path,
            start_line=nm.start_line,
            end_line=nm.end_line,
            properties=dict(nm.properties),
        ))

    return nodes


def _fallback_python_ast(
    content: str,
    rel_path: str,
) -> list[GraphNode]:
    """Extract symbols from Python source using the ast module.

    Args:
        content: Python source code.
        rel_path: Relative file path.

    Returns:
        List of GraphNode instances for top-level definitions.
    """
    import ast

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [_file_node(rel_path)]

    nodes: list[GraphNode] = [_file_node(rel_path)]
    for item in ast.iter_child_nodes(tree):
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            nodes.append(GraphNode(
                id=f"{rel_path}:{item.name}:fn:{item.lineno}",
                label=NodeLabel.FUNCTION,
                name=item.name,
                file_path=rel_path,
                start_line=item.lineno,
                end_line=item.end_lineno or item.lineno,
            ))
        elif isinstance(item, ast.ClassDef):
            nodes.append(GraphNode(
                id=f"{rel_path}:{item.name}:cls:{item.lineno}",
                label=NodeLabel.CLASS,
                name=item.name,
                file_path=rel_path,
                start_line=item.lineno,
                end_line=item.end_lineno or item.lineno,
            ))

    return nodes


def _file_node(rel_path: str) -> GraphNode:
    """Create a File node for a given path.

    Args:
        rel_path: Relative file path.

    Returns:
        GraphNode with FILE label.
    """
    return GraphNode(
        id=f"{rel_path}:File",
        label=NodeLabel.FILE,
        name=os.path.basename(rel_path),
        file_path=rel_path,
    )
