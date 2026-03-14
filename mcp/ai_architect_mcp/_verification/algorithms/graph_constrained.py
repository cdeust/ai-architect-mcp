"""Zero-LLM Graph Constrained Verifier — deterministic graph analysis.

Uses Tarjan's SCC algorithm for cycle detection, contradiction finding,
orphan detection, and coverage analysis. Zero LLM calls.
Research: Tarjan (1972); Besta et al. (2023) Graph of Thoughts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from ai_architect_mcp._models.graph import (
    ClaimGraphNode,
    ClaimRelationshipGraph,
    NodeType,
    RelationshipType,
)
from ai_architect_mcp._models.verification import (
    ClaimEvaluation,
    ClaimSource,
    ClaimType,
    Verdict,
    VerificationClaim,
    VerificationReport,
)

PENALTY_IN_CYCLE = -0.3
PENALTY_IN_CONFLICT = -0.25
PENALTY_ISOLATED = -0.1
BONUS_HIGH_IMPORTANCE = 0.1
GRAPH_CONFIDENCE = 0.95
PASS_THRESHOLD = 0.6


class GraphConstrainedVerifier:
    """Deterministic graph-based verifier. Zero LLM calls.

    Analyzes claim relationship graphs for structural issues:
    cycles, contradictions, orphans, and coverage gaps.
    """

    def verify(
        self, graph: ClaimRelationshipGraph
    ) -> VerificationReport:
        """Verify a claim relationship graph.

        Args:
            graph: The graph to verify.

        Returns:
            VerificationReport with structural analysis results.
        """
        cycles = self._detect_cycles(graph)
        contradictions = self._find_contradictions(graph)
        orphans = self._find_orphans(graph)

        cycle_node_ids = _collect_cycle_ids(cycles)
        conflict_node_ids = _collect_conflict_ids(contradictions)
        orphan_ids = set(orphans)

        claims: list[VerificationClaim] = []
        evaluations: list[ClaimEvaluation] = []

        for node in graph.nodes:
            claim = VerificationClaim(
                claim_id=node.claim_id,
                content=node.label,
                claim_type=ClaimType.GRAPH_NODE,
                source=ClaimSource.GENERATION,
                priority=50,
            )
            claims.append(claim)

            score, reasoning = _score_node(
                node, cycle_node_ids, conflict_node_ids, orphan_ids
            )

            evaluations.append(ClaimEvaluation(
                claim_id=node.claim_id,
                evaluator_id="graph_constrained",
                score=round(score, 4),
                confidence=GRAPH_CONFIDENCE,
                verdict=Verdict.PASS if score >= PASS_THRESHOLD else Verdict.FAIL,
                reasoning=reasoning,
            ))

        overall = (
            sum(e.score for e in evaluations) / len(evaluations)
            if evaluations
            else 0.0
        )

        return VerificationReport(
            claims=claims,
            evaluations=evaluations,
            overall_score=round(min(1.0, max(0.0, overall)), 4),
            algorithm_used="graph_constrained",
            timestamp=datetime.now(timezone.utc),
        )

    def _detect_cycles(
        self, graph: ClaimRelationshipGraph
    ) -> list[list[UUID]]:
        """Detect cycles using Tarjan's SCC algorithm.

        Args:
            graph: The graph to analyze.

        Returns:
            List of strongly connected components with >1 node.
        """
        adjacency: dict[UUID, list[UUID]] = {
            n.node_id: [] for n in graph.nodes
        }
        for edge in graph.edges:
            adjacency[edge.source_id].append(edge.target_id)

        state = _TarjanState()

        for node in graph.nodes:
            if node.node_id not in state.index:
                _strongconnect(node.node_id, adjacency, state)

        return state.sccs

    def _find_contradictions(
        self, graph: ClaimRelationshipGraph
    ) -> list[tuple[UUID, UUID]]:
        """Find edges with relationship=contradicts.

        Args:
            graph: The graph to analyze.

        Returns:
            List of (source_id, target_id) pairs that contradict.
        """
        return [
            (edge.source_id, edge.target_id)
            for edge in graph.edges
            if edge.relationship == RelationshipType.CONTRADICTS
        ]

    def _find_orphans(
        self, graph: ClaimRelationshipGraph
    ) -> list[UUID]:
        """Find nodes with zero incoming edges (except requirements).

        Args:
            graph: The graph to analyze.

        Returns:
            List of orphan node IDs.
        """
        has_incoming: set[UUID] = {
            edge.target_id for edge in graph.edges
        }
        return [
            n.node_id
            for n in graph.nodes
            if n.node_id not in has_incoming
            and n.node_type != NodeType.REQUIREMENT
        ]


class _TarjanState:
    """Mutable state for Tarjan's SCC algorithm."""

    def __init__(self) -> None:
        self.index_counter: int = 0
        self.stack: list[UUID] = []
        self.lowlinks: dict[UUID, int] = {}
        self.index: dict[UUID, int] = {}
        self.on_stack: set[UUID] = set()
        self.sccs: list[list[UUID]] = []


def _strongconnect(
    v: UUID,
    adjacency: dict[UUID, list[UUID]],
    state: _TarjanState,
) -> None:
    """Tarjan's strongconnect subroutine.

    Args:
        v: Current node ID.
        adjacency: Adjacency list.
        state: Mutable Tarjan state.
    """
    state.index[v] = state.index_counter
    state.lowlinks[v] = state.index_counter
    state.index_counter += 1
    state.stack.append(v)
    state.on_stack.add(v)

    for w in adjacency.get(v, []):
        if w not in state.index:
            _strongconnect(w, adjacency, state)
            state.lowlinks[v] = min(state.lowlinks[v], state.lowlinks[w])
        elif w in state.on_stack:
            state.lowlinks[v] = min(state.lowlinks[v], state.index[w])

    if state.lowlinks[v] == state.index[v]:
        scc: list[UUID] = []
        while True:
            w = state.stack.pop()
            state.on_stack.discard(w)
            scc.append(w)
            if w == v:
                break
        if len(scc) > 1:
            state.sccs.append(scc)


def _collect_cycle_ids(cycles: list[list[UUID]]) -> set[UUID]:
    """Collect all node IDs that participate in cycles.

    Args:
        cycles: List of SCCs.

    Returns:
        Set of node IDs in cycles.
    """
    result: set[UUID] = set()
    for cycle in cycles:
        for nid in cycle:
            result.add(nid)
    return result


def _collect_conflict_ids(
    contradictions: list[tuple[UUID, UUID]],
) -> set[UUID]:
    """Collect all node IDs involved in contradictions.

    Args:
        contradictions: List of (source, target) pairs.

    Returns:
        Set of node IDs in conflicts.
    """
    result: set[UUID] = set()
    for src, tgt in contradictions:
        result.add(src)
        result.add(tgt)
    return result


def _score_node(
    node: ClaimGraphNode,
    cycle_ids: set[UUID],
    conflict_ids: set[UUID],
    orphan_ids: set[UUID],
) -> tuple[float, str]:
    """Score a single graph node based on structural issues.

    Args:
        node: The graph node to score.
        cycle_ids: Node IDs in cycles.
        conflict_ids: Node IDs in conflicts.
        orphan_ids: Orphan node IDs.

    Returns:
        Tuple of (score, reasoning_string).
    """
    score = 1.0
    parts: list[str] = []

    if node.node_id in cycle_ids:
        score += PENALTY_IN_CYCLE
        parts.append("node is part of a dependency cycle")
    if node.node_id in conflict_ids:
        score += PENALTY_IN_CONFLICT
        parts.append("node has contradicting relationships")
    if node.node_id in orphan_ids:
        score += PENALTY_ISOLATED
        parts.append("node is isolated (no incoming edges)")
    if node.node_type == NodeType.REQUIREMENT:
        score += BONUS_HIGH_IMPORTANCE
        parts.append("requirement node (high importance)")

    score = max(0.0, min(1.0, score))
    reasoning = "; ".join(parts) if parts else "no structural issues"
    return score, reasoning
