"""Wiki command."""
from __future__ import annotations

import os
import sys
from typing import Any

from ..storage.git import get_git_root, is_git_repo
from ..storage.repo_manager import get_storage_paths, load_meta
from ..core.wiki.generator import WikiGenerator
from ..core.wiki.llm_client import resolve_llm_config


def wiki_command(
    input_path: str = "",
    force: bool = False,
    model: str = "",
    api_key: str = "",
    concurrency: int = 3,
) -> None:
    print("\n  Wiki Generator\n")

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
    meta = load_meta(paths["storagePath"])

    if not meta:
        print("  Repository not indexed. Run: analyze\n")
        return

    overrides: dict[str, Any] = {}
    if model:
        overrides["model"] = model
    if api_key:
        overrides["apiKey"] = api_key

    llm_config = resolve_llm_config(overrides)

    if not llm_config.get("apiKey"):
        key = input("  Enter LLM API key: ").strip()
        if not key:
            print("  API key required for wiki generation.\n")
            return
        llm_config["apiKey"] = key
        from ..storage.repo_manager import save_cli_config
        save_cli_config({"apiKey": key})

    kuzu_path = os.path.join(paths["storagePath"], "kuzu")

    def on_progress(phase: str, percent: int, detail: str) -> None:
        print(f"  [{phase}] {percent}% {detail}")

    generator = WikiGenerator(
        repo_path=repo_path,
        storage_path=paths["storagePath"],
        kuzu_path=kuzu_path,
        llm_config=llm_config,
        options={"force": force, "concurrency": concurrency},
        on_progress=on_progress,
    )

    result = generator.run()

    print(f"\n  Wiki generated: {result['pagesGenerated']} pages ({result['mode']})")
    if result.get("failedModules"):
        print(f"  Failed: {', '.join(result['failedModules'])}")
    print(f"  Output: {paths['storagePath']}/wiki/\n")
