from __future__ import annotations

import asyncio
import sys


def mcp_command() -> None:
    from ..mcp.server import backend, mcp

    async def start() -> None:
        await backend.init()
        repos = await backend.list_repos()
        if not repos:
            print("No indexed repos yet. Run `analyze` in a git repo.", file=sys.stderr)
        else:
            names = ", ".join(r["name"] for r in repos)
            print(f"MCP server starting with {len(repos)} repo(s): {names}", file=sys.stderr)

    asyncio.run(start())
    mcp.run()
