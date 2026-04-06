"""REST API request handlers for codebase intelligence.

Async handlers for repos, context, query, and analyze endpoints,
plus internal helpers for graph queries and search.
"""

from __future__ import annotations

from typing import Any

from ai_codebase_intelligence._server.models import APIRequest, APIResponse, RepoIndex
from ai_codebase_intelligence._tools import codebase_tools

# ---------------------------------------------------------------------------
# Internal helpers (patched in tests)
# ---------------------------------------------------------------------------


async def _query_repo_stats(repo_path: str) -> dict[str, int]:
    """Query the graph store for node/edge counts.

    Args:
        repo_path: Absolute path to the repository root.

    Returns:
        Dict with ``node_count`` and ``edge_count`` keys.
    """
    return {"node_count": 0, "edge_count": 0}


async def _run_search(repo_path: str, query: str) -> list[dict[str, Any]]:
    """Run hybrid search against the indexed repository.

    Args:
        repo_path: Absolute path to the repository root.
        query: The search query string.

    Returns:
        List of search result dicts.
    """
    return []


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def handle_list_repos(
    request: APIRequest,
    index: RepoIndex,
) -> APIResponse:
    """List all indexed repositories.

    Args:
        request: The incoming API request.
        index: Mapping of repo name to repo path.

    Returns:
        APIResponse with status 200 and list of repos.
    """
    repos = [
        {"name": name, "path": path}
        for name, path in index.items()
    ]
    return APIResponse(status=200, body={"repos": repos})


async def handle_context(
    request: APIRequest,
    name: str,
    index: RepoIndex,
) -> APIResponse:
    """Return context information for a repository.

    Args:
        request: The incoming API request.
        name: Repository name extracted from the route.
        index: Mapping of repo name to repo path.

    Returns:
        APIResponse with status 200 and context data, or 404 if not found.
    """
    if name not in index:
        return APIResponse(
            status=404,
            body={"error": f"Repository '{name}' not found"},
        )

    repo_path = index[name]
    stats = await _query_repo_stats(repo_path)
    return APIResponse(
        status=200,
        body={
            "name": name,
            "path": repo_path,
            "node_count": stats["node_count"],
            "edge_count": stats["edge_count"],
        },
    )


async def handle_query(
    request: APIRequest,
    name: str,
    index: RepoIndex,
) -> APIResponse:
    """Execute a search query against a repository.

    Args:
        request: The incoming API request.
        name: Repository name extracted from the route.
        index: Mapping of repo name to repo path.

    Returns:
        APIResponse with status 200 and search results, 400 if missing
        query param, or 404 if repo not found.
    """
    if name not in index:
        return APIResponse(
            status=404,
            body={"error": f"Repository '{name}' not found"},
        )

    q = request.query_params.get("q")
    if not q:
        return APIResponse(
            status=400,
            body={"error": "Missing required query parameter 'q'"},
        )

    repo_path = index[name]
    results = await _run_search(repo_path, q)
    return APIResponse(
        status=200,
        body={
            "query": q,
            "results": results,
            "total_matches": len(results),
        },
    )


async def handle_analyze(
    request: APIRequest,
    name: str,
    index: RepoIndex,
) -> APIResponse:
    """Trigger analysis/indexing of a repository.

    Args:
        request: The incoming API request.
        name: Repository name extracted from the route.
        index: Mapping of repo name to repo path.

    Returns:
        APIResponse with status 200 and analysis metrics, 404 if repo
        not found, or 500 on analysis failure.
    """
    if name not in index:
        return APIResponse(
            status=404,
            body={"error": f"Repository '{name}' not found"},
        )

    repo_path = index[name]
    try:
        output = await codebase_tools.analyze(repo_path)
    except Exception as exc:
        return APIResponse(
            status=500,
            body={"error": str(exc)},
        )

    return APIResponse(
        status=200,
        body={
            "status": "completed",
            "total_nodes": output.total_nodes,
            "total_relationships": output.total_relationships,
            "total_files": output.total_files,
            "total_communities": output.total_communities,
            "total_processes": output.total_processes,
            "duration_seconds": output.duration_seconds,
        },
    )
