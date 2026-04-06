"""REST API routing and request handling for codebase intelligence.

Provides route matching and dispatches to async handlers for repos,
context, query, and analyze endpoints. Re-exports data models and
handlers for backward compatibility.
"""

from __future__ import annotations

from ai_codebase_intelligence._server.handlers import (
    _query_repo_stats,
    _run_search,
    handle_analyze,
    handle_context,
    handle_list_repos,
    handle_query,
)
from ai_codebase_intelligence._server.models import (
    APIRequest,
    APIResponse,
    RepoIndex,
)

# ---------------------------------------------------------------------------
# Route constants
# ---------------------------------------------------------------------------

ROUTE_CONTEXT = "/repos/{name}/context"
ROUTE_QUERY = "/repos/{name}/query"
ROUTE_ANALYZE = "/repos/{name}/analyze"

# ---------------------------------------------------------------------------
# Route matching
# ---------------------------------------------------------------------------


def _match_route(path: str, pattern: str) -> dict[str, str] | None:
    """Match a request path against a route pattern.

    Supports ``{param}`` placeholders. Returns extracted params on match,
    or ``None`` when the path does not match.

    Args:
        path: The actual request path (e.g. ``/repos/myrepo/context``).
        pattern: The route pattern (e.g. ``/repos/{name}/context``).

    Returns:
        A dict of extracted path parameters, or None if no match.
    """
    path_parts = path.strip("/").split("/")
    pattern_parts = pattern.strip("/").split("/")

    if len(path_parts) != len(pattern_parts):
        return None

    params: dict[str, str] = {}
    for p_part, r_part in zip(path_parts, pattern_parts):
        if r_part.startswith("{") and r_part.endswith("}"):
            param_name = r_part[1:-1]
            params[param_name] = p_part
        elif p_part != r_part:
            return None

    return params


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

_ROUTES = [
    ("GET", "/repos", None),
    ("GET", ROUTE_CONTEXT, "context"),
    ("GET", ROUTE_QUERY, "query"),
    ("POST", ROUTE_ANALYZE, "analyze"),
]


async def route_request(
    request: APIRequest,
    index: RepoIndex,
) -> APIResponse:
    """Dispatch an API request to the matching handler.

    Args:
        request: The incoming API request.
        index: Mapping of repo name to repo path.

    Returns:
        APIResponse from the matched handler, or 404.
    """
    for method, pattern, handler_key in _ROUTES:
        if request.method != method:
            continue
        params = _match_route(request.path, pattern)
        if params is None:
            continue

        if handler_key is None:
            return await handle_list_repos(request, index)

        name = params.get("name", "")
        if handler_key == "context":
            return await handle_context(request, name, index)
        if handler_key == "query":
            return await handle_query(request, name, index)
        if handler_key == "analyze":
            return await handle_analyze(request, name, index)

    return APIResponse(status=404, body={"error": "Not found"})
