"""Session start hook — loads SessionState and validates SKILL.md.

Runs at SESSION_START phase to ensure the session has a valid
state and that the stage SKILL.md file exists.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

logger = logging.getLogger(__name__)

SKILL_MD_PATTERN = "skills/stage-{stage_id}-*/SKILL.md"
STAGE_45_SKILL = "skills/stage-4-5-interview/SKILL.md"


class SessionStartHook(Hook):
    """Validates session prerequisites at startup.

    Checks:
    1. Session ID is non-empty
    2. Stage SKILL.md file exists for the current stage
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the session start hook.

        Args:
            project_root: Root directory for locating SKILL.md files.
        """
        self._root = project_root or Path.cwd()

    @property
    def name(self) -> str:
        """Hook name."""
        return "session_start"

    @property
    def phase(self) -> HookPhase:
        """Runs at session start."""
        return HookPhase.SESSION_START

    async def execute(self, context: HookContext) -> HookResult:
        """Validate session prerequisites.

        Args:
            context: Hook execution context.

        Returns:
            PASS if prerequisites met, BLOCK otherwise.
        """
        if not context.session_id.strip():
            return HookResult(
                hook_name=self.name,
                status=HookStatus.BLOCK,
                message=(
                    "Session ID is empty — provide a valid "
                    "session_id in the context"
                ),
            )

        skill_path = self._find_skill_md(context.stage_id)
        if skill_path is None:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message=(
                    f"No SKILL.md found for stage {context.stage_id} "
                    f"— stage may not require one"
                ),
                metadata={"warning": "no_skill_md"},
            )

        return HookResult(
            hook_name=self.name,
            status=HookStatus.PASS,
            message=f"Session {context.session_id} initialized",
            metadata={"skill_md": str(skill_path)},
        )

    def _find_skill_md(self, stage_id: int) -> Path | None:
        """Find the SKILL.md file for a given stage.

        Args:
            stage_id: Pipeline stage number.

        Returns:
            Path to SKILL.md if found, None otherwise.
        """
        if stage_id == 45:
            path = self._root / STAGE_45_SKILL
            return path if path.exists() else None

        pattern = SKILL_MD_PATTERN.format(stage_id=stage_id)
        matches = list(self._root.glob(pattern))
        return matches[0] if matches else None
