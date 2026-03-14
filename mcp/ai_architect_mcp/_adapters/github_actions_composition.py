"""GitHub Actions composition root — factory wiring GHA adapters.

Provides the same factory interface as CompositionRoot but
wires GitHub Actions-specific adapter implementations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ai_architect_mcp._adapters.github_actions_context import (
    GitHubActionsContext,
)
from ai_architect_mcp._adapters.github_actions_filesystem import (
    GitHubActionsFilesystem,
)
from ai_architect_mcp._adapters.github_actions_git import GitHubActionsGit
from ai_architect_mcp._adapters.github_actions_github import (
    GitHubActionsGitHub,
)
from ai_architect_mcp._adapters.github_actions_xcode import GitHubActionsXcode
from ai_architect_mcp._adapters.ports import (
    FileSystemPort,
    GitHubOperationsPort,
    GitOperationsPort,
    StageContextPort,
    XcodeOperationsPort,
)

WORKSPACE_ENV = "GITHUB_WORKSPACE"


class GitHubActionsComposition:
    """Factory for GitHub Actions adapter instances.

    Reads configuration from GHA environment variables.
    """

    def __init__(self) -> None:
        """Initialize from GitHub Actions environment."""
        workspace = os.environ.get(WORKSPACE_ENV, ".")
        self._workspace = Path(workspace).resolve()
        self._repo = os.environ.get("AI_ARCHITECT_REPO", "")

    def create_git(self) -> GitOperationsPort:
        """Create a git adapter for GHA.

        Returns:
            GitOperationsPort backed by subprocess.
        """
        return GitHubActionsGit(repo_path=str(self._workspace))

    def create_github(self) -> GitHubOperationsPort:
        """Create a GitHub API adapter for GHA.

        Returns:
            GitHubOperationsPort backed by REST API.
        """
        return GitHubActionsGitHub(repo=self._repo)

    def create_xcode(self) -> XcodeOperationsPort:
        """Create a Xcode adapter (not supported in GHA).

        Returns:
            XcodeOperationsPort that raises NotSupportedError.
        """
        return GitHubActionsXcode()

    def create_filesystem(self) -> FileSystemPort:
        """Create a filesystem adapter bounded to workspace.

        Returns:
            FileSystemPort bounded to GITHUB_WORKSPACE.
        """
        return GitHubActionsFilesystem(workspace=self._workspace)

    def create_context(self) -> StageContextPort:
        """Create a stage context adapter for GHA.

        Returns:
            StageContextPort backed by JSON files.
        """
        return GitHubActionsContext(workspace=self._workspace)
