"""Context tools — load, save, query stage artifacts and handoff documents."""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._context.handoff import HandoffDocument
from ai_architect_mcp._context.stage_context import StageContext
from ai_architect_mcp.server import mcp

_context: StageContext | None = None


def _get_context() -> StageContext:
    """Get or create the singleton stage context."""
    global _context
    if _context is None:
        _context = StageContext()
    return _context


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_load_context(
    stage_id: int,
    finding_id: str,
) -> dict[str, Any]:
    """Load a stage artifact for a finding.

    Args:
        stage_id: Pipeline stage number (0-10).
        finding_id: Unique finding identifier.

    Returns:
        The stage artifact as a dictionary.
    """
    ctx = _get_context()
    return await ctx.load(stage_id, finding_id)


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
)
async def ai_architect_save_context(
    stage_id: int,
    finding_id: str,
    artifact: dict[str, Any],
) -> dict[str, str]:
    """Save a stage artifact for a finding.

    Args:
        stage_id: Pipeline stage number (0-10).
        finding_id: Unique finding identifier.
        artifact: The artifact data to save.

    Returns:
        Confirmation with stage_id and finding_id.
    """
    ctx = _get_context()
    await ctx.save(stage_id, finding_id, artifact)
    return {"status": "saved", "stage_id": str(stage_id), "finding_id": finding_id}


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_query_context(
    finding_id: str,
    query: str,
) -> list[dict[str, Any]]:
    """Query artifacts across all stages for a finding.

    Args:
        finding_id: Unique finding identifier.
        query: Search query string.

    Returns:
        List of matching artifact fragments.
    """
    ctx = _get_context()
    return await ctx.query(finding_id, query)


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_create_handoff(
    completed: list[str],
    in_progress: list[str],
    blocked: list[str],
    next_actions: list[str],
    session_id: str,
) -> dict[str, str]:
    """Create a handoff document for session boundary.

    Args:
        completed: Completed tasks.
        in_progress: In-progress tasks.
        blocked: Blocked tasks.
        next_actions: Next session priorities.
        session_id: Session identifier.

    Returns:
        Handoff document as markdown.
    """
    from datetime import datetime, timezone

    doc = HandoffDocument(
        completed=completed,
        in_progress=in_progress,
        blocked=blocked,
        next_actions=next_actions,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"markdown": doc.to_markdown(), "session_id": session_id}


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_load_handoff(
    markdown: str,
) -> dict[str, Any]:
    """Parse a handoff document from markdown.

    Args:
        markdown: Handoff document in markdown format.

    Returns:
        HandoffDocument as a dictionary.
    """
    doc = HandoffDocument.from_markdown(markdown)
    return doc.model_dump(mode="json")
