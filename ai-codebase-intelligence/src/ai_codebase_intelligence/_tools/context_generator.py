"""Generate AI context files (AGENTS.md, CLAUDE.md) for a repository.

Pure functions that produce markdown strings from repo metadata.
No I/O — callers are responsible for writing to disk.
"""

from __future__ import annotations

_TOOL_DEFINITIONS: list[tuple[str, str]] = [
    ("analyze", "Index a codebase and build the knowledge graph"),
    ("query", "Search for execution flows by keyword or concept"),
    ("context", "360-degree view of a single symbol"),
    ("impact", "Blast radius analysis for a symbol change"),
    ("detect_changes", "Map git changes to affected execution flows"),
    ("cypher", "Execute read-only SQL against the knowledge graph"),
    ("rename", "Multi-file coordinated symbol rename"),
    ("list_repos", "List all indexed repositories"),
]


def generate_agents_md(repo_name: str, tool_count: int) -> str:
    """Generate AGENTS.md content for a repository.

    Args:
        repo_name: Repository name for the title.
        tool_count: Maximum number of tools to include.

    Returns:
        Markdown string for AGENTS.md.
    """
    capped = min(tool_count, len(_TOOL_DEFINITIONS))
    tools = _TOOL_DEFINITIONS[:capped]

    tool_rows = "\n".join(
        f"| `{name}` | {desc} |" for name, desc in tools
    )

    return f"""# {repo_name} — AI Codebase Intelligence

## Available Tools ({capped})

| Tool | Description |
|------|-------------|
{tool_rows}

## Workflow

1. Use `analyze` to index the codebase
2. Use `query` to find relevant execution flows
3. Use `context` for detailed symbol inspection
4. Use `impact` before making changes
5. Use `detect_changes` after modifications

## Boundaries

### Always
- Use `analyze` before other tools on a new codebase
- Check `impact` before refactoring

### When Appropriate
- Use `cypher` for advanced graph queries
- Use `rename` for multi-file refactoring

### Never
- Modify the knowledge graph directly
- Skip impact analysis on critical paths

## Self-Review Checklist

- [ ] Ran `analyze` on current commit
- [ ] Checked `impact` for changed symbols
- [ ] Verified no broken execution flows
- [ ] Reviewed `detect_changes` output
"""


def generate_claude_md(repo_name: str) -> str:
    """Generate CLAUDE.md content for a repository.

    Args:
        repo_name: Repository name.

    Returns:
        Markdown string for CLAUDE.md.
    """
    return f"""# {repo_name} — Codebase Intelligence

## Workflow

1. Index with `ai_architect_codebase_analyze`
2. Search with `ai_architect_codebase_query`
3. Inspect with `ai_architect_codebase_context`
4. Assess with `ai_architect_codebase_impact`

## Quick Reference

- **analyze**: Build knowledge graph from source
- **query**: Hybrid BM25 + process search
- **context**: Symbol-centric 360-degree view
- **impact**: Blast radius analysis
- **detect_changes**: Git diff to graph mapping
- **cypher**: Raw SQL queries
- **rename**: Coordinated multi-file rename
- **list_repos**: Show indexed repositories

## Boundaries

- Read-only by default (rename requires explicit opt-in)
- Write operations blocked in cypher queries
- All tools are scoped to indexed repositories

## Self-Review Checklist

- [ ] Knowledge graph is up to date
- [ ] Impact analysis reviewed before changes
- [ ] No broken execution flows after modification
"""
