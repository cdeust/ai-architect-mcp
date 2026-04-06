"""Backend: co-change detection — Gall et al. 1998 + Zimmermann et al. 2005."""

from __future__ import annotations

from typing import Any

from ...core.storage.repo_store import get_index


async def cochange_tool(
    backend: Any,
    repo: dict[str, Any],
    params: dict[str, Any],
) -> Any:
    """Query co-change pairs for a target file.

    Args:
        backend: LocalBackend instance.
        repo: Resolved repo dict.
        params: Tool params with target file path.

    Returns:
        Co-change pairs with support and confidence.
    """
    await backend.ensure_initialized(repo["id"])
    index = get_index(repo["id"])
    target = params.get("target", "")

    if not target:
        return _all_cochange_pairs(index)

    return _cochange_for_file(index, target)


def _cochange_for_file(index: Any, target: str) -> dict[str, Any]:
    """Get co-change partners for a specific file."""
    file_nodes = [
        (nid, n) for nid, n in index._nodes.items()
        if n.label.value == "File"
        and n.file_path == target
    ]
    if not file_nodes:
        return {"error": f"File '{target}' not found in index"}

    file_id = file_nodes[0][0]
    partners: list[dict[str, Any]] = []

    for target_id, rel in index._out.get(file_id, []):
        if rel.relationship_type.value != "CO_CHANGES_WITH":
            continue
        partner = index._nodes.get(target_id)
        fp = partner.file_path if partner else ""
        partners.append({
            "filePath": fp,
            "confidence": rel.confidence,
            "reason": rel.properties.get("reason", ""),
        })

    partners.sort(key=lambda p: p["confidence"], reverse=True)
    return {
        "target": target,
        "coupledFiles": partners[:50],
        "citation": "Gall et al. 1998, ICSM; Zimmermann et al. 2005, IEEE TSE",
    }


def _all_cochange_pairs(index: Any) -> dict[str, Any]:
    """Get all co-change pairs across the repo."""
    pairs: list[dict[str, Any]] = []
    seen: set[str] = set()

    for node_id, edges in index._out.items():
        for target_id, rel in edges:
            if rel.relationship_type.value != "CO_CHANGES_WITH":
                continue
            pair_key = f"{min(node_id, target_id)}-{max(node_id, target_id)}"
            if pair_key in seen:
                continue
            seen.add(pair_key)

            src = index._nodes.get(node_id)
            tgt = index._nodes.get(target_id)
            pairs.append({
                "fileA": src.file_path if src else "",
                "fileB": tgt.file_path if tgt else "",
                "confidence": rel.confidence,
            })

    pairs.sort(key=lambda p: p["confidence"], reverse=True)
    return {
        "pairs": pairs[:100],
        "totalPairs": len(pairs),
        "citation": "Gall et al. 1998, ICSM; Zimmermann et al. 2005, IEEE TSE",
    }
