"""Context tools — load, save, query stage artifacts and handoff documents."""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._context.handoff import HandoffDocument
from ai_architect_mcp._context.stage_context import StageContext
from ai_architect_mcp._app import mcp
from ai_architect_mcp._observability.instrumentation import observe_tool_call

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
@observe_tool_call
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
@observe_tool_call
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
@observe_tool_call
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
@observe_tool_call
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
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_emit_ooda_checkpoint(
    stage_id: int,
    phase: str,
    decision: str,
    confidence: float = 1.0,
    session_id: str = "",
) -> dict[str, str]:
    """Emit an OODA checkpoint event at a decision point.

    Called by Claude at Observe-Orient-Decide-Act decision points
    during pipeline execution. Provides real-time visibility into
    the reasoning process.

    Args:
        stage_id: Current pipeline stage (0-10).
        phase: OODA phase — observe, orient, decide, or act.
        decision: Description of the decision or observation.
        confidence: Confidence level (0.0-1.0).
        session_id: Current session identifier.

    Returns:
        Confirmation with event details.
    """
    import uuid

    from ai_architect_mcp._observability.event_types import (
        EventType,
        PipelineEvent,
    )
    from ai_architect_mcp._observability.instrumentation import (
        get_observability_port,
    )

    port = get_observability_port()
    if port is not None:
        await port.emit(PipelineEvent(
            event_id=f"oc-{uuid.uuid4().hex[:12]}",
            event_type=EventType.OODA_CHECKPOINT,
            stage_id=stage_id,
            session_id=session_id,
            message=f"OODA {phase}: {decision}",
            metadata={
                "phase": phase,
                "decision": decision,
                "confidence": str(confidence),
            },
        ))

    return {
        "status": "emitted",
        "stage_id": str(stage_id),
        "phase": phase,
        "decision": decision,
    }


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_emit_thinking_step(
    stage_id: int,
    title: str,
    reasoning: str,
    session_id: str = "",
) -> dict[str, str]:
    """Emit a thinking step event for brain-map visualization.

    Call this at every significant reasoning point during pipeline
    execution: analyzing input, evaluating options, interpreting
    results, planning next steps. Each call creates a visible node
    in the brain-map graph showing the agent's cognitive process.

    Args:
        stage_id: Current pipeline stage (0-10).
        title: Short title — what the agent is thinking about.
        reasoning: The reasoning chain, analysis, or observation.
        session_id: Current session identifier.

    Returns:
        Confirmation with event details.
    """
    from ai_architect_mcp._observability.instrumentation import (
        emit_thinking_step,
    )
    await emit_thinking_step(stage_id, title, reasoning, session_id)
    return {
        "status": "emitted",
        "stage_id": str(stage_id),
        "title": title,
    }


@mcp.tool(
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
async def ai_architect_emit_decision(
    stage_id: int,
    title: str,
    options_considered: str,
    chosen: str,
    rationale: str,
    session_id: str = "",
) -> dict[str, str]:
    """Emit a decision event for brain-map visualization.

    Call this when the agent makes a significant decision during
    pipeline execution: choosing a strategy, selecting an algorithm,
    deciding to retry or proceed, accepting or rejecting an artifact.
    Each call creates a decision node in the brain-map graph.

    Args:
        stage_id: Current pipeline stage (0-10).
        title: What decision was made.
        options_considered: Alternatives that were evaluated.
        chosen: The option that was selected.
        rationale: Why this option was chosen over alternatives.
        session_id: Current session identifier.

    Returns:
        Confirmation with event details.
    """
    from ai_architect_mcp._observability.instrumentation import (
        emit_decision,
    )
    await emit_decision(
        stage_id, title, options_considered, chosen, rationale, session_id
    )
    return {
        "status": "emitted",
        "stage_id": str(stage_id),
        "title": title,
        "chosen": chosen,
    }


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
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
