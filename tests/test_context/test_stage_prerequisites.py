"""Tests for stage prerequisite enforcement.

Verifies that ``StageContext.save`` refuses to persist an artifact for
stage N until every prerequisite stage has produced an artifact for the
same finding. This is the gate that prevents the orchestrator from
skipping ahead to implementation before PRD generation has happened.
"""
from __future__ import annotations

import pytest

from ai_architect_mcp._context.artifact_store import ArtifactStore
from ai_architect_mcp._context.stage_context import StageContext
from ai_architect_mcp._context.stage_prerequisites import (
    STAGE_PREREQUISITES,
    StagePrerequisiteViolation,
    check_prerequisites,
    is_unknown_stage,
)


@pytest.fixture
def context() -> StageContext:
    """Fresh StageContext with an in-memory store."""
    return StageContext(store=ArtifactStore())


@pytest.fixture
def finding_id() -> str:
    return "TEST-PREREQ-001"


# ── pure check_prerequisites ────────────────────────────────────────────────


class TestCheckPrerequisites:
    """Direct tests for the pure prerequisite check."""

    def test_stage_zero_has_no_prerequisites(self) -> None:
        check_prerequisites(0, "f", set())  # must not raise

    def test_stage_one_requires_zero(self) -> None:
        with pytest.raises(StagePrerequisiteViolation) as exc:
            check_prerequisites(1, "f", set())
        assert exc.value.missing == [0]

    def test_stage_one_with_zero_completed_passes(self) -> None:
        check_prerequisites(1, "f", {0})

    def test_stage_six_requires_zero_through_five(self) -> None:
        # Stage 6 = Implementation. Requires 0..5 (health → review).
        with pytest.raises(StagePrerequisiteViolation) as exc:
            check_prerequisites(6, "f", {0, 1, 2})
        assert exc.value.missing == [3, 4, 5]

    def test_stage_six_with_full_prereqs_passes(self) -> None:
        check_prerequisites(6, "f", {0, 1, 2, 3, 4, 5})

    def test_violation_carries_finding_id(self) -> None:
        with pytest.raises(StagePrerequisiteViolation) as exc:
            check_prerequisites(4, "FIND-XYZ", set())
        assert exc.value.finding_id == "FIND-XYZ"
        assert exc.value.stage_id == 4

    def test_violation_message_lists_correct_order(self) -> None:
        with pytest.raises(StagePrerequisiteViolation) as exc:
            check_prerequisites(10, "f", {0, 5, 9})
        # Missing prereqs should be sorted ascending
        assert exc.value.missing == [1, 2, 3, 4, 6, 7, 8]

    def test_unknown_stage_eleven_passes(self) -> None:
        # Stage 11 is out of canonical range — value validation happens
        # in artifact_store, not here. The prereq check is permissive.
        check_prerequisites(11, "f", set())

    def test_unknown_stage_has_no_prerequisites(self) -> None:
        # Defensive: a stage id not in the map should not raise — the
        # caller is responsible for validating stage range elsewhere.
        check_prerequisites(99, "f", set())

    def test_is_unknown_stage(self) -> None:
        assert is_unknown_stage(0) is False
        assert is_unknown_stage(10) is False
        assert is_unknown_stage(11) is True
        assert is_unknown_stage(-1) is True


# ── StageContext integration ───────────────────────────────────────────────


class TestStageContextEnforcement:
    """End-to-end tests through StageContext.save()."""

    @pytest.mark.asyncio
    async def test_in_order_pipeline_succeeds(
        self, context: StageContext, finding_id: str,
    ) -> None:
        for stage_id in range(11):  # 0..10 inclusive
            await context.save(stage_id, finding_id, {"stage": stage_id})

        loaded = await context.load(10, finding_id)
        assert loaded["stage"] == 10

    @pytest.mark.asyncio
    async def test_skip_to_implementation_raises(
        self, context: StageContext, finding_id: str,
    ) -> None:
        # Save stage 0 only, then try to jump straight to implementation.
        await context.save(0, finding_id, {"stage": 0})
        with pytest.raises(StagePrerequisiteViolation) as exc:
            await context.save(6, finding_id, {"stage": 6})
        assert 1 in exc.value.missing
        assert 4 in exc.value.missing  # PRD generation
        assert 5 in exc.value.missing  # PRD review

    @pytest.mark.asyncio
    async def test_skip_prd_review_raises(
        self, context: StageContext, finding_id: str,
    ) -> None:
        for stage_id in (0, 1, 2, 3, 4):
            await context.save(stage_id, finding_id, {"stage": stage_id})
        # Try to save Implementation (6) without PRD review (5)
        with pytest.raises(StagePrerequisiteViolation) as exc:
            await context.save(6, finding_id, {"stage": 6})
        assert exc.value.missing == [5]

    @pytest.mark.asyncio
    async def test_each_finding_isolated(
        self, context: StageContext,
    ) -> None:
        # Finding A goes through 0→3
        for stage_id in range(4):
            await context.save(stage_id, "A", {"f": "A"})

        # Finding B fresh — must still start at 0, cannot piggyback on A
        with pytest.raises(StagePrerequisiteViolation):
            await context.save(3, "B", {"f": "B"})

    @pytest.mark.asyncio
    async def test_save_artifact_path_also_enforced(
        self, context: StageContext, finding_id: str,
    ) -> None:
        # The StageContextPort save_artifact path must enforce too.
        await context.save_artifact(0, finding_id, {"stage": 0})
        with pytest.raises(StagePrerequisiteViolation):
            await context.save_artifact(4, finding_id, {"stage": 4})


# ── declarative map sanity ─────────────────────────────────────────────────


class TestStagePrerequisitesMap:
    """Verify the declared map matches the canonical pipeline shape."""

    def test_all_eleven_stages_present(self) -> None:
        assert set(STAGE_PREREQUISITES.keys()) == set(range(11))

    def test_each_stage_requires_only_strictly_earlier_stages(self) -> None:
        for stage_id, required in STAGE_PREREQUISITES.items():
            for r in required:
                assert r < stage_id, (
                    f"Stage {stage_id} declares {r} as a prerequisite "
                    f"but {r} is not strictly earlier"
                )

    def test_each_stage_requires_all_earlier_stages(self) -> None:
        # Strict order: stage N requires {0, 1, ..., N-1}
        for stage_id in STAGE_PREREQUISITES:
            expected = frozenset(range(stage_id))
            assert STAGE_PREREQUISITES[stage_id] == expected
