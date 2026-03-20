from __future__ import annotations

import os

from ..storage.repo_manager import find_repo
from ..storage.git import is_git_repo, get_current_commit


def status_command() -> None:
    cwd = os.getcwd()
    if not is_git_repo(cwd):
        print("Not a git repository.")
        return
    repo = find_repo(cwd)
    if not repo:
        print("Repository not indexed.")
        print("Run: ai-codebase-intelligence analyze")
        return
    current = get_current_commit(repo["repoPath"])
    indexed = (repo.get("meta") or {}).get("lastCommit", "")
    up_to_date = current == indexed
    print(f"Repository: {repo['repoPath']}")
    print(f"Indexed: {(repo.get('meta') or {}).get('indexedAt', '')}")
    print(f"Indexed commit: {indexed[:7]}")
    print(f"Current commit: {current[:7]}")
    print(f"Status: {'up-to-date' if up_to_date else 'stale (re-run analyze)'}")
