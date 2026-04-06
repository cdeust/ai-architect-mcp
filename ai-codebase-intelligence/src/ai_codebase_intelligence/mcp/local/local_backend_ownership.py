"""Backend: ownership analysis — Bird et al. 2011."""

from __future__ import annotations

from typing import Any

from ...core.storage.repo_store import get_index


async def ownership_tool(
    backend: Any,
    repo: dict[str, Any],
    params: dict[str, Any],
) -> Any:
    """Query ownership data from AUTHORED_BY edges.

    Args:
        backend: LocalBackend instance.
        repo: Resolved repo dict.
        params: Tool params with optional target file path.

    Returns:
        Ownership data with per-file metrics.
    """
    await backend.ensure_initialized(repo["id"])
    index = get_index(repo["id"])
    target = params.get("target", "all")

    files: list[dict[str, Any]] = []
    for node_id, node in index._nodes.items():
        if node.label.value != "File":
            continue
        fp = node.file_path
        if not fp:
            continue
        if target != "all" and fp != target:
            continue

        authors = _get_file_authors(index, node_id)
        if not authors:
            continue

        total_conf = sum(a["fraction"] for a in authors)
        top = authors[0]
        minor_count = sum(1 for a in authors if a["fraction"] < 0.05)

        files.append({
            "filePath": fp,
            "ownershipRatio": round(top["fraction"], 4) if total_conf > 0 else 0.0,
            "minorContributors": minor_count,
            "topContributor": top["name"],
            "authorCount": len(authors),
            "authors": authors[:10],
        })

    files.sort(key=lambda f: f["ownershipRatio"])
    return {
        "files": files[:100],
        "totalFiles": len(files),
        "citation": "Bird et al. 2011, ESEC/FSE",
    }


def _get_file_authors(
    index: Any,
    file_id: str,
) -> list[dict[str, Any]]:
    """Get authors for a file via AUTHORED_BY edges."""
    authors: list[dict[str, Any]] = []
    for target_id, rel in index._out.get(file_id, []):
        if rel.relationship_type.value != "AUTHORED_BY":
            continue
        contrib = index._nodes.get(target_id)
        if not contrib:
            continue
        authors.append({
            "name": contrib.name,
            "email": contrib.properties.get("email", ""),
            "fraction": rel.confidence,
        })
    return sorted(authors, key=lambda a: a["fraction"], reverse=True)
