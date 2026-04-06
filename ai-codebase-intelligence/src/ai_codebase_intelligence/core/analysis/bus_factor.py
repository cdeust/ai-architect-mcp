"""Bus factor analysis — Avelino et al. 2016.

OBSERVATION: Avelino, G., Passos, L., Hora, A., & Valente, M.T. (2016).
  "A Novel Approach for Estimating Truck Factors." ICPC 2016.

PROBLEM: Projects with a bus factor of 1 face critical knowledge loss
  risk if that developer leaves. Identifying bus factor enables proactive
  knowledge transfer.

SOLUTION: Iteratively remove the top-coverage developer and count how
  many files become orphaned. Bus factor = number of removals before the
  orphan threshold is exceeded.

Algorithm (Avelino et al. 2016, Sec 3):
  1. For each file, determine primary author (highest AUTHORED_BY confidence)
  2. Count files per developer (coverage)
  3. Remove developer with highest coverage
  4. Count orphaned files (files whose primary author was removed)
  5. Repeat until orphaned > threshold * total_files
  6. Bus factor = number of removals
"""

from __future__ import annotations

from typing import Any

from ..graph.graph import KnowledgeGraph


def calculate_bus_factor(
    knowledge_graph: KnowledgeGraph,
    orphan_threshold: float = 0.5,
) -> dict[str, Any]:
    """Calculate the bus factor for the indexed repository.

    Args:
        knowledge_graph: Graph with Contributor nodes and AUTHORED_BY edges.
        orphan_threshold: Fraction of files orphaned to trigger bus factor.
            Default 0.5 per Avelino et al. 2016, Sec 3.

    Returns:
        Dict with busFactor, risk level, and removal sequence.
    """
    file_authors = _extract_file_authors(knowledge_graph)
    total_files = len(file_authors)

    if total_files == 0:
        return _empty_result()

    coverage = _compute_coverage(file_authors)
    removal_sequence: list[dict[str, Any]] = []
    removed: set[str] = set()
    orphaned_count = 0

    while coverage and orphaned_count / total_files < orphan_threshold:
        top_dev = max(coverage, key=lambda d: coverage[d])
        files_lost = coverage.pop(top_dev)
        removed.add(top_dev)
        orphaned_count += files_lost
        removal_sequence.append({
            "developer": top_dev,
            "filesOrphaned": files_lost,
            "cumulativeOrphaned": orphaned_count,
            "fractionOrphaned": round(orphaned_count / total_files, 4),
        })

    bus_factor = len(removal_sequence)
    risk = _classify_risk(bus_factor)

    return {
        "busFactor": bus_factor,
        "risk": risk,
        "totalFiles": total_files,
        "removalSequence": removal_sequence,
        "citation": "Avelino et al. 2016, ICPC",
    }


def _extract_file_authors(
    graph: KnowledgeGraph,
) -> dict[str, str]:
    """Map each file to its primary author (highest AUTHORED_BY confidence).

    Returns:
        Dict of {file_node_id: contributor_key}.
    """
    file_best: dict[str, tuple[str, float]] = {}
    for rel in graph.iter_relationships():
        if rel.relationship_type.value != "AUTHORED_BY":
            continue
        file_id = rel.source_id
        contrib_id = rel.target_id
        conf = rel.confidence
        current = file_best.get(file_id)
        if current is None or conf > current[1]:
            file_best[file_id] = (contrib_id, conf)
    return {fid: author for fid, (author, _) in file_best.items()}


def _compute_coverage(file_authors: dict[str, str]) -> dict[str, int]:
    """Count how many files each developer is primary author of."""
    coverage: dict[str, int] = {}
    for author in file_authors.values():
        coverage[author] = coverage.get(author, 0) + 1
    return coverage


def _classify_risk(bus_factor: int) -> str:
    """Classify bus factor risk. Labels are descriptive, not scientific claims."""
    if bus_factor <= 1:
        return "CRITICAL"
    if bus_factor <= 3:
        return "HIGH"
    if bus_factor <= 6:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> dict[str, Any]:
    """Return empty result when no ownership data exists."""
    return {
        "busFactor": 0,
        "risk": "UNKNOWN",
        "totalFiles": 0,
        "removalSequence": [],
        "citation": "Avelino et al. 2016, ICPC",
    }
