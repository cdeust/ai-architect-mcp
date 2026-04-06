"""Analyze command."""
from __future__ import annotations

import os
import time
from typing import Any

from ..storage.repo_manager import (
    get_storage_paths, save_meta, load_meta,
    add_to_gitignore, register_repo,
)
from ..storage.git import get_current_commit, is_git_repo, get_git_root
from ..core.ingestion.pipeline import run_pipeline_from_repo
from ..core.storage.repo_store import store_and_index


def analyze_command(input_path: str = "", force: bool = False, embeddings: bool = False) -> None:
    print("\n  Codebase Intelligence Analyzer\n")

    if input_path:
        repo_path = os.path.abspath(input_path)
    else:
        git_root = get_git_root(os.getcwd())
        if not git_root:
            print("  Not inside a git repository\n")
            return
        repo_path = git_root

    if not is_git_repo(repo_path):
        print("  Not a git repository\n")
        return

    paths = get_storage_paths(repo_path)
    current_commit = get_current_commit(repo_path)
    existing_meta = load_meta(paths["storagePath"])

    if existing_meta and not force and existing_meta.get("lastCommit") == current_commit:
        print("  Already up to date\n")
        return

    t0 = time.time()

    # Phase 1: Pipeline
    print("  Running pipeline...")
    result = run_pipeline_from_repo(repo_path, lambda p: print(f"  [{p.get('phase', '')}] {p.get('percent', 0)}% {p.get('message', '')}"))

    graph = result["graph"]

    # Phase 2: SQLite persistence
    print("  Storing to SQLite...")
    db_path = os.path.join(paths["storagePath"], "index.db")
    os.makedirs(paths["storagePath"], exist_ok=True)
    repo_name = os.path.basename(repo_path).lower()
    db_stats = store_and_index(repo_name, db_path, graph)
    stats = {"nodes": db_stats["nodes"], "edges": db_stats["relationships"]}

    # Phase 3: Save metadata
    meta: dict[str, Any] = {
        "repoPath": repo_path,
        "lastCommit": current_commit,
        "indexedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats": {
            "files": result["totalFileCount"],
            "nodes": stats["nodes"],
            "edges": stats["edges"],
            "communities": result["communityResult"]["stats"]["totalCommunities"],
            "processes": result["processResult"]["stats"]["totalProcesses"],
        },
    }
    save_meta(paths["storagePath"], meta)
    register_repo(repo_path, meta)
    add_to_gitignore(repo_path)

    total_time = time.time() - t0
    s = meta["stats"]
    print(f"\n  Repository indexed successfully ({total_time:.1f}s)\n")
    print(f"  {s['nodes']} nodes | {s['edges']} edges | {s['communities']} clusters | {s['processes']} flows")
    print(f"  {repo_path}\n")
