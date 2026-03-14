"""Save session summary hook — generates HandoffDocument at session end.

Runs at SESSION_END phase. Creates a HandoffDocument summarizing
completed work, in-progress items, and next actions for the
following session.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from ai_architect_mcp._context.handoff import HandoffDocument
from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

logger = logging.getLogger(__name__)


class SaveSessionSummaryHook(Hook):
    """Generates a HandoffDocument at session end.

    Extracts session metadata to build the handoff, ensuring
    no state is lost between sessions.
    """

    @property
    def name(self) -> str:
        """Hook name."""
        return "save_session_summary"

    @property
    def phase(self) -> HookPhase:
        """Runs at session end."""
        return HookPhase.SESSION_END

    async def execute(self, context: HookContext) -> HookResult:
        """Generate and return a HandoffDocument.

        Args:
            context: Session context with accumulated metadata.

        Returns:
            PASS with handoff document in metadata.
        """
        now = datetime.now(timezone.utc).isoformat()

        completed = context.input_data.get("completed", [])
        in_progress = context.input_data.get("in_progress", [])
        blocked = context.input_data.get("blocked", [])
        next_actions = context.input_data.get("next_actions", [])

        session_id = context.session_id or "unknown"

        handoff = HandoffDocument(
            session_id=session_id,
            timestamp=now,
            completed=completed,
            in_progress=in_progress,
            blocked=blocked,
            next_actions=next_actions,
        )

        markdown = handoff.to_markdown()

        return HookResult(
            hook_name=self.name,
            status=HookStatus.PASS,
            message=f"Session summary generated for {session_id}",
            metadata={
                "handoff_markdown": markdown,
                "handoff_data": handoff.model_dump(mode="json"),
            },
        )
