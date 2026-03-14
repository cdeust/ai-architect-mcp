"""GitHub Actions Filesystem adapter — bounded to GITHUB_WORKSPACE.

Provides FileSystemPort implementation that constrains all file
operations to the GitHub Actions workspace directory.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from ai_architect_mcp._adapters.filesystem_adapter import (
    BoundaryViolationError,
)
from ai_architect_mcp._adapters.ports import FileSystemPort

WORKSPACE_ENV_VAR = "GITHUB_WORKSPACE"


class GitHubActionsFilesystem(FileSystemPort):
    """Filesystem adapter bounded to GITHUB_WORKSPACE.

    Args:
        workspace: Override workspace path. Uses GITHUB_WORKSPACE env if None.
    """

    def __init__(self, workspace: Path | None = None) -> None:
        """Initialize the GHA filesystem adapter.

        Args:
            workspace: Workspace root. Falls back to GITHUB_WORKSPACE env var.

        Raises:
            ValueError: If no workspace can be determined.
        """
        if workspace is not None:
            self._root = workspace.resolve()
        else:
            env_workspace = os.environ.get(WORKSPACE_ENV_VAR)
            if not env_workspace:
                msg = (
                    f"{WORKSPACE_ENV_VAR} not set and no workspace provided "
                    f"— set the environment variable or pass workspace explicitly"
                )
                raise ValueError(msg)
            self._root = Path(env_workspace).resolve()

    async def read(self, path: Path) -> str:
        """Read a file within the workspace.

        Args:
            path: Relative or absolute path to read.

        Returns:
            File contents as string.
        """
        resolved = self._resolve(path)
        return resolved.read_text(encoding="utf-8")

    async def write(self, path: Path, content: str) -> None:
        """Write content to a file within the workspace.

        Args:
            path: Path to write to.
            content: Content to write.
        """
        resolved = self._resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")

    async def list_directory(
        self, path: Path, pattern: str = "*",
    ) -> list[Path]:
        """List files in a directory within the workspace.

        Args:
            path: Directory to list.
            pattern: Glob pattern for filtering.

        Returns:
            Matching file paths.
        """
        resolved = self._resolve(path)
        return sorted(resolved.glob(pattern))

    async def exists(self, path: Path) -> bool:
        """Check if a path exists within the workspace.

        Args:
            path: Path to check.

        Returns:
            True if exists.
        """
        resolved = self._resolve(path)
        return resolved.exists()

    async def grep(
        self, pattern: str, path: Path | None = None
    ) -> list[dict[str, Any]]:
        """Search file contents for pattern matches within workspace.

        Args:
            pattern: Regex pattern to search for.
            path: Optional directory to restrict search.

        Returns:
            List of match results with file, line, and content.
        """
        search_root = self._resolve(path or Path("."))
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

    def _resolve(self, path: Path) -> Path:
        """Resolve a path and verify it's within workspace.

        Args:
            path: Path to resolve.

        Returns:
            Resolved absolute path.

        Raises:
            BoundaryViolationError: If path escapes workspace.
        """
        resolved = (self._root / path).resolve()
        if not str(resolved).startswith(str(self._root)):
            raise BoundaryViolationError(path, self._root)
        return resolved
