"""Backend: resource query helpers for clusters and processes."""

from __future__ import annotations

import json
from typing import Any

from ...core.storage.repo_store import get_index, query_sql


async def query_clusters(
    backend: Any, repo_name: str, limit: int = 100,
) -> dict[str, Any]:
    """List community clusters with stats."""
    repo = await backend.resolve_repo(repo_name)
    await backend.ensure_initialized(repo["id"])
    try:
        rows = query_sql(repo["id"],
            f"SELECT id, properties FROM nodes WHERE label = 'Community' "
            f"ORDER BY CAST(json_extract(properties, '$.symbolCount') AS INTEGER) DESC LIMIT {limit}")
        clusters = []
        for r in rows:
            props = json.loads(r.get("properties", "{}"))
            clusters.append({
                "id": r["id"], "heuristicLabel": props.get("heuristicLabel", ""),
                "cohesion": props.get("cohesion", 0), "symbolCount": props.get("symbolCount", 0),
            })
        return {"clusters": clusters}
    except Exception:
        return {"clusters": []}


async def query_processes(
    backend: Any, repo_name: str, limit: int = 50,
) -> dict[str, Any]:
    """List execution flow processes with stats."""
    repo = await backend.resolve_repo(repo_name)
    await backend.ensure_initialized(repo["id"])
    try:
        rows = query_sql(repo["id"],
            f"SELECT id, properties FROM nodes WHERE label = 'Process' "
            f"ORDER BY CAST(json_extract(properties, '$.stepCount') AS INTEGER) DESC LIMIT {limit}")
        processes = []
        for r in rows:
            props = json.loads(r.get("properties", "{}"))
            processes.append({
                "id": r["id"], "heuristicLabel": props.get("heuristicLabel", ""),
                "processType": props.get("processType", ""), "stepCount": props.get("stepCount", 0),
            })
        return {"processes": processes}
    except Exception:
        return {"processes": []}


async def query_cluster_detail(
    backend: Any, name: str, repo_name: str,
) -> dict[str, Any]:
    """Get details and members of a specific community cluster."""
    repo = await backend.resolve_repo(repo_name)
    await backend.ensure_initialized(repo["id"])
    idx = get_index(repo["id"])
    clusters = idx.find_by_name(name)
    community = next((c for c in clusters if c.label.value == "Community"), None)
    if not community:
        return {"error": f"Cluster '{name}' not found"}
    members = []
    for nid, edges in idx._in.items():
        for src_id, rel in edges:
            if rel.relationship_type.value == "MEMBER_OF" and rel.target_id == community.id:
                node = idx.get_node(src_id)
                if node:
                    members.append({"name": node.name, "filePath": node.file_path})
    return {
        "cluster": {"id": community.id, "heuristicLabel": community.properties.get("heuristicLabel", community.name),
                    "cohesion": community.properties.get("cohesion", 0), "symbolCount": community.properties.get("symbolCount", 0)},
        "members": members[:30],
    }


async def query_process_detail(
    backend: Any, name: str, repo_name: str,
) -> dict[str, Any]:
    """Get details and steps of a specific execution flow process."""
    repo = await backend.resolve_repo(repo_name)
    await backend.ensure_initialized(repo["id"])
    idx = get_index(repo["id"])
    procs = idx.find_by_name(name)
    process = next((p for p in procs if p.label.value == "Process"), None)
    if not process:
        return {"error": f"Process '{name}' not found"}
    steps = []
    for nid_edges in idx._in.get(process.id, []):
        src_id, rel = nid_edges
        if rel.relationship_type.value == "STEP_IN_PROCESS":
            node = idx.get_node(src_id)
            if node:
                steps.append({
                    "step": rel.properties.get("step", 0),
                    "name": node.name,
                    "filePath": node.file_path,
                })
    steps.sort(key=lambda s: s["step"])
    return {
        "process": {"id": process.id, "heuristicLabel": process.properties.get("heuristicLabel", process.name),
                    "processType": process.properties.get("processType", ""), "stepCount": process.properties.get("stepCount", 0)},
        "steps": steps,
    }
