"""Context tool — uses GraphIndex instead of KuzuDB Cypher."""
from __future__ import annotations

from typing import Any

from ...core.storage.repo_store import get_index


async def context_tool(backend: Any, repo: dict[str, Any], params: dict[str, Any]) -> Any:
    await backend.ensure_initialized(repo["id"])
    name = params.get("name")
    uid = params.get("uid")
    file_path = params.get("file_path")
    include_content = params.get("include_content", False)

    if not name and not uid:
        return {"error": 'Either "name" or "uid" parameter is required.'}

    index = get_index(repo["id"])

    # Step 1: Find the symbol
    if uid:
        node = index.get_node(uid)
        symbols = [node] if node else []
    else:
        candidates = index.find_by_name(name)
        if file_path:
            candidates = [n for n in candidates if file_path in n.get("properties", {}).get("filePath", "")]
        symbols = candidates[:10]

    if not symbols:
        return {"error": f"Symbol '{name or uid}' not found"}

    # Step 2: Disambiguation
    if len(symbols) > 1 and not uid:
        return {
            "status": "ambiguous",
            "message": f"Found {len(symbols)} symbols matching '{name}'. Use uid or file_path to disambiguate.",
            "candidates": [
                {
                    "uid": s["id"],
                    "name": s.get("properties", {}).get("name", ""),
                    "kind": s.get("label", ""),
                    "filePath": s.get("properties", {}).get("filePath", ""),
                    "line": s.get("properties", {}).get("startLine", 0),
                }
                for s in symbols
            ],
        }

    # Step 3: Build full context
    sym = symbols[0]
    sym_id = sym["id"]
    props = sym.get("properties", {})

    # Categorized incoming refs
    incoming_edges = index.incoming(sym_id)
    incoming: dict[str, list[dict[str, Any]]] = {}
    for src_node, rel in incoming_edges:
        rt = rel.get("type", "").lower()
        if rt not in ("calls", "imports", "extends", "implements"):
            continue
        entry = {
            "uid": src_node["id"],
            "name": src_node.get("properties", {}).get("name", ""),
            "filePath": src_node.get("properties", {}).get("filePath", ""),
            "kind": src_node.get("label", ""),
        }
        incoming.setdefault(rt, []).append(entry)

    # Categorized outgoing refs
    outgoing_edges = index.outgoing(sym_id)
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for tgt_node, rel in outgoing_edges:
        rt = rel.get("type", "").lower()
        if rt not in ("calls", "imports", "extends", "implements"):
            continue
        entry = {
            "uid": tgt_node["id"],
            "name": tgt_node.get("properties", {}).get("name", ""),
            "filePath": tgt_node.get("properties", {}).get("filePath", ""),
            "kind": tgt_node.get("label", ""),
        }
        outgoing.setdefault(rt, []).append(entry)

    # Process participation
    processes = index.get_processes_for_node(sym_id)

    result: dict[str, Any] = {
        "status": "found",
        "symbol": {
            "uid": sym_id,
            "name": props.get("name", ""),
            "kind": sym.get("label", ""),
            "filePath": props.get("filePath", ""),
            "startLine": props.get("startLine", 0),
            "endLine": props.get("endLine", 0),
        },
        "incoming": incoming,
        "outgoing": outgoing,
        "processes": [
            {"id": p["id"], "name": p["label"], "step_index": p["step"], "step_count": p["stepCount"]}
            for p in processes
        ],
    }

    if include_content and props.get("content"):
        result["symbol"]["content"] = props["content"]

    return result
