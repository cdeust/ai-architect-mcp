"""Community detection — 1:1 port of gitnexus community-processor.js."""
from __future__ import annotations

from typing import Any, Callable

from ..graph.graph import KnowledgeGraph

COMMUNITY_COLORS = [
    "#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4",
    "#3b82f6", "#8b5cf6", "#d946ef", "#ec4899", "#f43f5e",
    "#14b8a6", "#84cc16",
]

MIN_CONFIDENCE_LARGE = 0.5
LEIDEN_TIMEOUT_S = 60


def get_community_color(community_index: int) -> str:
    return COMMUNITY_COLORS[community_index % len(COMMUNITY_COLORS)]


def process_communities(
    knowledge_graph: KnowledgeGraph,
    on_progress: Callable[[str, int], None] | None = None,
) -> dict[str, Any]:
    if on_progress:
        on_progress("Building graph for community detection...", 0)

    symbol_labels = {"Function", "Class", "Method", "Interface"}
    symbol_count = sum(
        1 for n in knowledge_graph.iter_nodes() if n.label.value in symbol_labels
    )
    is_large = symbol_count > 10_000

    try:
        import igraph as ig
        import leidenalg
    except ImportError:
        return {
            "communities": [],
            "memberships": [],
            "stats": {"totalCommunities": 0, "modularity": 0, "nodesProcessed": 0},
        }

    clustering_types = {"CALLS", "EXTENDS", "IMPLEMENTS"}
    connected: set[str] = set()
    node_degree: dict[str, int] = {}

    for rel in knowledge_graph.iter_relationships():
        if rel.relationship_type.value not in clustering_types:
            continue
        if rel.source_id == rel.target_id:
            continue
        if is_large and rel.confidence < MIN_CONFIDENCE_LARGE:
            continue
        connected.add(rel.source_id)
        connected.add(rel.target_id)
        node_degree[rel.source_id] = node_degree.get(rel.source_id, 0) + 1
        node_degree[rel.target_id] = node_degree.get(rel.target_id, 0) + 1

    # Build igraph
    node_ids: list[str] = []
    id_to_idx: dict[str, int] = {}

    for node in knowledge_graph.iter_nodes():
        if node.label.value not in symbol_labels:
            continue
        if node.id not in connected:
            continue
        if is_large and node_degree.get(node.id, 0) < 2:
            continue
        id_to_idx[node.id] = len(node_ids)
        node_ids.append(node.id)

    if not node_ids:
        return {
            "communities": [],
            "memberships": [],
            "stats": {"totalCommunities": 0, "modularity": 0, "nodesProcessed": 0},
        }

    edges: list[tuple[int, int]] = []
    seen_edges: set[tuple[int, int]] = set()
    for rel in knowledge_graph.iter_relationships():
        if rel.relationship_type.value not in clustering_types:
            continue
        if is_large and rel.confidence < MIN_CONFIDENCE_LARGE:
            continue
        s = id_to_idx.get(rel.source_id)
        t = id_to_idx.get(rel.target_id)
        if s is not None and t is not None and s != t:
            edge = (min(s, t), max(s, t))
            if edge not in seen_edges:
                seen_edges.add(edge)
                edges.append(edge)

    g = ig.Graph(n=len(node_ids), edges=edges, directed=False)

    if on_progress:
        lbl = f" (filtered from {symbol_count} symbols)" if is_large else ""
        on_progress(f"Running Leiden on {len(node_ids)} nodes, {len(edges)} edges{lbl}...", 30)

    resolution = 2.0 if is_large else 1.0
    try:
        partition = leidenalg.find_partition(
            g, leidenalg.RBConfigurationVertexPartition,
            resolution_parameter=resolution,
        )
    except Exception:
        partition_map = {nid: 0 for nid in node_ids}
        return _build_result(partition_map, 1, 0.0, knowledge_graph, on_progress)

    # Map back to node IDs
    partition_map: dict[str, int] = {}
    for idx, comm in enumerate(partition.membership):
        partition_map[node_ids[idx]] = comm

    comm_count = max(partition.membership) + 1 if partition.membership else 0
    modularity = partition.modularity

    if on_progress:
        on_progress(f"Found {comm_count} communities...", 60)

    return _build_result(partition_map, comm_count, modularity, knowledge_graph, on_progress)


def _build_result(
    communities_map: dict[str, int],
    count: int,
    modularity: float,
    knowledge_graph: KnowledgeGraph,
    on_progress: Callable[[str, int], None] | None,
) -> dict[str, Any]:
    # Group by community
    comm_members: dict[int, list[str]] = {}
    for nid, comm_num in communities_map.items():
        comm_members.setdefault(comm_num, []).append(nid)

    # Build node path lookup
    node_path: dict[str, str] = {}
    for node in knowledge_graph.iter_nodes():
        if node.file_path:
            node_path[node.id] = node.file_path

    community_nodes: list[dict[str, Any]] = []
    for comm_num, member_ids in comm_members.items():
        if len(member_ids) < 2:
            continue
        label = _generate_heuristic_label(member_ids, node_path, comm_num)
        community_nodes.append({
            "id": f"comm_{comm_num}",
            "label": label,
            "heuristicLabel": label,
            "cohesion": _calculate_cohesion(member_ids, communities_map),
            "symbolCount": len(member_ids),
        })

    community_nodes.sort(key=lambda c: c["symbolCount"], reverse=True)

    if on_progress:
        on_progress("Creating membership edges...", 80)

    memberships = [
        {"nodeId": nid, "communityId": f"comm_{comm}"}
        for nid, comm in communities_map.items()
    ]

    if on_progress:
        on_progress("Community detection complete!", 100)

    return {
        "communities": community_nodes,
        "memberships": memberships,
        "stats": {
            "totalCommunities": count,
            "modularity": modularity,
            "nodesProcessed": len(communities_map),
        },
    }


def _generate_heuristic_label(
    member_ids: list[str], node_path: dict[str, str], comm_num: int
) -> str:
    folder_counts: dict[str, int] = {}
    generic = {"src", "lib", "core", "utils", "common", "shared", "helpers"}
    for nid in member_ids:
        fp = node_path.get(nid, "")
        parts = [p for p in fp.split("/") if p]
        if len(parts) >= 2:
            folder = parts[-2]
            if folder.lower() not in generic:
                folder_counts[folder] = folder_counts.get(folder, 0) + 1

    if folder_counts:
        best = max(folder_counts, key=lambda k: folder_counts[k])
        return best[0].upper() + best[1:]

    return f"Cluster_{comm_num}"


def _calculate_cohesion(
    member_ids: list[str], communities_map: dict[str, int]
) -> float:
    if len(member_ids) <= 1:
        return 1.0
    member_set = set(member_ids)
    comm = communities_map.get(member_ids[0], -1)
    in_comm = sum(1 for m in member_ids if communities_map.get(m) == comm)
    return min(1.0, in_comm / len(member_ids))
