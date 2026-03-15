"""AI Architect MCP Server entry point.

FastMCP server exposing five tool groups (43 tools total):
- Verification: 5 evaluation algorithms + 2 consensus methods + 64 HOR rules
- Prompting: 5 enhancement algorithms + 15 thinking strategies
- Context: StageContext load/save/query + HandoffDocument management
- Scoring: compound scoring + dependency propagation
- Adapters: Git, Xcode, GitHub, FileSystem operations via port interfaces
- Interview: PRD dimension scoring (D1-D10) + gate evaluation
- Memory: session state, experience patterns, audit log, context budget

All tools are prefixed with ai_architect_ and annotated with:
readOnlyHint, destructiveHint, idempotentHint, openWorldHint.
"""

from __future__ import annotations

from ai_architect_mcp._app import mcp  # noqa: F401 — re-exported for backward compat

# Import tool modules to trigger @mcp.tool() registration.
# Each module decorates its functions with @mcp.tool() on import.
from ai_architect_mcp._tools import verification_tools  # noqa: F401, E402
from ai_architect_mcp._tools import hor_tools  # noqa: F401, E402
from ai_architect_mcp._tools import prompting_tools  # noqa: F401, E402
from ai_architect_mcp._tools import context_tools  # noqa: F401, E402
from ai_architect_mcp._tools import scoring_tools  # noqa: F401, E402
from ai_architect_mcp._tools import adapter_tools  # noqa: F401, E402
from ai_architect_mcp._tools import interview_tools  # noqa: F401, E402
from ai_architect_mcp._tools import memory_tools  # noqa: F401, E402
from ai_architect_mcp._tools import xcode_tools  # noqa: F401, E402


def main() -> None:
    """Start the AI Architect MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
