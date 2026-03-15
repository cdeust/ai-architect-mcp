"""POST_TOOL hook for emitting GATE_EVALUATED observability events.

Detects gate-related tool completions and emits structured events
to the observability port. Gates are pipeline checkpoints at
stage boundaries — this hook has the right vantage point to observe them.
"""

from __future__ import annotations

import uuid

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

GATE_TOOL_NAMES: frozenset[str] = frozenset({
    "ai_architect_run_interview_gate",
    "ai_architect_run_hor_rules",
    "ai_architect_verify_graph",
    "ai_architect_run_build",
    "ai_architect_run_tests",
})

HOOK_NAME: str = "observe-events"


class ObserveEventsHook(Hook):
    """POST_TOOL hook that emits GATE_EVALUATED events.

    Fires after gate-related tools complete. Extracts pass/fail
    outcome from tool output and emits a structured event.
    """

    @property
    def name(self) -> str:
        """Human-readable hook name."""
        return HOOK_NAME

    @property
    def phase(self) -> HookPhase:
        """This hook runs after tool execution."""
        return HookPhase.POST_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        """Emit GATE_EVALUATED event if the tool is a gate.

        Args:
            context: Hook execution context with tool output.

        Returns:
            Always PASS — observability never blocks the pipeline.
        """
        if context.tool_name not in GATE_TOOL_NAMES:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message="Not a gate tool, skipping",
            )

        from ai_architect_mcp._observability.instrumentation import (
            get_observability_port,
        )
        port = get_observability_port()
        if port is None:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message="No observability port configured",
            )

        passed = self._extract_gate_outcome(context.output_data)
        from ai_architect_mcp._observability.event_types import (
            EventType,
            PipelineEvent,
        )
        await port.emit(PipelineEvent(
            event_id=f"ge-{uuid.uuid4().hex[:12]}",
            event_type=EventType.GATE_EVALUATED,
            stage_id=context.stage_id,
            session_id=context.session_id,
            tool_name=context.tool_name,
            message=f"Gate {context.tool_name} {'passed' if passed else 'failed'}",
            metadata={"passed": str(passed)},
        ))

        return HookResult(
            hook_name=self.name,
            status=HookStatus.PASS,
            message=f"Emitted GATE_EVALUATED for {context.tool_name}",
        )

    @staticmethod
    def _extract_gate_outcome(output: dict[str, object]) -> bool:
        """Extract pass/fail from gate tool output.

        Args:
            output: Tool output dictionary.

        Returns:
            True if the gate passed, False otherwise.
        """
        if "passed" in output:
            return bool(output["passed"])
        if "adjusted_score" in output:
            score = output["adjusted_score"]
            return isinstance(score, (int, float)) and score >= 0.7
        return True
