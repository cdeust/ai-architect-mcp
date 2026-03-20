"""Hook implementation for codebase intelligence.

PreToolUse: augment Grep/Glob/Bash with graph context.
PostToolUse: auto-reindex on git commit/merge detection.
"""

from __future__ import annotations

import json
import sys


def augment() -> None:
    """Augment tool inputs with graph context.

    Reads tool input from stdin, enriches with relevant
    symbol context from the graph, outputs augmented input.
    """
    try:
        tool_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    file_path = tool_input.get("file_path", "") or tool_input.get("pattern", "")
    if not file_path:
        json.dump(tool_input, sys.stdout)
        return

    try:
        import asyncio
        from ai_codebase_intelligence._augmentation.engine import (
            GrepResult,
            augment_grep_results,
        )
        from ai_codebase_intelligence._storage.factory import create_graph_storage
        from ai_codebase_intelligence._storage.repo_manager import get_repo_db_path

        repo_path = tool_input.get("repo_path", ".")
        db_path = get_repo_db_path(repo_path)
        if db_path is None:
            json.dump(tool_input, sys.stdout)
            return

        storage = create_graph_storage(db_path)
        grep_result = GrepResult(
            file_path=file_path,
            line_number=int(tool_input.get("line_number", 1)),
            line_content=file_path,
            match_text=file_path,
        )
        enriched = asyncio.run(
            augment_grep_results([grep_result], storage)
        )
        if enriched:
            item = enriched[0]
            tool_input["_augmented"] = {
                "symbol_name": item.symbol_name,
                "symbol_kind": item.symbol_kind,
                "callers": item.callers,
                "processes": item.processes,
            }
    except ImportError:
        pass

    json.dump(tool_input, sys.stdout)


def reindex() -> None:
    """Check if a git commit occurred and trigger reindex.

    Monitors Bash tool outputs for git commit/merge patterns.
    When detected, schedules an incremental reindex.
    """
    try:
        tool_output = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    output_text = str(tool_output.get("output", ""))

    commit_patterns = [
        "create mode",
        "files changed",
        "insertions(+)",
        "deletions(-)",
        "Merge made by",
    ]

    for pattern in commit_patterns:
        if pattern in output_text:
            print(
                json.dumps(
                    {"reindex_needed": True, "trigger": pattern}
                )
            )
            return

    sys.exit(0)


def main() -> None:
    """Entry point — dispatch based on command."""
    if len(sys.argv) < 2:
        sys.exit(1)

    command = sys.argv[1]
    if command == "augment":
        augment()
    elif command == "reindex":
        reindex()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
