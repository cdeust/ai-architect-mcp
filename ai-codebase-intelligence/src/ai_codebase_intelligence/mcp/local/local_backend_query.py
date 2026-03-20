"""Query tool — uses SQLite FTS5 + GraphIndex instead of KuzuDB."""
from __future__ import annotations

from typing import Any

from ...core.storage.repo_store import search_fts, get_index


async def query_tool(backend: Any, repo: dict[str, Any], params: dict[str, Any]) -> Any:
    query_str = (params.get("query") or "").strip()
    if not query_str:
        return {"error": "query parameter is required and cannot be empty."}

    await backend.ensure_initialized(repo["id"])
    process_limit = params.get("limit", 5)
    max_symbols = params.get("max_symbols", 10)
    search_limit = process_limit * max_symbols

    # Step 1: FTS5 search
    fts_results = search_fts(repo["id"], query_str, search_limit)
    if not fts_results:
        return {"processes": [], "process_symbols": [], "definitions": []}

    index = get_index(repo["id"])

    # Step 2: RRF scoring
    score_map: dict[str, dict[str, Any]] = {}
    for i, r in enumerate(fts_results):
        key = r["id"]
        rrf = 1.0 / (60 + i)
        score_map[key] = {"score": rrf, "data": r}

    merged = sorted(score_map.items(), key=lambda x: x[1]["score"], reverse=True)[:search_limit]

    # Step 3: Trace to processes
    process_map: dict[str, dict[str, Any]] = {}
    definitions: list[dict[str, Any]] = []

    for _, item in merged:
        sym = item["data"]
        node_id = sym["id"]

        procs = index.get_processes_for_node(node_id)

        symbol_entry = {
            "id": node_id, "name": sym.get("name", ""),
            "type": sym.get("label", ""), "filePath": sym.get("filePath", ""),
            "startLine": sym.get("startLine"), "endLine": sym.get("endLine"),
        }

        if not procs:
            definitions.append(symbol_entry)
        else:
            for proc in procs:
                pid = proc["id"]
                if pid not in process_map:
                    process_map[pid] = {
                        "id": pid, "label": proc["label"],
                        "heuristicLabel": proc["label"],
                        "stepCount": proc["stepCount"],
                        "totalScore": 0, "symbols": [],
                    }
                process_map[pid]["totalScore"] += item["score"]
                process_map[pid]["symbols"].append({
                    **symbol_entry, "process_id": pid, "step_index": proc["step"],
                })

    ranked = sorted(process_map.values(), key=lambda p: p["totalScore"], reverse=True)[:process_limit]

    processes = [
        {"id": p["id"], "summary": p["heuristicLabel"],
         "priority": round(p["totalScore"], 3),
         "symbol_count": len(p["symbols"]),
         "step_count": p["stepCount"]}
        for p in ranked
    ]

    seen: set[str] = set()
    process_symbols: list[dict[str, Any]] = []
    for p in ranked:
        for s in p["symbols"][:max_symbols]:
            if s["id"] not in seen:
                seen.add(s["id"])
                process_symbols.append(s)

    return {
        "processes": processes,
        "process_symbols": process_symbols,
        "definitions": definitions[:20],
    }
