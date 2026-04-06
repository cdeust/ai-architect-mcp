"""Git utility functions for repository detection and metadata.

Pure wrappers around git CLI commands. No state, no side effects
beyond subprocess calls.
"""

from __future__ import annotations

import subprocess


def is_git_repo(path: str) -> bool:
    """Check if a path is inside a git repository.

    Args:
        path: Filesystem path to check.

    Returns:
        True if the path is inside a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def get_git_root(path: str) -> str | None:
    """Get the root directory of the git repository containing path.

    Args:
        path: Any path inside a git repo.

    Returns:
        Absolute path to the repo root, or None if not a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def get_current_commit(path: str) -> str:
    """Get the short hash of the current HEAD commit.

    Args:
        path: Path inside a git repository.

    Returns:
        7-character short hash, or empty string if not a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""
