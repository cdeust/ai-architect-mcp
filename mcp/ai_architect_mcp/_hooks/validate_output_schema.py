"""Validate output schema hook — checks tool output structure.

Runs at POST_TOOL phase. Validates that tool output conforms to
expected structure by checking required keys are present.
"""

from __future__ import annotations

import logging
from typing import Any

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

logger = logging.getLogger(__name__)

TOOL_SCHEMAS: dict[str, list[str]] = {
    "ai_architect_verify_claim": [
        "claim_id", "evaluator_id", "score", "confidence",
    ],
    "ai_architect_verify_graph": [
        "finding_id", "passed",
    ],
    "ai_architect_run_interview_gate": [
        "gate_decision", "dimension_scores",
    ],
    "ai_architect_consensus": [
        "algorithm", "final_score",
    ],
}


class ValidateOutputSchemaHook(Hook):
    """Validates tool output contains expected keys.

    Only validates tools that have a registered schema.
    Unknown tools pass through without validation.
    """

    @property
    def name(self) -> str:
        """Hook name."""
        return "validate_output_schema"

    @property
    def phase(self) -> HookPhase:
        """Runs after each tool call."""
        return HookPhase.POST_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        """Validate tool output against registered schema.

        Args:
            context: Hook context with tool output.

        Returns:
            PASS if valid or no schema, BLOCK if missing keys.
        """
        required_keys = TOOL_SCHEMAS.get(context.tool_name)
        if required_keys is None:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message=(
                    f"No schema registered for {context.tool_name} "
                    f"— skipping validation"
                ),
            )

        output = context.output_data
        missing = [
            key for key in required_keys
            if key not in output
        ]

        if missing:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.BLOCK,
                message=(
                    f"Tool {context.tool_name} output missing "
                    f"required keys: {', '.join(missing)}"
                ),
                metadata={"missing_keys": missing},
            )

        return HookResult(
            hook_name=self.name,
            status=HookStatus.PASS,
            message=(
                f"Tool {context.tool_name} output schema valid"
            ),
        )
