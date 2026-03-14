"""Port interfaces for infrastructure adapters.

Defines abstract base classes for all external system interactions.
Stage logic depends only on these interfaces — never on concrete adapters.
Concrete adapters implement these ports and are injected at the composition
root.

This is the hexagonal architecture boundary. Everything inside (stages,
algorithms, scoring) depends on ports. Everything outside (git, Xcode,
GitHub, filesystem) implements ports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


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
            The full branch reference (e.g., refs/heads/feature/finding-123).
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


class XcodeOperationsPort(ABC):
    """Port for Xcode build and test operations.

    All Xcode interactions go through this port. The concrete adapter
    wraps the Xcode MCP bridge (28 external tools).
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
    async def test(
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
    async def get_pull_request(self, pr_number: int) -> dict[str, Any]:
        """Get pull request details.

        Args:
            pr_number: The PR number.

        Returns:
            PR metadata including status, checks, and review state.
        """
        ...

    @abstractmethod
    async def add_comment(self, pr_number: int, body: str) -> dict[str, str]:
        """Add a comment to a pull request.

        Args:
            pr_number: The PR number.
            body: Comment body (markdown).

        Returns:
            Comment metadata with id and url.
        """
        ...


class FileSystemPort(ABC):
    """Port for filesystem operations.

    All file read/write operations in stage logic go through this port.
    This enables testing with in-memory filesystems and enforcing
    access control (e.g., preventing writes outside the project root).
    """

    @abstractmethod
    async def read(self, path: Path) -> str:
        """Read a file's contents.

        Args:
            path: Path to the file to read.

        Returns:
            The file contents as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    @abstractmethod
    async def write(self, path: Path, content: str) -> None:
        """Write content to a file, creating parent directories as needed.

        Args:
            path: Path to write to.
            content: Content to write.
        """
        ...

    @abstractmethod
    async def list_directory(self, path: Path, pattern: str = "*") -> list[Path]:
        """List files in a directory matching a pattern.

        Args:
            path: Directory to list.
            pattern: Glob pattern for filtering. Defaults to all files.

        Returns:
            List of matching file paths.
        """
        ...

    @abstractmethod
    async def exists(self, path: Path) -> bool:
        """Check if a path exists.

        Args:
            path: Path to check.

        Returns:
            True if the path exists, False otherwise.
        """
        ...


class StageContextPort(ABC):
    """Port for stage context operations.

    Abstracts the storage backend for stage artifacts. Concrete
    implementations may use iCloud, local filesystem, or in-memory
    storage for testing.
    """

    @abstractmethod
    async def load_artifact(
        self, stage_id: int, finding_id: str
    ) -> dict[str, Any]:
        """Load a stage artifact.

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.

        Returns:
            The stage artifact as a dictionary.
        """
        ...

    @abstractmethod
    async def save_artifact(
        self, stage_id: int, finding_id: str, artifact: dict[str, Any]
    ) -> None:
        """Save a stage artifact.

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.
            artifact: The artifact to persist.
        """
        ...

    @abstractmethod
    async def query_artifacts(
        self, finding_id: str, query: str
    ) -> list[dict[str, Any]]:
        """Query artifacts across stages for a finding.

        Args:
            finding_id: Unique finding identifier.
            query: Semantic query string.

        Returns:
            Matching artifact fragments with stage metadata.
        """
        ...
