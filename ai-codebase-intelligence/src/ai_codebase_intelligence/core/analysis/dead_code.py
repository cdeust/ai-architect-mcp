"""Dead code detection via conservative reachability analysis.

OBSERVATION: Grove, D., DeFouw, G., Dean, J., & Chambers, C. (1997).
  "Call Graph Construction in Object-Oriented Languages." OOPSLA 1997.
OBSERVATION: Tip, F., Palsberg, J., & Feinberg, M. (1999). "Scalable
  Propagation-Based Call Graph Construction Algorithms." OOPSLA 1999.

PROBLEM: Unused code accumulates as technical debt. Static reachability
  analysis identifies candidates for removal.

SOLUTION: Conservative CHA-based reachability from entry points.
  BFS from all entry points following CALLS edges. Unreachable nodes
  are dead code candidates with confidence levels reflecting call graph
  precision. Dynamic languages have higher false positive rates
  (Grove et al. 1997) — confidence is adjusted accordingly.

Confidence levels:
  HIGH (0.9): Unreachable, static language, no dynamic patterns
  MEDIUM (0.6): Unreachable, dynamic language or plugin-like naming
  LOW (0.3): Unreachable, reflection/decorator patterns detected
"""

from __future__ import annotations

import re
from typing import Any

from ..storage.graph_index import GraphIndex

# Patterns suggesting dynamic dispatch — lower confidence
DYNAMIC_PATTERNS = re.compile(
    r"(Plugin|Handler|Adapter|Middleware|Factory|Provider|Registry|Hook|Listener"
    r"|Callback|Decorator|Extension|Interceptor)$",
    re.IGNORECASE,
)

# Languages with high metaprogramming risk
DYNAMIC_LANGUAGES = frozenset({
    "python", "javascript", "typescript", "ruby", "php",
})

# Symbol types that can be entry points
ENTRY_LABELS = frozenset({
    "Function", "Method", "Class", "Constructor",
})

# Minimum entry point score to consider as an actual entry point
MIN_ENTRY_SCORE = 1.5


def detect_dead_code(
    index: GraphIndex,
    min_confidence: float = 0.6,
    include_low_confidence: bool = False,
) -> dict[str, Any]:
    """Detect unreachable code via BFS from entry points.

    Args:
        index: In-memory graph index with nodes and edges.
        min_confidence: Minimum confidence to include in results.
        include_low_confidence: Include LOW confidence candidates.

    Returns:
        Dict with candidates list and stats.
    """
    entry_points = _find_entry_points(index)
    reachable = _compute_reachable(index, entry_points)
    all_symbols = _collect_symbols(index)

    candidates: list[dict[str, Any]] = []
    excluded = 0

    for sym_id, sym in all_symbols.items():
        if sym_id in reachable:
            continue
        if _is_excluded(sym):
            excluded += 1
            continue

        confidence, reason = _classify_confidence(sym)
        if confidence < min_confidence and not include_low_confidence:
            excluded += 1
            continue

        candidates.append({
            "nodeId": sym_id,
            "name": sym.get("name", ""),
            "filePath": sym.get("filePath", ""),
            "label": sym.get("label", ""),
            "confidence": confidence,
            "reason": reason,
        })

    candidates.sort(key=lambda c: c["confidence"], reverse=True)

    return {
        "candidates": candidates,
        "stats": {
            "totalSymbols": len(all_symbols),
            "reachable": len(reachable),
            "unreachable": len(all_symbols) - len(reachable),
            "excluded": excluded,
            "reported": len(candidates),
            "entryPoints": len(entry_points),
        },
        "citation": "Grove et al. 1997, OOPSLA; Tip et al. 1999, OOPSLA",
    }


def _find_entry_points(index: GraphIndex) -> set[str]:
    """Identify entry points using caller/callee ratio heuristic.

    Entry points have many callees but few callers. Uses the same
    heuristic as entry_point_scoring.py: callee_count / (caller_count + 1).
    """
    entry_points: set[str] = set()
    for node_id, node in index._nodes.items():
        if node.label.value not in ENTRY_LABELS:
            continue
        if _is_test_file(node.file_path):
            continue
        callers = index.caller_count(node_id)
        callees = index.callee_count(node_id)
        score = callees / (callers + 1)
        if node.is_exported:
            score *= 2.0
        if score >= MIN_ENTRY_SCORE:
            entry_points.add(node_id)
    return entry_points


def _compute_reachable(
    index: GraphIndex,
    entry_points: set[str],
) -> set[str]:
    """BFS from all entry points following CALLS edges."""
    reachable: set[str] = set(entry_points)
    frontier = list(entry_points)

    while frontier:
        next_frontier: list[str] = []
        for node_id in frontier:
            for target_id, rel in index._out.get(node_id, []):
                if rel.relationship_type.value != "CALLS":
                    continue
                if target_id in reachable:
                    continue
                reachable.add(target_id)
                next_frontier.append(target_id)
        frontier = next_frontier

    return reachable


def _collect_symbols(index: GraphIndex) -> dict[str, dict[str, Any]]:
    """Collect all symbol nodes (functions, methods, classes)."""
    symbols: dict[str, dict[str, Any]] = {}
    for node_id, node in index._nodes.items():
        if node.label.value not in ENTRY_LABELS:
            continue
        if _is_test_file(node.file_path):
            continue
        symbols[node_id] = {
            "name": node.name,
            "filePath": node.file_path,
            "label": node.label.value,
            "language": node.language,
            "isExported": node.is_exported,
        }
    return symbols


def _is_excluded(sym: dict[str, Any]) -> bool:
    """Check if symbol should be excluded from dead code detection."""
    name = sym.get("name", "")
    if name.startswith("_") and not name.startswith("__"):
        return False  # private functions can still be dead
    if name.startswith("__") and name.endswith("__"):
        return True  # dunder methods are framework-called
    return False


def _classify_confidence(sym: dict[str, Any]) -> tuple[float, str]:
    """Classify dead code confidence based on language and naming."""
    name = sym.get("name", "")
    language = sym.get("language", "").lower()

    if DYNAMIC_PATTERNS.search(name):
        return 0.3, "dynamic-pattern-name"
    if language in DYNAMIC_LANGUAGES:
        return 0.6, "dynamic-language"
    if sym.get("isExported", False):
        return 0.6, "exported-but-unreachable"
    return 0.9, "static-unreachable"


def _is_test_file(file_path: str) -> bool:
    """Check if a file is a test file."""
    p = file_path.lower()
    return any(marker in p for marker in (
        ".test.", ".spec.", "__tests__/", "__mocks__/",
        "/test/", "/tests/", "/testing/", "/fixtures/",
        "_test.go", "_test.py", "/test_", "/conftest.",
    ))
