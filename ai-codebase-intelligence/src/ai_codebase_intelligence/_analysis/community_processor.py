"""Community detection via Leiden algorithm.

Wraps igraph + leidenalg to partition callable graph nodes into
communities based on CALLS, EXTENDS, and IMPLEMENTS relationships.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ai_codebase_intelligence._models.graph_types import (
    GraphNode,
    GraphRelationship,
    NodeLabel,
    RelationshipType,
)

_CLUSTERING_TYPES = frozenset({
    RelationshipType.CALLS,
    RelationshipType.EXTENDS,
    RelationshipType.IMPLEMENTS,
})

_CALLABLE_LABELS = frozenset({
    NodeLabel.FUNCTION,
    NodeLabel.METHOD,
    NodeLabel.CLASS,
    NodeLabel.INTERFACE,
    NodeLabel.CONSTRUCTOR,
})


class CommunityResult(BaseModel):
    """Result of community detection.

    Args:
        communities: Mapping of community_id to member node IDs.
        node_community: Mapping of node_id to its community_id.
        modularity: Graph modularity score from Leiden.
        metadata: Additional detection metadata.
    """

    communities: dict[str, list[str]] = Field(
        default_factory=dict,
        description="community_id -> [node_ids]",
    )
    node_community: dict[str, str] = Field(
        default_factory=dict,
        description="node_id -> community_id",
    )
    modularity: float = Field(default=0.0, description="Graph modularity")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional detection metadata",
    )


def detect_communities(
    nodes: list[GraphNode],
    rels: list[GraphRelationship],
) -> CommunityResult:
    """Detect communities among callable nodes using the Leiden algorithm.

    Args:
        nodes: All graph nodes.
        rels: All graph relationships.

    Returns:
        A CommunityResult with community assignments and modularity.
    """
    callable_nodes = [n for n in nodes if n.label in _CALLABLE_LABELS]
    callable_ids = {n.id for n in callable_nodes}

    clustering_rels = [
        r for r in rels
        if r.relationship_type in _CLUSTERING_TYPES
        and r.source_id in callable_ids
        and r.target_id in callable_ids
        and r.source_id != r.target_id
    ]

    if not callable_nodes:
        return CommunityResult(
            communities={"0": []},
            modularity=0.0,
        )

    if not clustering_rels:
        comm_id = "0"
        member_ids = [n.id for n in callable_nodes]
        node_comm = {nid: comm_id for nid in member_ids}
        return CommunityResult(
            communities={comm_id: member_ids},
            node_community=node_comm,
            modularity=0.0,
        )

    return _leiden_partition(callable_nodes, clustering_rels)


def _leiden_partition(
    nodes: list[GraphNode],
    rels: list[GraphRelationship],
) -> CommunityResult:
    """Run Leiden partitioning on the filtered graph.

    Args:
        nodes: Callable nodes only.
        rels: Filtered clustering relationships.

    Returns:
        CommunityResult from Leiden.
    """
    import igraph as ig
    import leidenalg

    node_ids = [n.id for n in nodes]
    id_to_idx: dict[str, int] = {nid: i for i, nid in enumerate(node_ids)}

    edges: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for r in rels:
        s = id_to_idx.get(r.source_id)
        t = id_to_idx.get(r.target_id)
        if s is not None and t is not None and s != t:
            edge = (min(s, t), max(s, t))
            if edge not in seen:
                seen.add(edge)
                edges.append(edge)

    g = ig.Graph(n=len(node_ids), edges=edges, directed=False)

    partition = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        resolution_parameter=1.0,
    )

    communities: dict[str, list[str]] = {}
    node_community: dict[str, str] = {}

    for idx, comm in enumerate(partition.membership):
        comm_id = str(comm)
        nid = node_ids[idx]
        communities.setdefault(comm_id, []).append(nid)
        node_community[nid] = comm_id

    return CommunityResult(
        communities=communities,
        node_community=node_community,
        modularity=partition.modularity,
    )
