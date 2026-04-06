"""Filesystem walker — discovers Python source files in a repository.

Walks the directory tree, collecting .py files and ignoring
__pycache__ directories.
"""

from __future__ import annotations

import os


def discover_files(repo_path: str) -> list[str]:
    """Discover all .py files under *repo_path*.

    Ignores __pycache__ directories. Returns an empty list if the
    path does not exist.

    Args:
        repo_path: Root directory to scan.

    Returns:
        Sorted list of absolute .py file paths.
    """
    if not os.path.isdir(repo_path):
        return []

    results: list[str] = []
    for dirpath, dirnames, filenames in os.walk(repo_path):
        dirnames[:] = [
            d for d in dirnames if d != "__pycache__"
        ]
        for fname in filenames:
            if fname.endswith(".py"):
                results.append(os.path.join(dirpath, fname))

    results.sort()
    return results
