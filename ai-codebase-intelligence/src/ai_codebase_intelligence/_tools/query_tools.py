"""Query, context, and impact MCP tools.

Read-only tools for searching and navigating the knowledge graph.
All depend on ports via the composition root — never on concrete adapters.
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
    name="ai_architect_codebase_query",
    description=(
        "Query the code knowledge graph for execution flows related to a concept. "
        "Returns processes (call chains) ranked by relevance, each with its symbols "
        "and file locations. Hybrid ranking: BM25 keyword + process tracing."
    ),
)
async def tool_query(
    query: str,
    repo: str = "",
    limit: int = 5,
    max_symbols: int = 10,
    include_content: bool = False,
) -> str:
    """Search the codebase for execution flows.

    Args:
        query: Natural language or keyword search query.
        repo: Repository name. Omit if only one indexed.
        limit: Max processes to return.
        max_symbols: Max symbols per process.
        include_content: Include full symbol source code.
    """
    backend = _get_backend()
    result = await backend.call_tool("query", {
        "query": query, "repo": repo or None,
        "limit": limit, "max_symbols": max_symbols,
        "include_content": include_content,
    })
    hint = "\n\n---\n**Next:** Use context(name: \"<symbol>\") for 360-degree view."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_context",
    description=(
        "360-degree view of a single code symbol. Shows categorized "
        "incoming/outgoing references (calls, imports, extends, implements), "
        "process participation, and file location."
    ),
)
async def tool_context(
    name: str = "",
    uid: str = "",
    file_path: str = "",
    include_content: bool = False,
    repo: str = "",
) -> str:
    """Get full context for a symbol.

    Args:
        name: Symbol name (e.g., 'validateUser').
        uid: Direct symbol UID from prior results.
        file_path: File path to disambiguate common names.
        include_content: Include full source code.
        repo: Repository name.
    """
    backend = _get_backend()
    result = await backend.call_tool("context", {
        "name": name, "uid": uid, "file_path": file_path,
        "include_content": include_content, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Use impact(target: \"<name>\", direction: \"upstream\") for blast radius."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_impact",
    description=(
        "Analyze the blast radius of changing a code symbol. Returns affected "
        "symbols grouped by depth, risk assessment, affected execution flows, "
        "and affected modules. d=1: WILL BREAK, d=2: LIKELY AFFECTED, d=3: MAY NEED TESTING."
    ),
)
async def tool_impact(
    target: str,
    direction: str = "upstream",
    maxDepth: int = 3,
    repo: str = "",
) -> str:
    """Blast radius analysis.

    Args:
        target: Name of function, class, or file to analyze.
        direction: upstream (dependants) or downstream (dependencies).
        maxDepth: Max relationship depth (default: 3).
        repo: Repository name.
    """
    backend = _get_backend()
    result = await backend.call_tool("impact", {
        "target": target, "direction": direction,
        "maxDepth": maxDepth, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Review d=1 items (WILL BREAK). Use context() on high-risk symbols."
    return json.dumps(result, indent=2) + hint
