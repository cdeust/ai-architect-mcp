"""Port interfaces for infrastructure adapters.

Defines abstract base classes for all external system interactions.
Stage logic depends only on these interfaces — never on concrete adapters.
Concrete adapters implement these ports and are injected at the composition
root.

This is the hexagonal architecture boundary. Everything inside (stages,
algorithms, scoring) depends on ports. Everything outside (git, Xcode,
GitHub, filesystem) implements ports.

FileSystemPort and StageContextPort are defined in ports_data.py
(split to respect the 300-line limit) and re-exported here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai_architect_mcp._adapters.ports_data import (
    FileSystemPort,
    StageContextPort,
)
from ai_architect_mcp._adapters.ports_github import GitHubOperationsPort

__all__ = [
    "FileSystemPort",
    "GitHubOperationsPort",
    "GitOperationsPort",
    "StageContextPort",
    "XcodeOperationsPort",
]


class GitOperationsPort(ABC):
    """Port for Git version control operations.

    All git interactions in the pipeline go through this port.
    Concrete adapter: git_adapter.py (wraps git CLI).
    """

    @abstractmethod
    async def create_branch(self, branch_name: str, base: str = "main") -> str:
        """Create a new branch from the specified base.

        Args:
            branch_name: Name for the new branch.
            base: Base branch to create from. Defaults to main.

        Returns:
            The full branch reference.
        """
        ...

    @abstractmethod
    async def commit(self, message: str, files: list[str]) -> str:
        """Stage specified files and create a commit.

        Args:
            message: Commit message following project conventions.
            files: List of file paths to stage and commit.

        Returns:
            The commit SHA.
        """
        ...

    @abstractmethod
    async def push(self, branch: str, force: bool = False) -> None:
        """Push a branch to the remote.

        Args:
            branch: Branch name to push.
            force: Whether to force-push. Use with extreme caution.
        """
        ...

    @abstractmethod
    async def diff(self, base: str, head: str) -> str:
        """Get the diff between two refs.

        Args:
            base: Base ref for comparison.
            head: Head ref for comparison.

        Returns:
            Unified diff as a string.
        """
        ...

    @abstractmethod
    async def log(self, branch: str, count: int = 10) -> list[dict[str, str]]:
        """Get recent commit log entries.

        Args:
            branch: Branch to read log from.
            count: Number of entries to return.

        Returns:
            List of commit entries with sha, message, author, date.
        """
        ...

    @abstractmethod
    async def reset(self, ref: str) -> None:
        """Reset current branch to ref.

        Args:
            ref: The git ref to reset to (commit SHA, branch, tag).
        """
        ...

    @abstractmethod
    async def reset_branch(self, branch: str, to_ref: str) -> None:
        """Reset a specific branch to a ref.

        Args:
            branch: The branch to reset.
            to_ref: The ref to reset the branch to.
        """
        ...

    @abstractmethod
    async def create_worktree(
        self, branch_name: str, base: str = "main"
    ) -> str:
        """Create an isolated git worktree with a new branch.

        One worktree per finding enables concurrent pipeline runs
        without checkout collisions.

        Args:
            branch_name: Branch to create in the worktree.
            base: Base branch to fork from.

        Returns:
            Absolute path to the worktree directory.
        """
        ...

    @abstractmethod
    async def remove_worktree(self, worktree_path: str) -> None:
        """Remove a previously created worktree.

        Args:
            worktree_path: Path returned by create_worktree.
        """
        ...


class XcodeOperationsPort(ABC):
    """Port for Xcode build, test, and bridge operations.

    All Xcode interactions go through this port. The concrete adapter
    wraps the Xcode MCP bridge for read/write/grep and xcodebuild
    for build/test/preview.
    """

    @abstractmethod
    async def build(
        self, scheme: str, configuration: str = "Debug"
    ) -> dict[str, Any]:
        """Build an Xcode scheme.

        Args:
            scheme: The Xcode scheme to build.
            configuration: Build configuration (Debug/Release).

        Returns:
            Build result with success status, warnings, errors.
        """
        ...

    @abstractmethod
    async def run_tests(
        self, scheme: str, test_plan: str | None = None
    ) -> dict[str, Any]:
        """Run tests for an Xcode scheme.

        Args:
            scheme: The Xcode scheme to test.
            test_plan: Optional test plan name. Runs all if None.

        Returns:
            Test results with pass/fail counts and failure details.
        """
        ...

    @abstractmethod
    async def preview(self, view_name: str) -> bytes:
        """Capture a SwiftUI preview snapshot.

        Args:
            view_name: The SwiftUI view to preview.

        Returns:
            PNG image bytes of the rendered preview.
        """
        ...

    @abstractmethod
    async def read(self, path: str) -> str:
        """Read via Xcode MCP bridge (XcodeRead).

        Args:
            path: Path to the file to read.

        Returns:
            File contents as a string.
        """
        ...

    @abstractmethod
    async def write(self, path: str, content: str) -> None:
        """Write via Xcode MCP bridge (XcodeWrite).

        Args:
            path: Path to write to.
            content: Content to write.
        """
        ...

    @abstractmethod
    async def grep(
        self, pattern: str, path: str | None = None
    ) -> list[dict[str, Any]]:
        """Search codebase via Xcode MCP bridge (XcodeGrep).

        Args:
            pattern: Search pattern.
            path: Optional path to restrict search.

        Returns:
            List of match results with file, line, and content.
        """
        ...


