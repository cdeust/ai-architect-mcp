"""Impact tool — uses GraphIndex BFS instead of KuzuDB Cypher."""
from __future__ import annotations

from typing import Any

from ...core.storage.repo_store import get_index
from .local_backend import is_test_file_path, VALID_RELATION_TYPES


async def impact_tool(backend: Any, repo: dict[str, Any], params: dict[str, Any]) -> Any:
    await backend.ensure_initialized(repo["id"])
    target = params.get("target", "")
    direction = params.get("direction", "upstream")
    max_depth = params.get("maxDepth", 3)
    raw_rel = params.get("relationTypes", [])
    rel_types = [t for t in raw_rel if t in VALID_RELATION_TYPES] if raw_rel else list(VALID_RELATION_TYPES)
    include_tests = params.get("includeTests", False)
    min_confidence = params.get("minConfidence", 0.0)

    index = get_index(repo["id"])

    # Find the target
    targets = index.find_by_name(target)
    if not targets:
        return {"error": f"Target '{target}' not found"}

    sym = targets[0]
    sym_id = sym.id

    # BFS direction mapping
    bfs_dir = "incoming" if direction == "upstream" else "outgoing"

    impacted = index.bfs(
        sym_id,
        direction=bfs_dir,
        rel_types=rel_types,
        max_depth=max_depth,
        min_confidence=min_confidence,
    )

    # Filter tests if needed
    if not include_tests:
        impacted = [i for i in impacted if not is_test_file_path(i.get("filePath", ""))]

    # Group by depth
    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in impacted:
        grouped.setdefault(item["depth"], []).append(item)

    direct_count = len(grouped.get(1, []))

    # Affected processes
    affected_processes: list[dict[str, Any]] = []
    process_hits: dict[str, dict[str, Any]] = {}
    for item in impacted:
        procs = index.get_processes_for_node(item["id"])
        for p in procs:
            pid = p["id"]
            if pid not in process_hits:
                process_hits[pid] = {"name": p["label"], "hits": 0, "broken_at_step": p["step"], "step_count": p["stepCount"]}
            process_hits[pid]["hits"] += 1
            if p["step"] < process_hits[pid]["broken_at_step"]:
                process_hits[pid]["broken_at_step"] = p["step"]
    affected_processes = sorted(process_hits.values(), key=lambda x: -x["hits"])[:20]

    # Affected modules
    affected_modules: list[dict[str, Any]] = []
    module_hits: dict[str, int] = {}
    for item in impacted:
        comm = index.get_community_for_node(item["id"])
        if comm:
            label = comm["label"]
            module_hits[label] = module_hits.get(label, 0) + 1
    affected_modules = [{"name": k, "hits": v} for k, v in sorted(module_hits.items(), key=lambda x: -x[1])][:20]

    # Risk
    pc = len(affected_processes)
    mc = len(affected_modules)
    risk = "LOW"
    if direct_count >= 30 or pc >= 5 or mc >= 5 or len(impacted) >= 200:
        risk = "CRITICAL"
    elif direct_count >= 15 or pc >= 3 or mc >= 3 or len(impacted) >= 100:
        risk = "HIGH"
    elif direct_count >= 5 or len(impacted) >= 30:
        risk = "MEDIUM"

    return {
        "target": {"id": sym_id, "name": sym.name, "filePath": sym.file_path},
        "direction": direction,
        "impactedCount": len(impacted),
        "risk": risk,
        "summary": {"direct": direct_count, "processes_affected": pc, "modules_affected": mc},
        "affected_processes": affected_processes,
        "affected_modules": affected_modules,
        "byDepth": grouped,
    }
