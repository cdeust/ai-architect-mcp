"""Clean command."""
from __future__ import annotations

import os
import shutil

from ..storage.repo_manager import find_repo, unregister_repo, list_registered_repos


def clean_command(all_repos: bool = False, force: bool = False) -> None:
    if all_repos:
        entries = list_registered_repos()
        if not entries:
            print("No indexed repositories found.")
            return
        if not force:
            print(f"This will delete indexes for {len(entries)} repo(s):")
            for e in entries:
                print(f"  - {e['name']} ({e['path']})")
            print("\nRun with --force to confirm deletion.")
            return
        for e in entries:
            try:
                shutil.rmtree(e.get("storagePath", ""), ignore_errors=True)
                unregister_repo(e["path"])
                print(f"Deleted: {e['name']} ({e.get('storagePath', '')})")
            except Exception as err:
                print(f"Failed to delete {e['name']}: {err}")
        return

    cwd = os.getcwd()
    repo = find_repo(cwd)
    if not repo:
        print("No indexed repository found in this directory.")
        return

    repo_name = os.path.basename(repo["repoPath"])
    if not force:
        print(f"This will delete the index for: {repo_name}")
        print(f"   Path: {repo['storagePath']}")
        print("\nRun with --force to confirm deletion.")
        return

    try:
        shutil.rmtree(repo["storagePath"], ignore_errors=True)
        unregister_repo(repo["repoPath"])
        print(f"Deleted: {repo['storagePath']}")
    except Exception as err:
        print(f"Failed to delete: {err}")
