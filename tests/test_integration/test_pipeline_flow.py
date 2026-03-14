"""Integration test — finding flows through stages 0-2 with mocked adapters."""

from __future__ import annotations

import pytest

from ai_architect_mcp._context.artifact_store import ArtifactStore
from ai_architect_mcp._context.stage_context import StageContext
from ai_architect_mcp._models.finding import Finding, Severity, SourceCategory
from ai_architect_mcp._scoring.compound import calculate_compound_score


class TestPipelineFlow:
    """Test finding progression through early pipeline stages."""

    @pytest.mark.asyncio
    async def test_stages_0_through_2(self) -> None:
        """Verify StageContext accumulates correctly across stages."""
        store = ArtifactStore()
        ctx = StageContext(store=store)

        finding = Finding(
            finding_id="FIND-INT-001",
            title="Integration Test Finding",
            description="Testing pipeline flow",
            source_category=SourceCategory.ANTHROPIC,
            relevance_score=0.9,
            severity=Severity.HIGH,
        )

        # Stage 0: Health Check
        await ctx.save(0, finding.finding_id, {
            "health_check": "passed",
            "tools_available": True,
            "skill_versions_valid": True,
        })

        # Verify Stage 0 output
        stage_0 = await ctx.load(0, finding.finding_id)
        assert stage_0["health_check"] == "passed"

        # Stage 1: Discovery
        await ctx.save(1, finding.finding_id, {
            "signals_detected": 3,
            "categories_scanned": 14,
            "findings": [finding.model_dump(mode="json")],
        })

        stage_1 = await ctx.load(1, finding.finding_id)
        assert stage_1["signals_detected"] == 3

        # Stage 2: Impact Analysis
        score = calculate_compound_score(0.9, 0.7, 0.8, 0.85)
        await ctx.save(2, finding.finding_id, {
            "compound_score": score.model_dump(mode="json"),
            "affected_modules": ["auth", "api"],
            "risk_level": "high",
        })

        stage_2 = await ctx.load(2, finding.finding_id)
        assert stage_2["risk_level"] == "high"

        # Verify forward accumulation
        stages = await store.list_stages(finding.finding_id)
        assert stages == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_forward_only_enforced(self) -> None:
        """Verify context rejects backward writes."""
        store = ArtifactStore()
        ctx = StageContext(store=store)

        await ctx.save(0, "FIND-001", {"stage": 0})
        await ctx.save(3, "FIND-001", {"stage": 3})

        from ai_architect_mcp._context.artifact_store import ContextViolationError
        with pytest.raises(ContextViolationError):
            await ctx.save(1, "FIND-001", {"stage": 1})

    @pytest.mark.asyncio
    async def test_query_across_stages(self) -> None:
        """Verify querying finds artifacts across stages."""
        store = ArtifactStore()
        ctx = StageContext(store=store)

        await ctx.save(0, "FIND-001", {"health": "ok"})
        await ctx.save(1, "FIND-001", {"signals": 3})
        await ctx.save(2, "FIND-001", {"health_impact": "high"})

        results = await ctx.query("FIND-001", "health")
        assert len(results) == 2  # stage 0 and stage 2
