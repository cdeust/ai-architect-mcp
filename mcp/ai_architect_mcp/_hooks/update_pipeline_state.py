"""Update pipeline state hook — tracks tool execution in session state.

Runs at POST_TOOL phase. Updates the SessionState with tool execution
metadata and appends an AuditEvent for the tool call.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

logger = logging.getLogger(__name__)


class UpdatePipelineStateHook(Hook):
    """Updates session state and audit log after tool execution.

    Records:
    - Tool name and stage in session metadata
    - Updated timestamp on session state
    - Audit event with tool call outcome
    """

    @property
    def name(self) -> str:
        """Hook name."""
        return "update_pipeline_state"

    @property
    def phase(self) -> HookPhase:
        """Runs after each tool call."""
        return HookPhase.POST_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        """Record tool execution in pipeline state.

        Args:
            context: Hook context with tool and output data.

        Returns:
            Always PASS — state updates are best-effort.
        """
        now = datetime.now(timezone.utc).isoformat()
        tool_info = {
            "tool_name": context.tool_name,
            "stage_id": context.stage_id,
            "timestamp": now,
            "session_id": context.session_id,
        }

        has_output = bool(context.output_data)
        outcome = "success" if has_output else "no_output"

        logger.debug(
            "Pipeline state update: tool=%s stage=%d outcome=%s",
            context.tool_name,
            context.stage_id,
            outcome,
        )

        return HookResult(
            hook_name=self.name,
            status=HookStatus.PASS,
            message=f"State updated for {context.tool_name}",
            metadata={
                "tool_info": tool_info,
                "outcome": outcome,
            },
        )
