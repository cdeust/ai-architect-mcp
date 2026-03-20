"""Instrumentation helpers for pipeline observability.

Provides the observe_tool_call decorator and helper functions for
emitting structured pipeline events from tool calls, artifact saves,
and HOR rule evaluations. Every event carries rich metadata so the
brain-map graph shows what was done, not just that something happened.
"""

from __future__ import annotations

import functools
import inspect
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from ai_architect_mcp._observability.event_types import EventType, PipelineEvent
from ai_architect_mcp._observability.observability_port import ObservabilityPort

logger = logging.getLogger(__name__)

_observability_port: ObservabilityPort | None = None

MAX_ARG_LENGTH: int = 200
MAX_RESULT_LENGTH: int = 200


def set_observability_port(port: ObservabilityPort | None) -> None:
    """Set the global observability port for instrumentation.

    Called once at startup from the composition root.

    Args:
        port: ObservabilityPort instance, or None to disable.
    """
    global _observability_port
    _observability_port = port


def get_observability_port() -> ObservabilityPort | None:
    """Get the current global observability port.

    Returns:
        The ObservabilityPort instance, or None if not configured.
    """
    return _observability_port


def _extract_args(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, str]:
    """Extract tool arguments as metadata key-value pairs.

    Captures argument names and truncated values so the graph shows
    what file was read, what claim was verified, etc.

    Args:
        func: The original function (for parameter names).
        args: Positional arguments.
        kwargs: Keyword arguments.

    Returns:
        Dict of param_name → truncated string value.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    meta: dict[str, str] = {}

    for i, val in enumerate(args):
        name = params[i] if i < len(params) else f"arg{i}"
        meta[f"input.{name}"] = _truncate(val)

    for key, val in kwargs.items():
        meta[f"input.{key}"] = _truncate(val)

    return meta


def _extract_result(result: Any) -> dict[str, str]:
    """Extract a result summary as metadata.

    Captures key fields from the return value so the graph shows
    outcomes: scores, verdicts, file paths, statuses.

    Args:
        result: The tool return value.

    Returns:
        Dict of result metadata.
    """
    meta: dict[str, str] = {}

    if isinstance(result, dict):
        for key in ("status", "score", "verdict", "passed", "adjusted_score",
                     "path", "branch", "sha", "finding_id", "decision",
                     "total_rules", "failed", "success"):
            if key in result:
                meta[f"output.{key}"] = _truncate(result[key])
    elif isinstance(result, list):
        meta["output.count"] = str(len(result))
    else:
        meta["output.type"] = type(result).__name__

    return meta


def _truncate(val: Any) -> str:
    """Truncate a value to a readable string for metadata.

    Args:
        val: Any value.

    Returns:
        Truncated string representation.
    """
    s = str(val)
    if len(s) > MAX_ARG_LENGTH:
        return s[:MAX_ARG_LENGTH] + "..."
    return s


def _build_message(tool_name: str, args_meta: dict[str, str]) -> str:
    """Build a human-readable message describing the tool call.

    Args:
        tool_name: Name of the tool.
        args_meta: Extracted argument metadata.

    Returns:
        Descriptive message string.
    """
    short = tool_name.replace("ai_architect_", "")
    parts = [short]

    for key, val in args_meta.items():
        name = key.replace("input.", "")
        if name in ("path", "content", "finding_id", "stage_id",
                     "rule_id", "dimension", "scheme", "branch_name",
                     "prompt", "query", "session_id", "category"):
            parts.append(f"{name}={val[:80]}")
            break

    return " → ".join(parts)


def observe_tool_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator emitting rich TOOL_CALLED/COMPLETED/FAILED events.

    Captures tool arguments in metadata so the brain-map shows what
    file was read, what claim was verified, what decision was made —
    not just that a tool was called.

    Args:
        func: The async tool function to instrument.

    Returns:
        Wrapped function with observability instrumentation.
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        port = _observability_port
        if port is None:
            return await func(*args, **kwargs)

        tool_name = func.__name__
        event_id = uuid.uuid4().hex[:12]
        stage_id = kwargs.get("stage_id", 0)
        if not isinstance(stage_id, int) or stage_id < 0 or stage_id > 10:
            stage_id = 0

        args_meta = _extract_args(func, args, kwargs)
        message = _build_message(tool_name, args_meta)

        await _emit_tool_called(port, event_id, stage_id, tool_name, message, args_meta)

        start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            elapsed_ms = (time.monotonic() - start) * 1000
            await _emit_tool_completed(
                port, event_id, stage_id, tool_name, message, args_meta, result, elapsed_ms,
            )
            return result
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            await _emit_tool_failed(
                port, event_id, stage_id, tool_name, message, args_meta, exc, elapsed_ms,
            )
            raise

    return wrapper


async def _emit_tool_called(
    port: ObservabilityPort, event_id: str, stage_id: int,
    tool_name: str, message: str, args_meta: dict[str, str],
) -> None:
    """Emit a TOOL_CALLED event."""
    await port.emit(PipelineEvent(
        event_id=f"tc-{event_id}", event_type=EventType.TOOL_CALLED,
        stage_id=stage_id, tool_name=tool_name,
        message=message, metadata=args_meta,
    ))


async def _emit_tool_completed(
    port: ObservabilityPort, event_id: str, stage_id: int,
    tool_name: str, message: str, args_meta: dict[str, str],
    result: object, elapsed_ms: float,
) -> None:
    """Emit a TOOL_COMPLETED event."""
    result_meta = _extract_result(result)
    await port.emit(PipelineEvent(
        event_id=f"td-{event_id}", event_type=EventType.TOOL_COMPLETED,
        stage_id=stage_id, tool_name=tool_name,
        message=f"{message} [{elapsed_ms:.0f}ms]",
        duration_ms=round(elapsed_ms, 2), metadata={**args_meta, **result_meta},
    ))


async def _emit_tool_failed(
    port: ObservabilityPort, event_id: str, stage_id: int,
    tool_name: str, message: str, args_meta: dict[str, str],
    exc: Exception, elapsed_ms: float,
) -> None:
    """Emit a TOOL_FAILED event."""
    await port.emit(PipelineEvent(
        event_id=f"tf-{event_id}", event_type=EventType.TOOL_FAILED,
        stage_id=stage_id, tool_name=tool_name,
        message=f"{message} FAILED: {exc}",
        duration_ms=round(elapsed_ms, 2),
        metadata={**args_meta, "error": str(exc)[:200]},
    ))



# Re-export emitter functions for backward compatibility.
# The actual implementations live in emitters.py to respect the 300-line limit.
from ai_architect_mcp._observability.emitters import (  # noqa: F401, E402
    emit_artifact_saved,
    emit_decision,
    emit_hor_rule,
    emit_thinking_step,
)
