"""Hook base types — phase, status, result, context, and abstract Hook.

All Python hooks implement the Hook ABC, which declares a phase and
an async execute method. Hooks return HookResult with PASS, BLOCK,
or ERROR status.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HookPhase(str, Enum):
    """Lifecycle phase when the hook executes."""

    SESSION_START = "session_start"
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    SESSION_END = "session_end"


class HookStatus(str, Enum):
    """Outcome of a hook execution."""

    PASS = "pass"
    BLOCK = "block"
    ERROR = "error"


class HookResult(BaseModel):
    """Result returned by a hook execution.

    PASS: continue to next hook or proceed.
    BLOCK: stop hook chain and reject the operation.
    ERROR: hook itself failed (not the operation).
    """

    hook_name: str = Field(
        description="Name of the hook that produced this result",
    )
    status: HookStatus = Field(
        description="Outcome of the hook execution",
    )
    message: str = Field(
        default="",
        description="Human-readable explanation of the result",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the hook executed",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context from the hook",
    )


class HookContext(BaseModel):
    """Context passed to hooks during execution.

    Contains information about the current session, stage, tool,
    and any relevant input/output data.
    """

    session_id: str = Field(
        default="",
        description="Current session identifier",
    )
    stage_id: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Current pipeline stage",
    )
    tool_name: str = Field(
        default="",
        description="Name of the tool being called (pre/post hooks)",
    )
    command: str = Field(
        default="",
        description="Command being executed (for security classification)",
    )
    input_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool input data",
    )
    output_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool output data (post-tool hooks only)",
    )
    skill_md_read: bool = Field(
        default=False,
        description="Whether SKILL.md has been read in this session",
    )


class Hook(ABC):
    """Abstract base class for all Python hooks.

    Each hook declares which phase it runs in and implements
    an async execute method that returns a HookResult.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable hook name for logging and results."""
        ...

    @property
    @abstractmethod
    def phase(self) -> HookPhase:
        """Lifecycle phase when this hook should execute."""
        ...

    @abstractmethod
    async def execute(self, context: HookContext) -> HookResult:
        """Execute the hook logic.

        Args:
            context: Hook execution context.

        Returns:
            HookResult with PASS, BLOCK, or ERROR status.
        """
        ...
