"""Tests for validate output schema hook."""

from __future__ import annotations

import pytest

from ai_architect_mcp._hooks.base import HookContext, HookStatus
from ai_architect_mcp._hooks.validate_output_schema import (
    ValidateOutputSchemaHook,
)


class TestValidateOutputSchemaHook:
    """Tests for ValidateOutputSchemaHook."""

    @pytest.mark.asyncio
    async def test_unknown_tool_passes(self) -> None:
        hook = ValidateOutputSchemaHook()
        ctx = HookContext(
            tool_name="unknown_tool",
            output_data={"anything": "goes"},
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS

    @pytest.mark.asyncio
    async def test_valid_output_passes(self) -> None:
        hook = ValidateOutputSchemaHook()
        ctx = HookContext(
            tool_name="ai_architect_run_interview_gate",
            output_data={
                "gate_decision": "APPROVED",
                "dimension_scores": [],
            },
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS

    @pytest.mark.asyncio
    async def test_missing_keys_blocks(self) -> None:
        hook = ValidateOutputSchemaHook()
        ctx = HookContext(
            tool_name="ai_architect_run_interview_gate",
            output_data={"gate_decision": "APPROVED"},
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.BLOCK
        assert "dimension_scores" in result.message

    @pytest.mark.asyncio
    async def test_verify_claim_schema(self) -> None:
        hook = ValidateOutputSchemaHook()
        ctx = HookContext(
            tool_name="ai_architect_verify_claim",
            output_data={
                "claim_id": "123",
                "evaluator_id": "eval-1",
                "score": 0.9,
                "confidence": 0.8,
            },
        )
        result = await hook.execute(ctx)
        assert result.status == HookStatus.PASS
