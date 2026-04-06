"""Backend: churn metrics — Nagappan & Ball 2005."""

from __future__ import annotations

from typing import Any

from ...core.analysis.churn_metrics import calculate_churn_metrics
from ...core.storage.repo_store import get_index


async def churn_tool(
    backend: Any,
    repo: dict[str, Any],
    params: dict[str, Any],
) -> Any:
    """Compute churn metrics for files in the repository.

    Args:
        backend: LocalBackend instance.
        repo: Resolved repo dict.
        params: Tool params with optional target and max_commits.

    Returns:
        Churn metrics per file and repo-level summary.
    """
    await backend.ensure_initialized(repo["id"])
    index = get_index(repo["id"])
    target = params.get("target", "all")
    max_commits = params.get("max_commits", 500)

    file_paths: list[str] = []
    for node_id, node in index._nodes.items():
        if node.label.value != "File":
            continue
        fp = node.file_path
        if not fp:
            continue
        if target != "all" and fp != target:
            continue
        file_paths.append(fp)

    result = calculate_churn_metrics(
        repo["repoPath"], file_paths, max_commits,
    )
    return result
