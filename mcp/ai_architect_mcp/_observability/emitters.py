"""Typed event emitter functions for pipeline observability.

Each function emits a specific event type with structured metadata.
All functions are no-ops when no observability port is configured.
"""

from __future__ import annotations

import uuid

from ai_architect_mcp._observability.event_types import EventType, PipelineEvent
from ai_architect_mcp._observability.instrumentation import get_observability_port


async def emit_artifact_saved(
    stage_id: int,
    finding_id: str,
    session_id: str = "",
) -> None:
    """Emit an ARTIFACT_SAVED event.

    Args:
        stage_id: Pipeline stage that saved the artifact.
        finding_id: Finding identifier for the artifact.
        session_id: Current session identifier.
    """
    port = get_observability_port()
    if port is None:
        return

    await port.emit(PipelineEvent(
        event_id=f"as-{uuid.uuid4().hex[:12]}",
        event_type=EventType.ARTIFACT_SAVED,
        stage_id=stage_id,
        session_id=session_id,
        message=f"Artifact saved for finding {finding_id} at stage {stage_id}",
        metadata={"finding_id": finding_id},
    ))


async def emit_hor_rule(
    rule_id: int,
    rule_name: str,
    category: str,
    passed: bool,
    stage_id: int = 7,
    session_id: str = "",
) -> None:
    """Emit an HOR_RULE_EVALUATED event.

    Args:
        rule_id: The HOR rule ID (1-64).
        rule_name: Human-readable rule name.
        category: Rule category.
        passed: Whether the rule passed.
        stage_id: Pipeline stage (defaults to 7 — verification).
        session_id: Current session identifier.
    """
    port = get_observability_port()
    if port is None:
        return

    status = "passed" if passed else "failed"
    await port.emit(PipelineEvent(
        event_id=f"hr-{uuid.uuid4().hex[:12]}",
        event_type=EventType.HOR_RULE_EVALUATED,
        stage_id=stage_id,
        session_id=session_id,
        message=f"HOR rule {rule_id} ({rule_name}) {status}",
        metadata={
            "rule_id": str(rule_id),
            "rule_name": rule_name,
            "category": category,
            "passed": str(passed),
        },
    ))


async def emit_thinking_step(
    stage_id: int,
    title: str,
    reasoning: str,
    session_id: str = "",
) -> None:
    """Emit a THINKING_STEP event for agent reasoning visibility.

    Args:
        stage_id: Current pipeline stage.
        title: Short title of what the agent is thinking about.
        reasoning: The reasoning chain or analysis.
        session_id: Current session identifier.
    """
    port = get_observability_port()
    if port is None:
        return

    await port.emit(PipelineEvent(
        event_id=f"ts-{uuid.uuid4().hex[:12]}",
        event_type=EventType.THINKING_STEP,
        stage_id=stage_id,
        session_id=session_id,
        message=f"Thinking: {title}",
        metadata={
            "title": title,
            "reasoning": reasoning[:500],
        },
    ))


async def emit_decision(
    stage_id: int,
    title: str,
    options_considered: str,
    chosen: str,
    rationale: str,
    session_id: str = "",
) -> None:
    """Emit a DECISION_MADE event for agent decision visibility.

    Args:
        stage_id: Current pipeline stage.
        title: What decision was made.
        options_considered: Alternatives that were evaluated.
        chosen: The option selected.
        rationale: Why this option was chosen.
        session_id: Current session identifier.
    """
    port = get_observability_port()
    if port is None:
        return

    await port.emit(PipelineEvent(
        event_id=f"dm-{uuid.uuid4().hex[:12]}",
        event_type=EventType.DECISION_MADE,
        stage_id=stage_id,
        session_id=session_id,
        message=f"Decision: {title} → {chosen}",
        metadata={
            "title": title,
            "options": options_considered[:300],
            "chosen": chosen[:200],
            "rationale": rationale[:300],
        },
    ))
