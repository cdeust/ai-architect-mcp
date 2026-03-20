"""FastMCP singleton for the Codebase Intelligence MCP server.

Extracted into its own module to avoid the __main__ double-import trap.
All tool modules import `mcp` from here instead of from server.py.
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("ai-codebase-intelligence")
