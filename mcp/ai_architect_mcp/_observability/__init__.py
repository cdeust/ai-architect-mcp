"""Pipeline observability — event types, ports, and adapters.

Re-exports the public API for the observability module.
"""

from ai_architect_mcp._observability.composite_adapter import (
    CompositeObservabilityAdapter,
)
from ai_architect_mcp._observability.event_types import EventType, PipelineEvent
from ai_architect_mcp._observability.file_adapter import FileObservabilityAdapter
from ai_architect_mcp._observability.instrumentation import (
    emit_artifact_saved,
    emit_decision,
    emit_hor_rule,
    emit_thinking_step,
    observe_tool_call,
    set_observability_port,
)
from ai_architect_mcp._observability.observability_port import ObservabilityPort
from ai_architect_mcp._observability.sse_adapter import SSEObservabilityAdapter

__all__ = [
    "CompositeObservabilityAdapter",
    "EventType",
    "FileObservabilityAdapter",
    "ObservabilityPort",
    "PipelineEvent",
    "SSEObservabilityAdapter",
    "emit_artifact_saved",
    "emit_decision",
    "emit_hor_rule",
    "emit_thinking_step",
    "observe_tool_call",
    "set_observability_port",
]
