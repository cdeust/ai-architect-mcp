"""Pipeline type models — progress tracking and result reporting."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelinePhase(str, Enum):
    """Phases of the ingestion pipeline."""

    SCAN = "scan"
    STRUCTURE = "structure"
    PARSE = "parse"
    RESOLVE = "resolve"
    COMMUNITY = "community"
    PROCESS = "process"


class PhaseStatus(str, Enum):
    """Status of a pipeline phase."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PhaseProgress(BaseModel):
    """Progress of a single pipeline phase.

    Args:
        phase: Which pipeline phase.
        status: Current status.
        total_items: Total items to process.
        processed_items: Items processed so far.
        started_at: When the phase started.
        message: Human-readable status message.
    """

    phase: PipelinePhase = Field(description="Pipeline phase")
    status: PhaseStatus = Field(default=PhaseStatus.PENDING, description="Current status")
    total_items: int = Field(default=0, ge=0, description="Total items to process")
    processed_items: int = Field(default=0, ge=0, description="Items processed so far")
    started_at: datetime | None = Field(default=None, description="Phase start time")
    message: str = Field(default="", description="Status message")


class PipelineProgress(BaseModel):
    """Aggregate progress across all pipeline phases."""

    phases: dict[str, PhaseProgress] = Field(default_factory=dict)
    overall_percent: float = Field(default=0.0, ge=0.0, le=100.0)


class PipelineResult(BaseModel):
    """Result of a complete pipeline run.

    Args:
        repo_path: Repository that was indexed.
        commit_hash: Git commit at indexing time.
        total_files: Files discovered.
        total_nodes: Symbols extracted.
        total_relationships: Edges created.
        total_communities: Communities detected.
        total_processes: Execution flows traced.
        duration_seconds: Pipeline duration.
        errors: Errors encountered.
    """

    repo_path: str = Field(description="Repository path")
    commit_hash: str = Field(default="", description="Git commit hash")
    total_files: int = Field(default=0, ge=0)
    total_nodes: int = Field(default=0, ge=0)
    total_relationships: int = Field(default=0, ge=0)
    total_communities: int = Field(default=0, ge=0)
    total_processes: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    errors: list[str] = Field(default_factory=list)


class RepoMetadata(BaseModel):
    """Metadata about an indexed repository.

    Args:
        repo_path: Absolute path.
        repo_name: Human-readable name.
        last_commit: Last indexed commit hash.
        languages: Detected languages.
        last_indexed_at: When last indexed.
    """

    repo_path: str = Field(description="Repository path")
    repo_name: str = Field(default="", description="Repository name")
    total_nodes: int = Field(default=0, ge=0, description="Total indexed nodes")
    last_commit: str = Field(default="", description="Last commit hash")
    languages: list[str] = Field(default_factory=list, description="Detected languages")
    last_indexed_at: datetime | None = Field(default=None, description="Last index time")
