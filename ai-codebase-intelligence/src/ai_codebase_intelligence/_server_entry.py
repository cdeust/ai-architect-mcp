"""FastMCP server entry — imports _app singleton + all tool modules.

Tools exposed (11 total):
  Indexing (atomic, Claude-orchestrated):
    scan, parse, store, analyze (convenience)
  Query (read-only):
    query, context, impact
  Analysis (read-only):
    detect_changes, list_repos
  Mutation (destructive):
    rename, cypher
"""

from __future__ import annotations

import logging

from ai_codebase_intelligence._app import mcp  # noqa: F401

# Import tool modules to trigger @mcp.tool registration
from ai_codebase_intelligence._tools import indexing_tools  # noqa: F401
from ai_codebase_intelligence._tools import query_tools  # noqa: F401
from ai_codebase_intelligence._tools import analysis_tools  # noqa: F401
from ai_codebase_intelligence._tools import mutation_tools  # noqa: F401


def main() -> None:
    """Start the MCP server on stdio transport."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()
