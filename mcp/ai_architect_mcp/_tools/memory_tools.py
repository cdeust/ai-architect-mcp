"""Memory tools — MCP tools for the four-layer memory model.

Exposes session state, experience patterns, audit events, and context
budget management as MCP tool endpoints.
"""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp._adapters.memory_ports import (
    AuditPort,
    ExperiencePort,
    PipelineStatePort,
)
from ai_architect_mcp._context.budget_monitor import BudgetMonitor
from ai_architect_mcp._models.audit_event import AuditEvent, AuditQuery
from ai_architect_mcp._models.experience_pattern import ExperiencePattern
from ai_architect_mcp._models.session_state import SessionState
from ai_architect_mcp._app import mcp

_composition_root: CompositionRoot | None = None


def _get_root() -> CompositionRoot:
    """Get or create the module-level composition root.

    Returns:
        Shared CompositionRoot instance.
    """
    global _composition_root
    if _composition_root is None:
        _composition_root = CompositionRoot()
    return _composition_root


def _get_pipeline_state() -> PipelineStatePort:
    """Get the pipeline state adapter.

    Returns:
        PipelineStatePort implementation.
    """
    return _get_root().create_pipeline_state()


def _get_experience() -> ExperiencePort:
    """Get the experience pattern adapter.

    Returns:
        ExperiencePort implementation.
    """
    return _get_root().create_experience()


def _get_audit() -> AuditPort:
    """Get the audit event adapter.

    Returns:
        AuditPort implementation.
    """
    return _get_root().create_audit()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_load_session_state(
    session_id: str,
) -> dict[str, Any] | None:
    """Load a pipeline session state by ID.

    Args:
        session_id: Unique session identifier.

    Returns:
        Session state as a dictionary, or None if not found.
    """
    adapter = _get_pipeline_state()
    state = await adapter.load(session_id)
    if state is None:
        return None
    return state.model_dump(mode="json")


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_save_session_state(
    state_data: dict[str, Any],
) -> dict[str, str]:
    """Save a pipeline session state.

    Args:
        state_data: Session state fields as a dictionary.

    Returns:
        Confirmation with session_id.
    """
    state = SessionState.model_validate(state_data)
    adapter = _get_pipeline_state()
    await adapter.save(state)
    return {"status": "saved", "session_id": state.session_id}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_save_experience_pattern(
    pattern_data: dict[str, Any],
) -> dict[str, str]:
    """Save an experience pattern.

    Args:
        pattern_data: Experience pattern fields as a dictionary.

    Returns:
        Confirmation with pattern_id.
    """
    pattern = ExperiencePattern.model_validate(pattern_data)
    adapter = _get_experience()
    await adapter.save(pattern)
    return {"status": "saved", "pattern_id": pattern.pattern_id}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_list_experience_patterns(
    stage_id: int | None = None,
    min_relevance: float = 0.0,
) -> list[dict[str, Any]]:
    """List experience patterns filtered by stage and relevance.

    Args:
        stage_id: Optional stage filter (0-10).
        min_relevance: Minimum current relevance threshold.

    Returns:
        List of matching patterns as dictionaries.
    """
    adapter = _get_experience()
    patterns = await adapter.list_patterns(
        stage_id=stage_id, min_relevance=min_relevance
    )
    return [p.model_dump(mode="json") for p in patterns]


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_reinforce_pattern(
    pattern_id: str,
) -> dict[str, Any]:
    """Reinforce an experience pattern by ID.

    Args:
        pattern_id: ID of the pattern to reinforce.

    Returns:
        The reinforced pattern as a dictionary.
    """
    adapter = _get_experience()
    reinforced = await adapter.reinforce(pattern_id)
    return reinforced.model_dump(mode="json")


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_append_audit_event(
    event_data: dict[str, Any],
) -> dict[str, str]:
    """Append an immutable audit event.

    Args:
        event_data: Audit event fields as a dictionary.

    Returns:
        Confirmation with event_id.
    """
    event = AuditEvent.model_validate(event_data)
    adapter = _get_audit()
    await adapter.append(event)
    return {"status": "appended", "event_id": event.event_id}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_query_audit_events(
    query_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Query audit events with filters.

    Args:
        query_data: AuditQuery fields as a dictionary.

    Returns:
        Matching audit events as dictionaries.
    """
    query = AuditQuery.model_validate(query_data)
    adapter = _get_audit()
    events = await adapter.query(query)
    return [e.model_dump(mode="json") for e in events]


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_check_context_budget(
    total_tokens: int,
    used_tokens: int,
) -> dict[str, Any]:
    """Check context budget and get disclosure level recommendation.

    Args:
        total_tokens: Maximum token capacity.
        used_tokens: Tokens consumed so far.

    Returns:
        Budget status with recommended disclosure level.
    """
    monitor = BudgetMonitor(total_tokens=total_tokens)
    budget = monitor.update(used_tokens)
    return {
        "total_tokens": budget.total_tokens,
        "used_tokens": budget.used_tokens,
        "remaining_tokens": budget.remaining_tokens,
        "usage_percent": round(budget.usage_percent, 4),
        "disclosure_level": budget.disclosure_level.value,
        "should_compact": monitor.should_compact(),
    }
