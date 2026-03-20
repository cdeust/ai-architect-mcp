"""AI context generator — 1:1 port of gitnexus cli/ai-context.js."""
from __future__ import annotations

import os
from typing import Any

START_MARKER = "<!-- codebase-intelligence:start -->"
END_MARKER = "<!-- codebase-intelligence:end -->"


def _generate_content(project_name: str, stats: dict[str, Any]) -> str:
    return f"""{START_MARKER}
# Codebase Intelligence

This project is indexed as **{project_name}** ({stats.get('nodes', 0)} symbols, {stats.get('edges', 0)} relationships, {stats.get('processes', 0)} execution flows).

## Always Do

- **MUST run impact analysis before editing any symbol.** Run `ai_architect_codebase_impact(target: "symbolName", direction: "upstream")` and report the blast radius.
- **MUST run `ai_architect_codebase_detect_changes()` before committing.**
- When exploring code, use `ai_architect_codebase_query(query: "concept")` to find execution flows.
- For full context on a symbol, use `ai_architect_codebase_context(name: "symbolName")`.

## When Refactoring

- **Renaming**: Use `ai_architect_codebase_rename(symbol_name: "old", new_name: "new", dry_run: true)` first.
- After any refactor: run `ai_architect_codebase_detect_changes(scope: "all")`.

## Never Do

- NEVER edit a symbol without running impact analysis first.
- NEVER ignore HIGH or CRITICAL risk warnings.
- NEVER commit without running detect_changes.

## Tools

| Tool | Command |
|------|---------|
| query | `ai_architect_codebase_query(query: "auth")` |
| context | `ai_architect_codebase_context(name: "validateUser")` |
| impact | `ai_architect_codebase_impact(target: "X", direction: "upstream")` |
| detect_changes | `ai_architect_codebase_detect_changes(scope: "staged")` |
| rename | `ai_architect_codebase_rename(symbol_name: "old", new_name: "new")` |
| cypher | `ai_architect_codebase_cypher(query: "MATCH ...")` |

{END_MARKER}"""


def _upsert_section(file_path: str, content: str) -> str:
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return "created"

    with open(file_path, encoding="utf-8") as f:
        existing = f.read()

    start_idx = existing.find(START_MARKER)
    end_idx = existing.find(END_MARKER)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        before = existing[:start_idx]
        after = existing[end_idx + len(END_MARKER):]
        new_content = before + content + after
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content.strip() + "\n")
        return "updated"

    new_content = existing.strip() + "\n\n" + content + "\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return "appended"


def generate_ai_context_files(
    repo_path: str,
    storage_path: str,
    project_name: str,
    stats: dict[str, Any],
) -> dict[str, list[str]]:
    content = _generate_content(project_name, stats)
    created_files: list[str] = []

    agents_path = os.path.join(repo_path, "AGENTS.md")
    agents_result = _upsert_section(agents_path, content)
    created_files.append(f"AGENTS.md ({agents_result})")

    claude_path = os.path.join(repo_path, "CLAUDE.md")
    claude_result = _upsert_section(claude_path, content)
    created_files.append(f"CLAUDE.md ({claude_result})")

    return {"files": created_files}
