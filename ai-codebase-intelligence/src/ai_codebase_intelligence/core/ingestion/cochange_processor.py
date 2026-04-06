"""Co-change processor — logical coupling via association rule mining.

OBSERVATION: Gall, H., Hajek, K., & Jazayeri, M. (1998). "Detection of
  Logical Coupling Based on Product Release History." ICSM 1998.
OBSERVATION: Zimmermann, T., Zeller, A., Weissgerber, P., & Diehl, S.
  (2005). "Mining Version Histories to Guide Software Changes." IEEE TSE.

PROBLEM: Files that change together without import links indicate hidden
  coupling — structural debt invisible to AST analysis.
SOLUTION: Association rule mining on commit history. For each file pair,
  compute support (co-occurrence count) and confidence (conditional
  probability). Thresholds are tunable per project — no universal
  optimal value (Zimmermann et al. 2005, Sec 5.3).

Algorithm:
  support(A,B) = count(commits containing both A and B)
  confidence(A→B) = support(A,B) / count(commits containing A)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

from ..._models.graph_types import GraphRelationship, RelationshipType
from ..graph.graph import KnowledgeGraph
from ...storage.git import git_log_commits
from ...lib.utils import generate_id

logger = logging.getLogger(__name__)

DEFAULT_MIN_SUPPORT = 3
DEFAULT_MIN_CONFIDENCE = 0.5
DEFAULT_MAX_COMMITS = 500


def process_cochange(
    knowledge_graph: KnowledgeGraph,
    repo_path: str,
    on_progress: Callable[[str, int], None] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect co-change pairs and create CO_CHANGES_WITH edges.

    Args:
        knowledge_graph: The knowledge graph to mutate.
        repo_path: Absolute path to the git repository.
        on_progress: Optional progress callback(message, percent).
        config: Optional config overrides for thresholds.

    Returns:
        Dict with pairs list and stats.
    """
    cfg = config or {}
    min_support = cfg.get("cochange_min_support", DEFAULT_MIN_SUPPORT)
    min_confidence = cfg.get("cochange_min_confidence", DEFAULT_MIN_CONFIDENCE)
    max_commits = cfg.get("max_commits", DEFAULT_MAX_COMMITS)

    if on_progress:
        on_progress("Extracting commit history...", 0)

    commits = git_log_commits(repo_path, max_commits=max_commits)
    if not commits:
        return {"pairs": [], "stats": {"commitsAnalyzed": 0, "pairsFound": 0}}

    indexed_files = _get_indexed_file_paths(knowledge_graph)
    if on_progress:
        on_progress(f"Mining {len(commits)} commits for co-change...", 30)

    file_commits, pair_support = _mine_cooccurrences(commits, indexed_files)

    if on_progress:
        on_progress("Computing confidence scores...", 70)

    pairs = _filter_pairs(
        pair_support, file_commits, min_support, min_confidence,
    )

    _create_cochange_edges(knowledge_graph, pairs, indexed_files)

    if on_progress:
        on_progress(f"Found {len(pairs)} co-change pairs", 100)

    return {
        "pairs": pairs,
        "stats": {
            "commitsAnalyzed": len(commits),
            "pairsFound": len(pairs),
            "filesWithCochange": len({p["fileA"] for p in pairs} | {p["fileB"] for p in pairs}),
        },
    }


def _get_indexed_file_paths(graph: KnowledgeGraph) -> dict[str, str]:
    """Get {filePath: nodeId} for all indexed File nodes."""
    result: dict[str, str] = {}
    for node in graph.iter_nodes():
        if node.label.value == "File":
            if node.file_path:
                result[node.file_path] = node.id
    return result


def _mine_cooccurrences(
    commits: list[dict[str, Any]],
    indexed_files: dict[str, str],
) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    """Count per-file commits and pairwise co-occurrences.

    Only considers files that are in the indexed graph.
    """
    file_commits: dict[str, int] = defaultdict(int)
    pair_support: dict[tuple[str, str], int] = defaultdict(int)

    for commit in commits:
        files = [f for f in commit.get("files", []) if f in indexed_files]
        for f in files:
            file_commits[f] += 1
        for i, fa in enumerate(files):
            for fb in files[i + 1:]:
                key = (min(fa, fb), max(fa, fb))
                pair_support[key] += 1

    return dict(file_commits), dict(pair_support)


def _filter_pairs(
    pair_support: dict[tuple[str, str], int],
    file_commits: dict[str, int],
    min_support: int,
    min_confidence: float,
) -> list[dict[str, Any]]:
    """Filter pairs by support and confidence thresholds."""
    pairs: list[dict[str, Any]] = []
    for (fa, fb), support in pair_support.items():
        if support < min_support:
            continue
        count_a = file_commits.get(fa, 0)
        count_b = file_commits.get(fb, 0)
        conf_a_to_b = support / count_a if count_a > 0 else 0.0
        conf_b_to_a = support / count_b if count_b > 0 else 0.0
        max_conf = max(conf_a_to_b, conf_b_to_a)
        if max_conf < min_confidence:
            continue
        pairs.append({
            "fileA": fa,
            "fileB": fb,
            "support": support,
            "confidenceAtoB": round(conf_a_to_b, 4),
            "confidenceBtoA": round(conf_b_to_a, 4),
        })
    return sorted(pairs, key=lambda p: p["support"], reverse=True)


def _create_cochange_edges(
    graph: KnowledgeGraph,
    pairs: list[dict[str, Any]],
    indexed_files: dict[str, str],
) -> None:
    """Create CO_CHANGES_WITH relationships in the graph."""
    for pair in pairs:
        id_a = indexed_files.get(pair["fileA"])
        id_b = indexed_files.get(pair["fileB"])
        if not id_a or not id_b:
            continue

        graph.add_relationship(GraphRelationship(
            source_id=id_a,
            target_id=id_b,
            relationship_type=RelationshipType.CO_CHANGES_WITH,
            confidence=round(max(pair["confidenceAtoB"], pair["confidenceBtoA"]), 4),
            properties={"reason": "gall-1998-zimmermann-2005"},
        ))
