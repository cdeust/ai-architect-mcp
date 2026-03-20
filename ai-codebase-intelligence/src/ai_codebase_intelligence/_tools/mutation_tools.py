"""Mutation MCP tools — rename, cypher.

rename is destructive (modifies files). cypher is read-only (writes blocked).
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
    name="ai_architect_codebase_rename",
    description=(
        "Multi-file coordinated rename using the knowledge graph + text search. "
        "Finds all references via graph (high confidence) and regex text search "
        "(lower confidence). Preview by default (dry_run=true)."
    ),
)
async def tool_rename(
    new_name: str,
    symbol_name: str = "",
    symbol_uid: str = "",
    dry_run: bool = True,
    repo: str = "",
) -> str:
    """Rename a symbol across the codebase.

    Args:
        new_name: The new name for the symbol.
        symbol_name: Current symbol name to rename.
        symbol_uid: Direct symbol UID from prior results.
        dry_run: Preview edits without modifying files (default: true).
        repo: Repository name.
    """
    backend = _get_backend()
    result = await backend.call_tool("rename", {
        "new_name": new_name, "symbol_name": symbol_name,
        "symbol_uid": symbol_uid, "dry_run": dry_run,
        "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Run detect_changes() to verify no unexpected side effects."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_cypher",
    description=(
        "Execute SQL query against the code knowledge graph. "
        "Tables: nodes (id, label, name, file_path, content), "
        "relationships (source_id, target_id, type, confidence). "
        "Write operations are blocked."
    ),
)
async def tool_cypher(query: str, repo: str = "") -> str:
    """Execute read-only SQL query.

    Args:
        query: SQL query to execute.
        repo: Repository name.
    """
    backend = _get_backend()
    result = await backend.call_tool("cypher", {
        "query": query, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Use context(name: \"<name>\") to explore a result symbol."
    return json.dumps(result, indent=2) + hint
