"""Composition root — factory wiring all adapters to port interfaces.

The ONE place where concrete adapter types are instantiated.
All other code depends only on port interfaces, never on concrete adapters.

Environment variables:
- AI_ARCHITECT_MCPBRIDGE_PATH: xcrun path for mcpbridge (default: xcrun)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from ai_architect_mcp._adapters.filesystem_adapter import FileSystemAdapter
from ai_architect_mcp._adapters.git_adapter import GitAdapter
from ai_architect_mcp._adapters.github_adapter import GitHubAdapter
from ai_architect_mcp._adapters.local_audit import LocalAudit
from ai_architect_mcp._adapters.local_experience import LocalExperience
from ai_architect_mcp._adapters.local_pipeline_state import LocalPipelineState
from ai_architect_mcp._adapters.memory_ports import (
    AuditPort,
    ExperiencePort,
    PipelineStatePort,
)
from ai_architect_mcp._adapters.ports import (
    FileSystemPort,
    GitHubOperationsPort,
    GitOperationsPort,
    StageContextPort,
    XcodeOperationsPort,
)
from ai_architect_mcp._adapters.xcode_adapter import XcodeAdapter
from ai_architect_mcp._context.stage_context import StageContext
from ai_architect_mcp._observability.composite_adapter import (
    CompositeObservabilityAdapter,
)
from ai_architect_mcp._observability.file_adapter import FileObservabilityAdapter
from ai_architect_mcp._observability.observability_port import ObservabilityPort
from ai_architect_mcp._observability.sse_adapter import SSEObservabilityAdapter

logger = logging.getLogger(__name__)

ENV_MCPBRIDGE_PATH: str = "AI_ARCHITECT_MCPBRIDGE_PATH"
ENV_ANTHROPIC_API_KEY: str = "ANTHROPIC_API_KEY"


class CompositionRoot:
    """Factory for creating adapter instances.

    Wires concrete adapters to their port interfaces. This is the
    only module that imports concrete adapter classes.

    Mcpbridge is used for Xcode operations when available;
    otherwise falls back to xcodebuild CLI.

    Args:
        project_root: Root directory for the project.
        repo_path: Path to the git repository.
        github_repo: GitHub repository in owner/repo format.
        data_dir: Pipeline data directory for state and artifacts.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        repo_path: str = ".",
        github_repo: str | None = None,
        data_dir: Path | None = None,
    ) -> None:
        """Initialize the composition root.

        Args:
            project_root: Root directory for filesystem operations.
            repo_path: Path to the git repository.
            github_repo: GitHub repository identifier.
            data_dir: Pipeline data directory. Defaults to project_root/.pipeline.
        """
        self._project_root = project_root or Path.cwd()
        self._repo_path = repo_path
        self._github_repo = github_repo
        self._data_dir = data_dir or (self._project_root / ".pipeline")
        self._mcpbridge_path = os.environ.get(ENV_MCPBRIDGE_PATH, "xcrun")
        self._llm_client: object | None = None

    def _mcpbridge_available(self) -> bool:
        """Check if xcrun mcpbridge is available on this system.

        Returns:
            True if xcrun is found and assumed to support mcpbridge.
        """
        return shutil.which(self._mcpbridge_path) is not None

    def create_git(self) -> GitOperationsPort:
        """Create a git operations adapter.

        Returns:
            GitOperationsPort implementation.
        """
        return GitAdapter(repo_path=self._repo_path)

    def create_github(self) -> GitHubOperationsPort:
        """Create a GitHub operations adapter.

        Returns:
            GitHubOperationsPort implementation.
        """
        return GitHubAdapter(repo=self._github_repo)

    def create_xcode(self) -> XcodeOperationsPort:
        """Create an Xcode operations adapter.

        Uses mcpbridge when available, falls back to xcodebuild CLI.

        Returns:
            XcodeOperationsPort implementation.
        """
        if self._mcpbridge_available():
            from ai_architect_mcp._adapters.xcode_mcpbridge_adapter import (
                XcodeMCPBridgeAdapter,
            )
            logger.info("Using XcodeMCPBridgeAdapter (mcpbridge)")
            return XcodeMCPBridgeAdapter(xcrun_path=self._mcpbridge_path)

        logger.info(
            "mcpbridge not available, falling back to XcodeAdapter (xcodebuild CLI)"
        )
        return XcodeAdapter(project_path=self._repo_path)

    def create_filesystem(self) -> FileSystemPort:
        """Create a filesystem adapter.

        Returns:
            FileSystemPort implementation.
        """
        return FileSystemAdapter(project_root=self._project_root)

    def create_pipeline_state(self) -> PipelineStatePort:
        """Create a pipeline state persistence adapter.

        Returns:
            PipelineStatePort implementation.
        """
        return LocalPipelineState(data_dir=self._data_dir)

    def create_experience(self) -> ExperiencePort:
        """Create an experience pattern storage adapter.

        Returns:
            ExperiencePort implementation.
        """
        return LocalExperience(data_dir=self._data_dir)

    def create_audit(self) -> AuditPort:
        """Create an audit event logging adapter.

        Returns:
            AuditPort implementation.
        """
        return LocalAudit(data_dir=self._data_dir)

    @staticmethod
    def _read_claude_oauth_token() -> str | None:
        """Read OAuth access token from Claude Code credentials.

        Looks for ~/.claude/.credentials.json → claudeAiOauth.accessToken.

        Returns:
            OAuth access token string or None.
        """
        creds_path = Path.home() / ".claude" / ".credentials.json"
        if not creds_path.exists():
            return None
        try:
            data = json.loads(creds_path.read_text())
            token = data.get("claudeAiOauth", {}).get("accessToken")
            if token:
                logger.debug("Found Claude OAuth token in credentials file")
            return token
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed to read Claude credentials: %s", exc)
            return None

    def create_llm_client(self) -> object | None:
        """Create or return cached Anthropic async client.

        Auth priority:
        1. Claude subscription OAuth token from ~/.claude/.credentials.json
        2. ANTHROPIC_API_KEY environment variable

        Returns:
            AsyncAnthropic instance or None.
        """
        if self._llm_client is not None:
            return self._llm_client

        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            logger.warning("anthropic package not installed — LLM-backed tools will use stub mode")
            return None

        # 1. Try Claude subscription OAuth token
        oauth_token = self._read_claude_oauth_token()
        if oauth_token:
            self._llm_client = AsyncAnthropic(auth_token=oauth_token)
            logger.info("LLM client created (AsyncAnthropic via Claude OAuth)")
            return self._llm_client

        # 2. Fall back to API key
        api_key = os.environ.get(ENV_ANTHROPIC_API_KEY)
        if api_key:
            self._llm_client = AsyncAnthropic(api_key=api_key)
            logger.info("LLM client created (AsyncAnthropic via API key)")
            return self._llm_client

        logger.warning("No Claude OAuth token or ANTHROPIC_API_KEY — LLM-backed tools will use stub mode")
        return None

    def create_context(self) -> StageContextPort:
        """Create a stage context adapter.

        Returns:
            StageContextPort implementation.
        """
        return StageContext()

    def create_observability(
        self, enable_sse: bool = True
    ) -> ObservabilityPort:
        """Create a composite observability adapter.

        Combines file-based JSONL persistence with optional SSE streaming.
        The SSE adapter must be started separately via its start() method.

        Args:
            enable_sse: Whether to include the SSE adapter.

        Returns:
            ObservabilityPort implementation multiplexing all backends.
        """
        trace_dir = self._data_dir
        file_adapter = FileObservabilityAdapter(data_dir=trace_dir)

        adapters: list[ObservabilityPort] = [file_adapter]
        if enable_sse:
            sse_adapter = SSEObservabilityAdapter()
            adapters.append(sse_adapter)
            logger.info("Observability: file + SSE adapters created")
        else:
            logger.info("Observability: file adapter only")

        return CompositeObservabilityAdapter(adapters=adapters)
