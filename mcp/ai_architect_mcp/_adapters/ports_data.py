"""Port interfaces for data-oriented adapters.

Separated from ports.py to respect the 300-line limit.
Contains FileSystemPort and StageContextPort — both deal with
data persistence and file operations rather than build tooling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


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

    @abstractmethod
    async def grep(
        self, pattern: str, path: Path | None = None
    ) -> list[dict[str, Any]]:
        """Search file contents for pattern matches.

        Args:
            pattern: Regex pattern to search for.
            path: Optional directory to restrict search. Searches root if None.

        Returns:
            List of match results with file, line, and content.
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
