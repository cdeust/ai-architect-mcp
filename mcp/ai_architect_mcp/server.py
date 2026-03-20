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

import logging

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
from ai_architect_mcp._tools import pipeline_tools  # noqa: F401, E402

logger = logging.getLogger(__name__)


def _init_observability() -> None:
    """Initialize the observability pipeline at server startup.

    Creates the composite adapter (file + SSE) and sets it as the
    global observability port so every @observe_tool_call decorator,
    HOR rule emission, and artifact save emits real-time events.

    The SSE adapter is started asynchronously on first use via
    the event loop. The JSONL file adapter writes immediately.
    """
    from ai_architect_mcp._observability.instrumentation import (
        set_observability_port,
    )
    from ai_architect_mcp._tools._composition import get_root

    root = get_root()
    port = root.create_observability(enable_sse=True)
    set_observability_port(port)
    logger.info("Observability pipeline initialized (file + SSE)")


def main() -> None:
    """Start the AI Architect MCP server."""
    _init_observability()
    mcp.run()


if __name__ == "__main__":
    main()
