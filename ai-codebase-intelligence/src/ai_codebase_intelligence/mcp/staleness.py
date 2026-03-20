"""Staleness check — 1:1 port of gitnexus mcp/staleness.js."""
from __future__ import annotations

import subprocess
from typing import Any


def check_staleness(repo_path: str, last_commit: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{last_commit}..HEAD"],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
        commits_behind = int(result.stdout.strip()) if result.stdout.strip() else 0
        if commits_behind > 0:
            s = "s" if commits_behind > 1 else ""
            return {
                "isStale": True,
                "commitsBehind": commits_behind,
                "hint": f"Index is {commits_behind} commit{s} behind HEAD. Run analyze tool to update.",
            }
        return {"isStale": False, "commitsBehind": 0}
    except (subprocess.CalledProcessError, OSError, ValueError):
        return {"isStale": False, "commitsBehind": 0}
