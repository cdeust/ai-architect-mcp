"""Direct CLI tool commands — 1:1 port of gitnexus cli/tool.js."""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

_backend: Any = None


async def _get_backend() -> Any:
    global _backend
    if _backend is not None:
        return _backend
    from ..mcp.local.local_backend import LocalBackend
    _backend = LocalBackend()
    ok = await _backend.init()
    if not ok:
        print("No indexed repositories found. Run: analyze", file=sys.stderr)
        sys.exit(1)
    return _backend


def _output(data: Any) -> None:
    text = data if isinstance(data, str) else json.dumps(data, indent=2)
    sys.stderr.write(text + "\n")


def query_command(query_text: str, repo: str = "", limit: int = 5, content: bool = False) -> None:
    if not query_text.strip():
        print("Usage: query <search_query>", file=sys.stderr)
        sys.exit(1)

    async def run() -> None:
        backend = await _get_backend()
        result = await backend.call_tool("query", {
            "query": query_text, "limit": limit,
            "include_content": content, "repo": repo or None,
        })
        _output(result)

    asyncio.run(run())


def context_command(name: str = "", uid: str = "", file_path: str = "", repo: str = "", content: bool = False) -> None:
    if not name.strip() and not uid:
        print("Usage: context <symbol_name> [--uid <uid>]", file=sys.stderr)
        sys.exit(1)

    async def run() -> None:
        backend = await _get_backend()
        result = await backend.call_tool("context", {
            "name": name or None, "uid": uid or None,
            "file_path": file_path or None,
            "include_content": content, "repo": repo or None,
        })
        _output(result)

    asyncio.run(run())


def impact_command(target: str, direction: str = "upstream", depth: int = 3, repo: str = "") -> None:
    if not target.strip():
        print("Usage: impact <symbol_name> [--direction upstream|downstream]", file=sys.stderr)
        sys.exit(1)

    async def run() -> None:
        backend = await _get_backend()
        result = await backend.call_tool("impact", {
            "target": target, "direction": direction,
            "maxDepth": depth, "repo": repo or None,
        })
        _output(result)

    asyncio.run(run())


def cypher_command(query: str, repo: str = "") -> None:
    if not query.strip():
        print("Usage: cypher <cypher_query>", file=sys.stderr)
        sys.exit(1)

    async def run() -> None:
        backend = await _get_backend()
        result = await backend.call_tool("cypher", {
            "query": query, "repo": repo or None,
        })
        _output(result)

    asyncio.run(run())
