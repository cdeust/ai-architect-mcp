"""Tests for hook registry."""

from __future__ import annotations

import pytest

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)
from ai_architect_mcp._hooks.registry import HookRegistry


class _PassHook(Hook):
    """Test hook that always passes."""

    @property
    def name(self) -> str:
        return "pass_hook"

    @property
    def phase(self) -> HookPhase:
        return HookPhase.PRE_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        return HookResult(
            hook_name=self.name, status=HookStatus.PASS, message="ok",
        )


class _BlockHook(Hook):
    """Test hook that always blocks."""

    @property
    def name(self) -> str:
        return "block_hook"

    @property
    def phase(self) -> HookPhase:
        return HookPhase.PRE_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        return HookResult(
            hook_name=self.name, status=HookStatus.BLOCK, message="blocked",
        )


class _ErrorHook(Hook):
    """Test hook that raises an exception."""

    @property
    def name(self) -> str:
        return "error_hook"

    @property
    def phase(self) -> HookPhase:
        return HookPhase.PRE_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        msg = "hook exploded"
        raise RuntimeError(msg)


class TestHookRegistry:
    """Tests for HookRegistry."""

    def test_register_and_get(self) -> None:
        registry = HookRegistry()
        hook = _PassHook()
        registry.register(hook)
        hooks = registry.get_hooks(HookPhase.PRE_TOOL)
        assert len(hooks) == 1
        assert hooks[0].name == "pass_hook"

    def test_hook_count(self) -> None:
        registry = HookRegistry()
        registry.register(_PassHook())
        registry.register(_BlockHook())
        assert registry.hook_count == 2

    @pytest.mark.asyncio
    async def test_all_pass(self) -> None:
        registry = HookRegistry()
        registry.register(_PassHook())
        results = await registry.run_phase(
            HookPhase.PRE_TOOL, HookContext(),
        )
        assert len(results) == 1
        assert results[0].status == HookStatus.PASS

    @pytest.mark.asyncio
    async def test_short_circuit_on_block(self) -> None:
        registry = HookRegistry()
        registry.register(_BlockHook())
        registry.register(_PassHook())
        results = await registry.run_phase(
            HookPhase.PRE_TOOL, HookContext(),
        )
        assert len(results) == 1
        assert results[0].status == HookStatus.BLOCK

    @pytest.mark.asyncio
    async def test_pass_before_block(self) -> None:
        registry = HookRegistry()
        registry.register(_PassHook())
        registry.register(_BlockHook())
        results = await registry.run_phase(
            HookPhase.PRE_TOOL, HookContext(),
        )
        assert len(results) == 2
        assert results[0].status == HookStatus.PASS
        assert results[1].status == HookStatus.BLOCK

    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        registry = HookRegistry()
        registry.register(_ErrorHook())
        results = await registry.run_phase(
            HookPhase.PRE_TOOL, HookContext(),
        )
        assert len(results) == 1
        assert results[0].status == HookStatus.ERROR
        assert "exploded" in results[0].message

    @pytest.mark.asyncio
    async def test_empty_phase(self) -> None:
        registry = HookRegistry()
        results = await registry.run_phase(
            HookPhase.SESSION_START, HookContext(),
        )
        assert len(results) == 0
