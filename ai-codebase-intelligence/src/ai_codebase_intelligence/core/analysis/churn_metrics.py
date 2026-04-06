"""Churn metrics — relative code churn per Nagappan & Ball 2005.

OBSERVATION: Nagappan, N. & Ball, T. (2005). "Use of Relative Code
  Churn Measures to Predict System Defect Density." ICSE 2005.

PROBLEM: High-churn files are statistically more likely to contain
  defects. Relative churn (normalized by file size) is a stronger
  predictor than absolute churn.

SOLUTION: Compute per-file churn metrics from git log --numstat.
  Report absolute and relative measures. NO multiplication with
  complexity — that combination is not peer-reviewed.

Metrics (Nagappan & Ball 2005, Sec 3):
  churn_count: number of commits touching the file
  lines_added: total lines added across all commits
  lines_deleted: total lines deleted across all commits
  relative_churn: lines_added / total_loc (if total_loc > 0)
  relative_deleted: lines_deleted / total_loc (if total_loc > 0)
"""

from __future__ import annotations

import os
from typing import Any

from ...storage.git import git_file_churn


def calculate_churn_metrics(
    repo_path: str,
    file_paths: list[str],
    max_commits: int = 500,
) -> dict[str, Any]:
    """Compute churn metrics for a list of files.

    Args:
        repo_path: Absolute path to the git repository.
        file_paths: Relative file paths to analyze.
        max_commits: Maximum commits to scan per file.

    Returns:
        Dict with per-file metrics and repo-level summary.
    """
    results: list[dict[str, Any]] = []
    files_with_churn = 0

    for file_path in file_paths:
        churn = git_file_churn(repo_path, file_path, max_commits)
        total_loc = _count_lines(repo_path, file_path)

        relative_churn = (
            churn["lines_added"] / total_loc if total_loc > 0 else 0.0
        )
        relative_deleted = (
            churn["lines_deleted"] / total_loc if total_loc > 0 else 0.0
        )

        if churn["churn_count"] > 0:
            files_with_churn += 1

        results.append({
            "filePath": file_path,
            "churnCount": churn["churn_count"],
            "linesAdded": churn["lines_added"],
            "linesDeleted": churn["lines_deleted"],
            "totalLoc": total_loc,
            "relativeChurn": round(relative_churn, 4),
            "relativeDeleted": round(relative_deleted, 4),
        })

    results.sort(key=lambda r: r["churnCount"], reverse=True)
    total_files = len(file_paths)
    files_churned_ratio = (
        files_with_churn / total_files if total_files > 0 else 0.0
    )

    return {
        "files": results,
        "repoLevel": {
            "totalFiles": total_files,
            "filesWithChurn": files_with_churn,
            "filesChurnedRatio": round(files_churned_ratio, 4),
        },
        "citation": "Nagappan & Ball 2005, ICSE",
    }


def _count_lines(repo_path: str, file_path: str) -> int:
    """Count lines in a file. Returns 0 if file not readable."""
    full_path = os.path.join(repo_path, file_path)
    try:
        with open(full_path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0
