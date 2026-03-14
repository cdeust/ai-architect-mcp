"""Composition root — factory wiring all adapters to port interfaces.

The ONE place where concrete adapter types are instantiated.
All other code depends only on port interfaces, never on concrete adapters.

Environment variables:
- AI_ARCHITECT_MCPBRIDGE_PATH: xcrun path for mcpbridge (default: xcrun)
"""

from __future__ import annotations

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

logger = logging.getLogger(__name__)

ENV_MCPBRIDGE_PATH: str = "AI_ARCHITECT_MCPBRIDGE_PATH"


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
    """

    def __init__(
        self,
        project_root: Path | None = None,
        repo_path: str = ".",
        github_repo: str | None = None,
    ) -> None:
        """Initialize the composition root.

        Args:
            project_root: Root directory for filesystem operations.
            repo_path: Path to the git repository.
            github_repo: GitHub repository identifier.
        """
        self._project_root = project_root or Path.cwd()
        self._repo_path = repo_path
        self._github_repo = github_repo
        self._mcpbridge_path = os.environ.get(ENV_MCPBRIDGE_PATH, "xcrun")

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
        return LocalPipelineState(data_dir=self._project_root / ".ai-architect")

    def create_experience(self) -> ExperiencePort:
        """Create an experience pattern storage adapter.

        Returns:
            ExperiencePort implementation.
        """
        return LocalExperience(data_dir=self._project_root / ".ai-architect")

    def create_audit(self) -> AuditPort:
        """Create an audit event logging adapter.

        Returns:
            AuditPort implementation.
        """
        return LocalAudit(data_dir=self._project_root / ".ai-architect")

    def create_context(self) -> StageContextPort:
        """Create a stage context adapter.

        Returns:
            StageContextPort implementation.
        """
        return StageContext()
