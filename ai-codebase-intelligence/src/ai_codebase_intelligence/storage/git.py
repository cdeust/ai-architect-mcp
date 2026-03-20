from __future__ import annotations

import os
import subprocess


def is_git_repo(repo_path: str) -> bool:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path, capture_output=True, check=True,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def get_current_commit(repo_path: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return ""


def get_git_root(from_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=from_path, capture_output=True, text=True, check=True,
        )
        raw = result.stdout.strip()
        return os.path.abspath(raw)
    except (subprocess.CalledProcessError, OSError):
        return None
