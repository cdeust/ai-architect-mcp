"""Tests for pipeline state models — stage boundaries, status transitions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_architect_mcp._models.pipeline import (
    MAX_STAGE_ID,
    MIN_STAGE_ID,
    PipelineState,
    StageOutput,
    StageStatus,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestStageStatus:
    """Test StageStatus enum."""

    def test_all_statuses_present(self) -> None:
        assert len(StageStatus) == 5

    def test_values(self) -> None:
        expected = {"pending", "in_progress", "completed", "failed", "skipped"}
        assert {s.value for s in StageStatus} == expected


class TestStageOutput:
    """Test StageOutput model."""

    def test_valid_output(self) -> None:
        output = StageOutput(
            stage_id=2,
            finding_id="FIND-001",
            artifact={"score": 0.85},
            status=StageStatus.COMPLETED,
        )
        assert output.stage_id == 2
        assert output.artifact["score"] == 0.85

    def test_stage_id_below_min_rejected(self) -> None:
        with pytest.raises(ValueError):
            StageOutput(
                stage_id=-1,
                finding_id="FIND-001",
                status=StageStatus.PENDING,
            )

    def test_stage_id_above_max_rejected(self) -> None:
        with pytest.raises(ValueError):
            StageOutput(
                stage_id=11,
                finding_id="FIND-001",
                status=StageStatus.PENDING,
            )

    def test_failed_requires_error_message(self) -> None:
        with pytest.raises(ValueError, match="error_message is required"):
            StageOutput(
                stage_id=3,
                finding_id="FIND-001",
                status=StageStatus.FAILED,
            )

    def test_failed_with_message_ok(self) -> None:
        output = StageOutput(
            stage_id=3,
            finding_id="FIND-001",
            status=StageStatus.FAILED,
            error_message="HOR rule 15 failed: confirmatory bias detected",
        )
        assert output.error_message is not None

    def test_boundary_stage_ids(self) -> None:
        for stage_id in [MIN_STAGE_ID, MAX_STAGE_ID]:
            output = StageOutput(
                stage_id=stage_id,
                finding_id="FIND-001",
                status=StageStatus.PENDING,
            )
            assert output.stage_id == stage_id


class TestPipelineState:
    """Test PipelineState model."""

    def test_valid_state(self) -> None:
        state = PipelineState(
            finding_id="FIND-001",
            current_stage=2,
            completed_stages=[0, 1],
        )
        assert state.current_stage == 2
        assert state.completed_stages == [0, 1]

    def test_unsorted_completed_stages_rejected(self) -> None:
        with pytest.raises(ValueError, match="sorted"):
            PipelineState(
                finding_id="FIND-001",
                current_stage=3,
                completed_stages=[2, 0, 1],
            )

    def test_duplicate_completed_stages_rejected(self) -> None:
        with pytest.raises(ValueError, match="duplicates"):
            PipelineState(
                finding_id="FIND-001",
                current_stage=3,
                completed_stages=[0, 1, 1, 2],
            )

    def test_invalid_stage_in_completed_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid stage_id"):
            PipelineState(
                finding_id="FIND-001",
                current_stage=2,
                completed_stages=[0, 1, 15],
            )

    def test_serialization_round_trip(self) -> None:
        state = PipelineState(
            finding_id="FIND-001",
            current_stage=3,
            completed_stages=[0, 1, 2],
        )
        dumped = state.model_dump(mode="json")
        restored = PipelineState.model_validate(dumped)
        assert restored.finding_id == state.finding_id
        assert restored.completed_stages == state.completed_stages

    def test_fixture_mid_run(self) -> None:
        fixture_path = FIXTURES_DIR / "pipeline_state_mid_run.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            state = PipelineState.model_validate(data)
            assert state.current_stage >= 0
