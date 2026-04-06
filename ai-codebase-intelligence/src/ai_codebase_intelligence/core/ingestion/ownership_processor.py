"""Ownership processor — code ownership analysis per Bird et al. 2011.

OBSERVATION: Bird, C., Nagappan, N., Murphy, B., Gall, H., & Devanbu, P.
  (2011). "Don't Touch My Code! Examining the Effects of Ownership on
  Software Quality." ESEC/FSE 2011.
PROBLEM: Components with low ownership (many minor contributors, no
  dominant author) have significantly more pre/post-release defects.
SOLUTION: Compute per-file ownership ratio and minor contributor count
  using git blame aggregation. Store as Contributor nodes + AUTHORED_BY
  edges in the knowledge graph.

Algorithm (Bird et al. 2011, Sec 4.2 & 5.1):
  ownership_ratio = max_author_lines / total_lines
  minor_contributors = count(authors where lines/total < 0.05)
  Threshold 5% from Bird et al. 2011, Sec 5.1.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from ..._models.graph_types import (
    GraphNode, GraphRelationship, NodeLabel, RelationshipType,
)
from ..graph.graph import KnowledgeGraph
from ...storage.git import git_blame_file
from ...lib.utils import generate_id

logger = logging.getLogger(__name__)

MINOR_THRESHOLD = 0.05  # Bird et al. 2011, Sec 5.1


def process_ownership(
    knowledge_graph: KnowledgeGraph,
    repo_path: str,
    on_progress: Callable[[str, int], None] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute code ownership and create Contributor nodes + AUTHORED_BY edges.

    Args:
        knowledge_graph: The knowledge graph to mutate.
        repo_path: Absolute path to the git repository.
        on_progress: Optional progress callback(message, percent).
        config: Optional config with minor_contributor_threshold.

    Returns:
        Dict with contributors list, ownership data, and stats.
    """
    cfg = config or {}
    threshold = cfg.get("minor_contributor_threshold", MINOR_THRESHOLD)

    file_nodes = _collect_file_nodes(knowledge_graph)
    total = len(file_nodes)
    if on_progress:
        on_progress(f"Analyzing ownership for {total} files...", 0)

    contributors: dict[str, dict[str, Any]] = {}
    ownerships: list[dict[str, Any]] = []
    files_processed = 0

    for file_id, file_path in file_nodes:
        blame = git_blame_file(repo_path, file_path)
        if not blame:
            files_processed += 1
            continue

        total_lines = sum(a["line_count"] for a in blame)
        if total_lines == 0:
            files_processed += 1
            continue

        ownership = _compute_file_ownership(
            file_id, file_path, blame, total_lines, threshold,
        )
        ownerships.append(ownership)

        _upsert_contributors(
            knowledge_graph, contributors, blame, file_id, total_lines,
        )

        files_processed += 1
        if on_progress and files_processed % 50 == 0:
            pct = int((files_processed / max(total, 1)) * 100)
            on_progress(f"Ownership: {files_processed}/{total} files", pct)

    if on_progress:
        on_progress("Ownership analysis complete", 100)

    return {
        "contributors": list(contributors.values()),
        "ownerships": ownerships,
        "stats": {
            "filesAnalyzed": files_processed,
            "contributorsFound": len(contributors),
            "filesWithLowOwnership": sum(
                1 for o in ownerships if o["ownershipRatio"] < 0.5
            ),
        },
    }


def _collect_file_nodes(
    graph: KnowledgeGraph,
) -> list[tuple[str, str]]:
    """Extract (id, filePath) pairs for all File nodes."""
    results: list[tuple[str, str]] = []
    for node in graph.iter_nodes():
        if node.label.value == "File":
            if node.file_path:
                results.append((node.id, node.file_path))
    return results


def _compute_file_ownership(
    file_id: str,
    file_path: str,
    blame: list[dict[str, Any]],
    total_lines: int,
    threshold: float,
) -> dict[str, Any]:
    """Compute ownership metrics for a single file."""
    top = blame[0]
    ownership_ratio = top["line_count"] / total_lines
    minor_count = sum(
        1 for a in blame if a["line_count"] / total_lines < threshold
    )
    return {
        "fileId": file_id,
        "filePath": file_path,
        "ownershipRatio": round(ownership_ratio, 4),
        "minorContributors": minor_count,
        "topContributor": top["author"],
        "topContributorEmail": top["email"],
        "authorCount": len(blame),
    }


def _upsert_contributors(
    graph: KnowledgeGraph,
    contributors: dict[str, dict[str, Any]],
    blame: list[dict[str, Any]],
    file_id: str,
    total_lines: int,
) -> None:
    """Create Contributor nodes and AUTHORED_BY edges."""
    for author_info in blame:
        key = author_info["email"] or author_info["author"]
        contrib_id = generate_id("Contributor", key)

        if key not in contributors:
            contributors[key] = {
                "id": contrib_id,
                "name": author_info["author"],
                "email": author_info["email"],
                "commitCount": 0,
                "filesAuthored": 0,
            }
            graph.add_node(GraphNode(
                id=contrib_id,
                label=NodeLabel.CONTRIBUTOR,
                name=author_info["author"],
                properties={
                    "email": author_info["email"],
                    "commitCount": 0,
                },
            ))

        contributors[key]["filesAuthored"] += 1
        fraction = author_info["line_count"] / total_lines

        graph.add_relationship(GraphRelationship(
            source_id=file_id,
            target_id=contrib_id,
            relationship_type=RelationshipType.AUTHORED_BY,
            confidence=round(fraction, 4),
            properties={"reason": "git-blame-bird-2011"},
        ))
