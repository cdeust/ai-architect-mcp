"""Enforce document read hook — blocks tools if SKILL.md not read.

Runs at PRE_TOOL phase. Requires that the stage SKILL.md has been
read before any tool call is permitted. This ensures Claude has
read the skill specification before acting.
"""

from __future__ import annotations

import logging

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

logger = logging.getLogger(__name__)

EXEMPT_TOOLS = frozenset({
    "ai_architect_load_session_state",
    "ai_architect_check_context_budget",
})


class EnforceDocReadHook(Hook):
    """Blocks tool calls until SKILL.md has been read.

    Certain tools are exempt (session state loading, budget checks)
    since they may be needed before the skill is read.
    """

    @property
    def name(self) -> str:
        """Hook name."""
        return "enforce_doc_read"

    @property
    def phase(self) -> HookPhase:
        """Runs before each tool call."""
        return HookPhase.PRE_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        """Check if SKILL.md has been read before allowing tool use.

        Args:
            context: Hook execution context.

        Returns:
            PASS if SKILL.md read or tool is exempt, BLOCK otherwise.
        """
        if context.tool_name in EXEMPT_TOOLS:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message=(
                    f"Tool {context.tool_name} is exempt from "
                    f"SKILL.md read requirement"
                ),
            )

        if context.skill_md_read:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message="SKILL.md has been read",
            )

        return HookResult(
            hook_name=self.name,
            status=HookStatus.BLOCK,
            message=(
                f"Tool {context.tool_name} blocked — read the stage "
                f"SKILL.md before calling any tools. This ensures "
                f"you understand the stage specification before acting."
            ),
        )
