"""Tests for ArtifactStore — store/retrieve, forward-only, query."""

from __future__ import annotations

import pytest

from ai_architect_mcp._context.artifact_store import (
    ArtifactNotFoundError,
    ArtifactStore,
    ContextViolationError,
)


@pytest.fixture
def store() -> ArtifactStore:
    """Create an in-memory artifact store."""
    return ArtifactStore()


class TestStoreAndRetrieve:
    """Test basic store and retrieve operations."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, store: ArtifactStore) -> None:
        artifact = {"score": 0.85, "modules": ["auth"]}
        await store.store(0, "FIND-001", artifact)
        result = await store.retrieve(0, "FIND-001")
        assert result == artifact

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_raises(self, store: ArtifactStore) -> None:
        with pytest.raises(ArtifactNotFoundError):
            await store.retrieve(0, "FIND-MISSING")

    @pytest.mark.asyncio
    async def test_exists_true(self, store: ArtifactStore) -> None:
        await store.store(0, "FIND-001", {"data": True})
        assert await store.exists(0, "FIND-001") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, store: ArtifactStore) -> None:
        assert await store.exists(0, "FIND-001") is False


class TestForwardOnly:
    """Test forward-only write constraint."""

    @pytest.mark.asyncio
    async def test_forward_write_allowed(self, store: ArtifactStore) -> None:
        await store.store(0, "FIND-001", {"stage": 0})
        await store.store(1, "FIND-001", {"stage": 1})
        await store.store(2, "FIND-001", {"stage": 2})
        assert await store.exists(2, "FIND-001")

    @pytest.mark.asyncio
    async def test_backward_write_blocked(self, store: ArtifactStore) -> None:
        await store.store(0, "FIND-001", {"stage": 0})
        await store.store(3, "FIND-001", {"stage": 3})
        with pytest.raises(ContextViolationError, match="Cannot modify stage 2"):
            await store.store(2, "FIND-001", {"stage": 2})

    @pytest.mark.asyncio
    async def test_overwrite_same_stage_with_later_exists_blocked(
        self, store: ArtifactStore
    ) -> None:
        await store.store(1, "FIND-001", {"v": 1})
        await store.store(5, "FIND-001", {"v": 5})
        with pytest.raises(ContextViolationError):
            await store.store(1, "FIND-001", {"v": 2})

    @pytest.mark.asyncio
    async def test_different_findings_independent(self, store: ArtifactStore) -> None:
        await store.store(5, "FIND-001", {"stage": 5})
        await store.store(0, "FIND-002", {"stage": 0})
        assert await store.exists(0, "FIND-002")


class TestQuery:
    """Test query across stages."""

    @pytest.mark.asyncio
    async def test_query_matches(self, store: ArtifactStore) -> None:
        await store.store(0, "FIND-001", {"health": "ok"})
        await store.store(1, "FIND-001", {"signals": 3})
        results = await store.query("FIND-001", "health")
        assert len(results) == 1
        assert results[0]["stage_id"] == 0

    @pytest.mark.asyncio
    async def test_query_no_matches(self, store: ArtifactStore) -> None:
        await store.store(0, "FIND-001", {"data": "test"})
        results = await store.query("FIND-001", "nonexistent_key_xyz")
        assert len(results) == 0


class TestListStages:
    """Test listing stages for a finding."""

    @pytest.mark.asyncio
    async def test_list_stages(self, store: ArtifactStore) -> None:
        await store.store(0, "FIND-001", {})
        await store.store(2, "FIND-001", {})
        await store.store(5, "FIND-001", {})
        stages = await store.list_stages("FIND-001")
        assert stages == [0, 2, 5]

    @pytest.mark.asyncio
    async def test_list_stages_empty(self, store: ArtifactStore) -> None:
        stages = await store.list_stages("FIND-MISSING")
        assert stages == []


class TestValidation:
    """Test stage_id validation."""

    @pytest.mark.asyncio
    async def test_invalid_stage_id_negative(self, store: ArtifactStore) -> None:
        with pytest.raises(ValueError, match="out of range"):
            await store.store(-1, "FIND-001", {})

    @pytest.mark.asyncio
    async def test_invalid_stage_id_too_high(self, store: ArtifactStore) -> None:
        with pytest.raises(ValueError, match="out of range"):
            await store.store(11, "FIND-001", {})

    @pytest.mark.asyncio
    async def test_boundary_stage_ids(self, store: ArtifactStore) -> None:
        await store.store(0, "FIND-001", {"min": True})
        await store.store(10, "FIND-002", {"max": True})
        assert await store.exists(0, "FIND-001")
        assert await store.exists(10, "FIND-002")
