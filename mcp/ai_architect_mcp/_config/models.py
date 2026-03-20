"""Configuration models — Pydantic v2 types for server configuration.

Each section maps to a TOML table. All fields have defaults from
defaults.toml. Environment variables override with AI_ARCHITECT_ prefix.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ServerSection(BaseModel):
    """Server network configuration."""

    host: str = Field(
        default="127.0.0.1",
        description="Host address to bind the MCP server to",
    )
    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Port number for the MCP server",
    )
    log_level: str = Field(
        default="info",
        description="Logging level (debug, info, warning, error, critical)",
    )


class VerificationSection(BaseModel):
    """Verification engine configuration."""

    hor_rule_count: int = Field(
        default=64,
        ge=1,
        description="Number of HOR rules to evaluate",
    )
    max_debate_rounds: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum rounds for multi-agent debate",
    )
    consensus_algorithm: str = Field(
        default="weighted_average",
        description="Default consensus algorithm for score resolution",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for passing verification",
    )


class PromptingSection(BaseModel):
    """Prompting engine configuration."""

    default_strategy: str = Field(
        default="adaptive_expansion",
        description="Default thinking strategy for prompt enhancement",
    )
    max_thinking_depth: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum depth for tree-of-thought exploration",
    )
    thought_buffer_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum thoughts retained in the signal-aware buffer",
    )


class ContextSection(BaseModel):
    """Context management configuration."""

    max_stages: int = Field(
        default=11,
        ge=1,
        description="Total number of pipeline stages (0-10)",
    )
    data_dir: str = Field(
        default=".pipeline",
        description="Root data directory for pipeline state and artifacts",
    )
    artifact_persist_dir: str = Field(
        default=".pipeline/artifacts",
        description="Directory for persisting stage artifacts",
    )
    session_persist_dir: str = Field(
        default=".pipeline/sessions",
        description="Directory for session state persistence",
    )


class AdaptersSection(BaseModel):
    """Infrastructure adapter configuration."""

    git_repo_path: str = Field(
        default=".",
        description="Path to the git repository",
    )
    github_repo: str = Field(
        default="",
        description="GitHub repository in owner/repo format",
    )
    project_root: str = Field(
        default=".",
        description="Root directory for filesystem operations",
    )


class LoggingSection(BaseModel):
    """Logging configuration."""

    format: str = Field(
        default="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        description="Python logging format string",
    )
    file: str = Field(
        default="",
        description="Log file path (empty for stdout only)",
    )


class ServerConfig(BaseModel):
    """Root configuration model combining all sections.

    Maps to the full TOML configuration file structure.
    Each section corresponds to a [section] table in TOML.
    """

    server: ServerSection = Field(
        default_factory=ServerSection,
        description="Server network settings",
    )
    verification: VerificationSection = Field(
        default_factory=VerificationSection,
        description="Verification engine settings",
    )
    prompting: PromptingSection = Field(
        default_factory=PromptingSection,
        description="Prompting engine settings",
    )
    context: ContextSection = Field(
        default_factory=ContextSection,
        description="Context management settings",
    )
    adapters: AdaptersSection = Field(
        default_factory=AdaptersSection,
        description="Infrastructure adapter settings",
    )
    logging: LoggingSection = Field(
        default_factory=LoggingSection,
        description="Logging settings",
    )
