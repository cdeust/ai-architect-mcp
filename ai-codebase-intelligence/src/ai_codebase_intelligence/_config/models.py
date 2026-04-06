"""Configuration models — Pydantic v2 types for all settings.

Each section maps to a TOML table in defaults.toml. Environment
variables override with CI_ prefix (CI_INDEXING_MAX_FILE_SIZE_BYTES).

OBSERVATION: Hardcoding constants across multiple modules makes them
  difficult to audit and tune (CHUNK_BYTE_BUDGET, MAX_FILE_SIZE, RRF_K).
PROBLEM: Changing one constant requires grep across the entire codebase.
  No validation — typos silently produce wrong behavior.
SOLUTION: Single TOML config file + Pydantic models with Field validation.
  One source of truth, type-checked at startup, documented in-place.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ServerSection(BaseModel):
    """HTTP/MCP server configuration."""

    host: str = Field(default="127.0.0.1", description="Bind address")
    port: int = Field(default=4747, ge=1, le=65535, description="Port number")
    log_level: str = Field(default="info", description="Logging level")


class IndexingSection(BaseModel):
    """Ingestion pipeline configuration."""

    max_file_size_bytes: int = Field(
        default=524288, ge=1024,
        description="Skip files larger than this (512KB default)",
    )
    chunk_byte_budget: int = Field(
        default=20_971_520, ge=1_048_576,
        description="Max source bytes per parse chunk (20MB default)",
    )
    ast_cache_size: int = Field(
        default=50, ge=1,
        description="LRU cache size for parsed AST trees",
    )
    max_content_snippet: int = Field(
        default=5000, ge=100,
        description="Max chars of source code stored per symbol",
    )


class SearchSection(BaseModel):
    """Search engine configuration."""

    fts_result_limit: int = Field(
        default=20, ge=1, le=1000,
        description="Maximum FTS results per query",
    )
    rrf_k: int = Field(
        default=60, ge=1,
        description="Reciprocal Rank Fusion constant (standard: 60)",
    )


class CommunitySection(BaseModel):
    """Leiden community detection configuration."""

    leiden_resolution_small: float = Field(
        default=1.0, gt=0.0,
        description="Resolution parameter for small graphs (<10K nodes)",
    )
    leiden_resolution_large: float = Field(
        default=2.0, gt=0.0,
        description="Resolution parameter for large graphs (≥10K nodes)",
    )
    large_graph_threshold: int = Field(
        default=10_000, ge=100,
        description="Node count threshold for large-graph mode",
    )
    min_confidence_large: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Skip low-confidence edges in large graphs",
    )


class ProcessSection(BaseModel):
    """Process (execution flow) detection configuration."""

    max_trace_depth: int = Field(
        default=10, ge=2, le=50,
        description="BFS maximum traversal depth",
    )
    max_branching: int = Field(
        default=4, ge=1, le=20,
        description="BFS maximum branching factor per node",
    )
    max_processes: int = Field(
        default=75, ge=1,
        description="Maximum processes to detect",
    )
    min_steps: int = Field(
        default=3, ge=2,
        description="Minimum steps for a valid process (2-step is trivial)",
    )
    min_trace_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Skip CALLS edges below this confidence in traces",
    )


class ImpactSection(BaseModel):
    """Impact analysis defaults."""

    default_max_depth: int = Field(
        default=3, ge=1, le=10,
        description="Default BFS depth for blast radius analysis",
    )
    default_min_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Default minimum edge confidence filter",
    )


class StorageSection(BaseModel):
    """Storage configuration."""

    db_filename: str = Field(
        default="index.db",
        description="SQLite database filename inside storage directory",
    )
    storage_dir: str = Field(
        default=".codebase-intelligence",
        description="Storage directory name created inside the indexed repo",
    )


class GitAnalyticsSection(BaseModel):
    """Git history analytics configuration.

    All thresholds trace to peer-reviewed papers. None are invented.
    Thresholds are tunable per project — no universal optimal value
    exists (Zimmermann et al. 2005, Sec 5.3).
    """

    max_commits: int = Field(
        default=500, ge=1,
        description="Max commits to analyze from git log",
    )
    orphan_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description=(
            "Fraction of files orphaned before bus factor is counted. "
            "Avelino et al. 2016, ICPC, Sec 3"
        ),
    )
    minor_contributor_threshold: float = Field(
        default=0.05, ge=0.0, le=1.0,
        description=(
            "Devs contributing below this fraction are minor contributors. "
            "Bird et al. 2011, ESEC/FSE, Sec 5.1"
        ),
    )
    cochange_min_support: int = Field(
        default=3, ge=1,
        description=(
            "Min co-occurrences for co-change detection. "
            "Project-dependent — Zimmermann et al. 2005, IEEE TSE, Sec 5.3"
        ),
    )
    cochange_min_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description=(
            "Min conditional probability for co-change pair. "
            "Project-dependent — Zimmermann et al. 2005, IEEE TSE, Sec 5.3"
        ),
    )


class CodeIntelligenceConfig(BaseModel):
    """Root configuration — aggregates all sections.

    Loaded from defaults.toml, overridden by environment variables.
    """

    server: ServerSection = Field(default_factory=ServerSection)
    indexing: IndexingSection = Field(default_factory=IndexingSection)
    search: SearchSection = Field(default_factory=SearchSection)
    community: CommunitySection = Field(default_factory=CommunitySection)
    process: ProcessSection = Field(default_factory=ProcessSection)
    impact: ImpactSection = Field(default_factory=ImpactSection)
    storage: StorageSection = Field(default_factory=StorageSection)
    git_analytics: GitAnalyticsSection = Field(default_factory=GitAnalyticsSection)
