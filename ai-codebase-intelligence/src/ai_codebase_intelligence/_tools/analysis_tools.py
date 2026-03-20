"""Analysis MCP tools — detect_changes, list_repos.

Read-only tools. Indexing is handled by indexing_tools.py.
"""

from __future__ import annotations

import json

from .._app import mcp
from ..mcp.local.local_backend import LocalBackend

_backend: LocalBackend | None = None


def _get_backend() -> LocalBackend:
    global _backend
    if _backend is None:
        _backend = LocalBackend()
    return _backend


@mcp.tool(
    name="ai_architect_codebase_detect_changes",
    description=(
        "Analyze code changes and find affected execution flows. "
        "Maps changed files to indexed symbols, then traces which "
        "processes are impacted. Use before committing."
    ),
)
async def tool_detect_changes(
    repo: str = "",
    scope: str = "unstaged",
    base_ref: str = "",
) -> str:
    """Detect symbols affected by git changes.

    Args:
        repo: Repository name. Omit if only one indexed.
        scope: What to analyze: unstaged, staged, all, or compare.
        base_ref: Branch/commit for compare scope.
    """
    backend = _get_backend()
    result = await backend.call_tool("detect_changes", {
        "scope": scope, "base_ref": base_ref, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Review affected processes. Use context() on high-risk symbols."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_list_repos",
    description="List all indexed repositories with stats.",
)
async def tool_list_repos() -> str:
    """List all indexed repositories."""
    backend = _get_backend()
    result = await backend.call_tool("list_repos", {})
    hint = "\n\n---\n**Next:** READ codebase://repo/{name}/context for any repo above."
    return json.dumps(result, indent=2) + hint
