"""Tests for pipeline type models."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_codebase_intelligence._models.pipeline_types import (
    PhaseProgress,
    PhaseStatus,
    PipelinePhase,
    PipelineProgress,
    PipelineResult,
    RepoMetadata,
)


class TestPipelinePhase:
    """Tests for PipelinePhase enum."""

    def test_all_phases(self) -> None:
        assert len(PipelinePhase) == 6
        phases = [p.value for p in PipelinePhase]
        assert phases == ["scan", "structure", "parse", "resolve", "community", "process"]


class TestPhaseProgress:
    """Tests for PhaseProgress model."""

    def test_default_progress(self) -> None:
        progress = PhaseProgress(phase=PipelinePhase.SCAN)
        assert progress.status == PhaseStatus.PENDING
        assert progress.total_items == 0
        assert progress.processed_items == 0
        assert progress.started_at is None

    def test_running_progress(self) -> None:
        now = datetime.now(timezone.utc)
        progress = PhaseProgress(
            phase=PipelinePhase.PARSE,
            status=PhaseStatus.RUNNING,
            total_items=100,
            processed_items=50,
            started_at=now,
        )
        assert progress.processed_items == 50


class TestPipelineResult:
    """Tests for PipelineResult model."""

    def test_default_result(self) -> None:
        result = PipelineResult(repo_path="/tmp/repo")
        assert result.total_files == 0
        assert result.total_nodes == 0
        assert result.errors == []

    def test_completed_result(self) -> None:
        result = PipelineResult(
            repo_path="/tmp/repo",
            commit_hash="abc1234",
            total_files=150,
            total_nodes=2800,
            total_relationships=5600,
            total_communities=12,
            total_processes=45,
            duration_seconds=8.5,
        )
        assert result.total_nodes == 2800


class TestRepoMetadata:
    """Tests for RepoMetadata model."""

    def test_create_metadata(self) -> None:
        meta = RepoMetadata(
            repo_path="/Users/dev/project",
            repo_name="project",
            last_commit="abc1234",
            languages=["python", "typescript"],
        )
        assert meta.repo_name == "project"
        assert len(meta.languages) == 2

    def test_serialization_roundtrip(self) -> None:
        meta = RepoMetadata(
            repo_path="/tmp/repo",
            repo_name="repo",
            last_indexed_at=datetime.now(timezone.utc),
        )
        data = meta.model_dump(mode="json")
        restored = RepoMetadata.model_validate(data)
        assert restored.repo_path == meta.repo_path
