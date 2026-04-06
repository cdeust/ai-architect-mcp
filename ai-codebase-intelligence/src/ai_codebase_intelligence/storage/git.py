"""Git adapter — subprocess wrappers for git operations.

All functions are read-only. No mutations to the git state.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any


def is_git_repo(repo_path: str) -> bool:
    """Check if a path is inside a git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path, capture_output=True, check=True,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def get_current_commit(repo_path: str) -> str:
    """Get the HEAD commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return ""


def get_git_root(from_path: str) -> str | None:
    """Resolve the absolute path to the git root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=from_path, capture_output=True, text=True, check=True,
        )
        raw = result.stdout.strip()
        return os.path.abspath(raw)
    except (subprocess.CalledProcessError, OSError):
        return None


def git_log_commits(
    repo_path: str,
    max_commits: int = 500,
) -> list[dict[str, Any]]:
    """Extract commit history with changed files.

    Each commit includes SHA, author, email, date, and list of changed
    files. Used by co-change detection (Gall et al. 1998, ICSM) and
    churn metrics (Nagappan & Ball 2005, ICSE).

    Args:
        repo_path: Absolute path to the git repository.
        max_commits: Maximum commits to analyze. Default 500.

    Returns:
        List of commit dicts with sha, author, email, date, files.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={max_commits}",
             "--pretty=format:%H\t%aN\t%aE\t%aI", "--name-only"],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return []
    return _parse_git_log_output(result.stdout)


def _parse_git_log_output(raw: str) -> list[dict[str, Any]]:
    """Parse git log --name-only output into structured commits."""
    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "\t" in line:
            parts = line.split("\t", 3)
            if len(parts) == 4:
                if current:
                    commits.append(current)
                current = {
                    "sha": parts[0], "author": parts[1],
                    "email": parts[2], "date": parts[3], "files": [],
                }
                continue
        if current:
            current["files"].append(line)
    if current:
        commits.append(current)
    return commits


def git_blame_file(
    repo_path: str,
    file_path: str,
) -> list[dict[str, Any]]:
    """Aggregate line ownership per author for a single file.

    Uses git blame --line-porcelain for accurate per-line attribution.
    Aggregation follows Bird et al. 2011 (ESEC/FSE): ownership is
    measured by fraction of lines attributed to each author.

    Args:
        repo_path: Absolute path to the git repository.
        file_path: Relative path to the file within the repo.

    Returns:
        List of dicts with author, email, line_count, sorted descending.
    """
    try:
        result = subprocess.run(
            ["git", "blame", "--line-porcelain", "--", file_path],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return []
    return _parse_blame_output(result.stdout)


def _parse_blame_output(raw: str) -> list[dict[str, Any]]:
    """Parse git blame --line-porcelain output into author aggregates."""
    author_lines: dict[str, dict[str, Any]] = {}
    current_author = ""
    current_email = ""
    for line in raw.split("\n"):
        if line.startswith("author "):
            current_author = line[7:]
        elif line.startswith("author-mail "):
            current_email = line[12:].strip("<>")
            key = current_email or current_author
            if key not in author_lines:
                author_lines[key] = {
                    "author": current_author,
                    "email": current_email,
                    "line_count": 0,
                }
            author_lines[key]["line_count"] += 1
    return sorted(
        author_lines.values(),
        key=lambda a: a["line_count"],
        reverse=True,
    )


def git_file_churn(
    repo_path: str,
    file_path: str,
    max_commits: int = 500,
) -> dict[str, Any]:
    """Compute churn metrics for a single file.

    Implements relative code churn measures from Nagappan & Ball 2005
    (ICSE): churned LOC, deleted LOC, and commit count.

    Args:
        repo_path: Absolute path to the git repository.
        file_path: Relative path to the file within the repo.
        max_commits: Maximum commits to scan.

    Returns:
        Dict with churn_count, lines_added, lines_deleted.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={max_commits}",
             "--pretty=format:", "--numstat", "--follow", "--", file_path],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return {"churn_count": 0, "lines_added": 0, "lines_deleted": 0}
    return _parse_numstat_output(result.stdout)


def _parse_numstat_output(raw: str) -> dict[str, Any]:
    """Parse git log --numstat output into churn totals."""
    added = 0
    deleted = 0
    count = 0
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] != "-":
            try:
                added += int(parts[0])
                deleted += int(parts[1])
                count += 1
            except ValueError:
                continue
    return {"churn_count": count, "lines_added": added, "lines_deleted": deleted}
