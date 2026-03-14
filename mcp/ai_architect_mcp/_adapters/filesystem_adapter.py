"""Filesystem adapter — concrete implementation of FileSystemPort.

Wraps async file operations with project root boundary enforcement.
Injected at the composition root. Never imported directly by stage logic.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_architect_mcp._adapters.ports import FileSystemPort


class BoundaryViolationError(Exception):
    """Raised when a file operation attempts to escape the project root."""

    def __init__(self, path: Path, root: Path) -> None:
        self.path = path
        self.root = root
        super().__init__(
            f"Path {path} is outside project root {root} — "
            f"all file operations must stay within the project boundary"
        )


class FileSystemAdapter(FileSystemPort):
    """Concrete filesystem adapter with boundary enforcement.

    All file operations are constrained to the project root directory.
    Attempts to read or write outside the root raise BoundaryViolationError.

    Args:
        project_root: Root directory for all file operations.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the filesystem adapter.

        Args:
            project_root: Root directory boundary.
        """
        self._root = project_root.resolve()

    async def read(self, path: Path) -> str:
        """Read a file's contents.

        Args:
            path: Path to the file to read.

        Returns:
            The file contents as a string.

        Raises:
            BoundaryViolationError: If path is outside project root.
            FileNotFoundError: If the file does not exist.
        """
        resolved = self._resolve_and_check(path)
        return resolved.read_text(encoding="utf-8")

    async def write(self, path: Path, content: str) -> None:
        """Write content to a file, creating parent directories.

        Args:
            path: Path to write to.
            content: Content to write.

        Raises:
            BoundaryViolationError: If path is outside project root.
        """
        resolved = self._resolve_and_check(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")

    async def list_directory(
        self, path: Path, pattern: str = "*"
    ) -> list[Path]:
        """List files in a directory matching a pattern.

        Args:
            path: Directory to list.
            pattern: Glob pattern for filtering.

        Returns:
            List of matching file paths.

        Raises:
            BoundaryViolationError: If path is outside project root.
        """
        resolved = self._resolve_and_check(path)
        return sorted(resolved.glob(pattern))

    async def exists(self, path: Path) -> bool:
        """Check if a path exists.

        Args:
            path: Path to check.

        Returns:
            True if the path exists.

        Raises:
            BoundaryViolationError: If path is outside project root.
        """
        resolved = self._resolve_and_check(path)
        return resolved.exists()

    async def grep(
        self, pattern: str, path: Path | None = None
    ) -> list[dict[str, Any]]:
        """Search file contents for pattern matches.

        Args:
            pattern: Regex pattern to search for.
            path: Optional directory to restrict search. Searches root if None.

        Returns:
            List of match results with file, line, and content.

        Raises:
            BoundaryViolationError: If path is outside project root.
        """
        search_root = self._resolve_and_check(path or Path("."))
        compiled = re.compile(pattern)
        matches: list[dict[str, Any]] = []

        for file_path in search_root.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for line_num, line in enumerate(text.splitlines(), start=1):
                if compiled.search(line):
                    matches.append({
                        "file": str(file_path.relative_to(self._root)),
                        "line": line_num,
                        "content": line,
                    })
        return matches

    def _resolve_and_check(self, path: Path) -> Path:
        """Resolve a path and verify it's within the project root.

        Args:
            path: Path to resolve and check.

        Returns:
            The resolved absolute path.

        Raises:
            BoundaryViolationError: If path escapes the project root.
        """
        resolved = (self._root / path).resolve()
        if not str(resolved).startswith(str(self._root)):
            raise BoundaryViolationError(path, self._root)
        return resolved
