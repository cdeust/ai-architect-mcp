from __future__ import annotations

from ..storage.repo_manager import list_registered_repos


def list_command() -> None:
    entries = list_registered_repos(validate=True)
    if not entries:
        print("No indexed repositories found.")
        print("Run `ai-codebase-intelligence analyze` in a git repo to index it.")
        return
    print(f"\n  Indexed Repositories ({len(entries)})\n")
    for entry in entries:
        stats = entry.get("stats", {})
        commit = (entry.get("lastCommit") or "unknown")[:7]
        print(f"  {entry['name']}")
        print(f"    Path:    {entry['path']}")
        print(f"    Indexed: {entry.get('indexedAt', '')}")
        print(f"    Commit:  {commit}")
        print(f"    Stats:   {stats.get('files', 0)} files, {stats.get('nodes', 0)} symbols, {stats.get('edges', 0)} edges")
        if stats.get("communities"):
            print(f"    Clusters:   {stats['communities']}")
        if stats.get("processes"):
            print(f"    Processes:  {stats['processes']}")
        print("")
