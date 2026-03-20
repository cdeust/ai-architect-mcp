"""GitHub port interface — extracted from ports.py for 300-line compliance.

Defines the abstract base class for all GitHub API interactions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class GitHubOperationsPort(ABC):
    """Port for GitHub API operations.

    All GitHub interactions go through this port. The concrete adapter
    wraps the GitHub CLI (gh) or API.
    """

    @abstractmethod
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict[str, Any]:
        """Create a pull request.

        Args:
            title: PR title.
            body: PR description body (markdown).
            head: Source branch.
            base: Target branch. Defaults to main.

        Returns:
            PR metadata with number, url, and state.
        """
        ...

    @abstractmethod
    async def fetch_tree(
        self, path: str = "", ref: str = "HEAD"
    ) -> list[dict[str, str]]:
        """Fetch repository tree structure.

        Args:
            path: Subdirectory path. Empty string for root.
            ref: Git ref to fetch from. Defaults to HEAD.

        Returns:
            List of tree entries with path, type, and sha.
        """
        ...

    @abstractmethod
    async def fetch_file(self, path: str, ref: str = "HEAD") -> str:
        """Fetch a single file's contents from the remote.

        Args:
            path: File path within the repository.
            ref: Git ref to fetch from. Defaults to HEAD.

        Returns:
            File contents as a string.
        """
        ...

    @abstractmethod
    async def batch_fetch(
        self, paths: list[str], ref: str = "HEAD"
    ) -> dict[str, str]:
        """Batch fetch multiple files from the remote.

        Args:
            paths: List of file paths to fetch.
            ref: Git ref to fetch from. Defaults to HEAD.

        Returns:
            Mapping of path to file contents.
        """
        ...
