"""Tests for StageContext — integration with ArtifactStore, boundary validation."""

from __future__ import annotations

import pytest

from ai_architect_mcp._context.artifact_store import (
    ArtifactNotFoundError,
    ArtifactStore,
    ContextViolationError,
)
from ai_architect_mcp._context.stage_context import StageContext


@pytest.fixture
def context() -> StageContext:
    """Create a StageContext with in-memory store."""
    return StageContext(store=ArtifactStore())


class TestStageContext:
    """Test StageContext operations."""

    @pytest.mark.asyncio
    async def test_save_and_load(self, context: StageContext) -> None:
        artifact = {"signals": 5}
        await context.save(1, "FIND-001", artifact)
        result = await context.load(1, "FIND-001")
        assert result == artifact

    @pytest.mark.asyncio
    async def test_load_nonexistent_raises(self, context: StageContext) -> None:
        with pytest.raises(ArtifactNotFoundError):
            await context.load(0, "FIND-MISSING")

    @pytest.mark.asyncio
    async def test_forward_only_enforcement(self, context: StageContext) -> None:
        await context.save(0, "FIND-001", {"stage": 0})
        await context.save(5, "FIND-001", {"stage": 5})
        with pytest.raises(ContextViolationError):
            await context.save(2, "FIND-001", {"stage": 2})

    @pytest.mark.asyncio
    async def test_query(self, context: StageContext) -> None:
        await context.save(0, "FIND-001", {"health": "ok"})
        await context.save(1, "FIND-001", {"signals": 3})
        results = await context.query("FIND-001", "health")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_invalid_stage_id(self, context: StageContext) -> None:
        with pytest.raises(ValueError, match="out of range"):
            await context.save(11, "FIND-001", {})

    @pytest.mark.asyncio
    async def test_invalid_stage_id_negative(self, context: StageContext) -> None:
        with pytest.raises(ValueError, match="out of range"):
            await context.load(-1, "FIND-001")


class TestStageContextPortProtocol:
    """Test StageContextPort protocol methods."""

    @pytest.mark.asyncio
    async def test_load_artifact(self, context: StageContext) -> None:
        await context.save_artifact(0, "FIND-001", {"data": True})
        result = await context.load_artifact(0, "FIND-001")
        assert result == {"data": True}

    @pytest.mark.asyncio
    async def test_query_artifacts(self, context: StageContext) -> None:
        await context.save_artifact(0, "FIND-001", {"key": "value"})
        results = await context.query_artifacts("FIND-001", "key")
        assert len(results) == 1
