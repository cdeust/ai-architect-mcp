"""Hook registry — stores hooks by phase, runs with short-circuit.

The registry collects hooks and executes them in registration order
for a given phase. Execution short-circuits on the first BLOCK result.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

logger = logging.getLogger(__name__)


class HookRegistry:
    """Registry for Python hooks with phase-based dispatch.

    Hooks are registered for specific phases and executed in order.
    The first BLOCK result short-circuits the chain.
    """

    def __init__(self) -> None:
        """Initialize an empty hook registry."""
        self._hooks: dict[HookPhase, list[Hook]] = defaultdict(list)

    def register(self, hook: Hook) -> None:
        """Register a hook for its declared phase.

        Args:
            hook: The hook instance to register.
        """
        self._hooks[hook.phase].append(hook)
        logger.debug(
            "Registered hook %s for phase %s",
            hook.name,
            hook.phase.value,
        )

    def get_hooks(self, phase: HookPhase) -> list[Hook]:
        """Get all hooks registered for a phase.

        Args:
            phase: The lifecycle phase.

        Returns:
            List of hooks in registration order.
        """
        return list(self._hooks[phase])

    async def run_phase(
        self, phase: HookPhase, context: HookContext,
    ) -> list[HookResult]:
        """Execute all hooks for a phase, short-circuiting on BLOCK.

        Args:
            phase: The lifecycle phase to run.
            context: Execution context for hooks.

        Returns:
            List of HookResults from executed hooks. If a hook
            returns BLOCK, execution stops and the BLOCK result
            is the last in the list.
        """
        results: list[HookResult] = []
        hooks = self._hooks[phase]

        for hook in hooks:
            try:
                result = await hook.execute(context)
            except Exception as exc:
                result = HookResult(
                    hook_name=hook.name,
                    status=HookStatus.ERROR,
                    message=f"Hook raised exception: {exc}",
                )

            results.append(result)
            logger.info(
                "%s [%s]: %s",
                result.status.value.upper(),
                hook.name,
                result.message,
            )

            if result.status == HookStatus.BLOCK:
                logger.warning(
                    "Hook chain short-circuited by %s", hook.name,
                )
                break

        return results

    @property
    def hook_count(self) -> int:
        """Total number of registered hooks across all phases."""
        return sum(len(hooks) for hooks in self._hooks.values())
