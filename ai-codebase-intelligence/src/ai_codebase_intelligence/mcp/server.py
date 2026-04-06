"""MCP Server. Uses fastmcp."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastmcp import FastMCP

from .local.local_backend import LocalBackend
from .resources import read_resource, get_resource_definitions, get_resource_templates

logger = logging.getLogger(__name__)

NEXT_STEP_HINTS: dict[str, str] = {
    "list_repos": "\n\n---\n**Next:** READ codebase://repo/{name}/context for any repo above.",
    "query": "\n\n---\n**Next:** Use context(name: \"<symbol>\") for 360-degree view.",
    "context": "\n\n---\n**Next:** Use impact(target: \"<name>\", direction: \"upstream\") to check blast radius.",
    "impact": "\n\n---\n**Next:** Review d=1 items first (WILL BREAK).",
    "detect_changes": "\n\n---\n**Next:** Review affected processes. Use context() on high-risk symbols.",
    "rename": "\n\n---\n**Next:** Run detect_changes() to verify no unexpected side effects.",
    "cypher": "\n\n---\n**Next:** Use context(name: \"<name>\") to explore a result symbol.",
}

backend = LocalBackend()
mcp = FastMCP("ai-codebase-intelligence")


@mcp.tool(name="ai_architect_codebase_list_repos", description="List indexed repositories")
async def tool_list_repos() -> str:
    result = await backend.call_tool("list_repos", {})
    return json.dumps(result, indent=2) + NEXT_STEP_HINTS.get("list_repos", "")


@mcp.tool(name="ai_architect_codebase_query", description="Hybrid search: BM25 + process ranking")
async def tool_query(query: str, repo: str = "", limit: int = 5, max_symbols: int = 10, include_content: bool = False) -> str:
    result = await backend.call_tool("query", {"query": query, "repo": repo or None, "limit": limit, "max_symbols": max_symbols, "include_content": include_content})
    return json.dumps(result, indent=2) + NEXT_STEP_HINTS.get("query", "")


@mcp.tool(name="ai_architect_codebase_context", description="360 degree symbol view")
async def tool_context(name: str = "", uid: str = "", file_path: str = "", include_content: bool = False, repo: str = "") -> str:
    result = await backend.call_tool("context", {"name": name, "uid": uid, "file_path": file_path, "include_content": include_content, "repo": repo or None})
    return json.dumps(result, indent=2) + NEXT_STEP_HINTS.get("context", "")


@mcp.tool(name="ai_architect_codebase_impact", description="Blast radius analysis")
async def tool_impact(target: str, direction: str = "upstream", maxDepth: int = 3, repo: str = "") -> str:
    result = await backend.call_tool("impact", {"target": target, "direction": direction, "maxDepth": maxDepth, "repo": repo or None})
    return json.dumps(result, indent=2) + NEXT_STEP_HINTS.get("impact", "")


@mcp.tool(name="ai_architect_codebase_detect_changes", description="Git diff to affected symbols and processes")
async def tool_detect_changes(repo: str = "", scope: str = "unstaged", base_ref: str = "") -> str:
    result = await backend.call_tool("detect_changes", {"scope": scope, "base_ref": base_ref, "repo": repo or None})
    return json.dumps(result, indent=2) + NEXT_STEP_HINTS.get("detect_changes", "")


@mcp.tool(name="ai_architect_codebase_cypher", description="Raw Cypher queries (read-only)")
async def tool_cypher(query: str, repo: str = "") -> str:
    result = await backend.call_tool("cypher", {"query": query, "repo": repo or None})
    return json.dumps(result, indent=2) + NEXT_STEP_HINTS.get("cypher", "")


@mcp.tool(name="ai_architect_codebase_rename", description="Multi-file coordinated rename")
async def tool_rename(new_name: str, symbol_name: str = "", symbol_uid: str = "", dry_run: bool = True, repo: str = "") -> str:
    result = await backend.call_tool("rename", {"new_name": new_name, "symbol_name": symbol_name, "symbol_uid": symbol_uid, "dry_run": dry_run, "repo": repo or None})
    return json.dumps(result, indent=2) + NEXT_STEP_HINTS.get("rename", "")


@mcp.tool(name="ai_architect_codebase_analyze", description="Index a repository")
async def tool_analyze(repo_path: str, force: bool = False) -> str:
    from ..core.ingestion.pipeline import run_pipeline_from_repo
    from ..storage.repo_manager import register_repo, get_storage_paths
    from ..storage.git import get_current_commit
    from ..core.storage.repo_store import store_and_index
    import os, time

    start = time.monotonic()
    result = run_pipeline_from_repo(repo_path)
    graph = result["graph"]
    duration = time.monotonic() - start

    paths = get_storage_paths(repo_path)
    commit = get_current_commit(repo_path)
    db_path = os.path.join(paths["storagePath"], "index.db")
    os.makedirs(paths["storagePath"], exist_ok=True)
    repo_name = os.path.basename(repo_path).lower()
    store_and_index(repo_name, db_path, graph)

    stats = {
        "files": result["totalFileCount"],
        "nodes": graph.node_count,
        "edges": graph.relationship_count,
        "communities": result["communityResult"]["stats"]["totalCommunities"],
        "processes": result["processResult"]["stats"]["totalProcesses"],
    }
    register_repo(repo_path, {"indexedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "lastCommit": commit, "stats": stats})

    return json.dumps({
        "repo_path": repo_path, "total_files": stats["files"],
        "total_nodes": stats["nodes"], "total_relationships": stats["edges"],
        "total_communities": stats["communities"], "total_processes": stats["processes"],
        "duration_seconds": round(duration, 2),
    }, indent=2)


# Resources
@mcp.resource("codebase://repos")
async def resource_repos() -> str:
    return await read_resource("codebase://repos", backend)

@mcp.resource("codebase://setup")
async def resource_setup() -> str:
    return await read_resource("codebase://setup", backend)

@mcp.resource("codebase://repo/{name}/context")
async def resource_context(name: str) -> str:
    return await read_resource(f"codebase://repo/{name}/context", backend)

@mcp.resource("codebase://repo/{name}/clusters")
async def resource_clusters(name: str) -> str:
    return await read_resource(f"codebase://repo/{name}/clusters", backend)

@mcp.resource("codebase://repo/{name}/processes")
async def resource_processes(name: str) -> str:
    return await read_resource(f"codebase://repo/{name}/processes", backend)

@mcp.resource("codebase://schema")
async def resource_schema() -> str:
    return await read_resource("codebase://schema", backend)

@mcp.resource("codebase://repo/{name}/cluster/{cluster}")
async def resource_cluster(name: str, cluster: str) -> str:
    return await read_resource(f"codebase://repo/{name}/cluster/{cluster}", backend)

@mcp.resource("codebase://repo/{name}/process/{process}")
async def resource_process(name: str, process: str) -> str:
    return await read_resource(f"codebase://repo/{name}/process/{process}", backend)


# Prompts
@mcp.prompt("detect_impact")
async def prompt_detect_impact(scope: str = "all", base_ref: str = "") -> str:
    return f"""Analyze the impact of my current code changes before committing.

1. Run `git diff {base_ref or 'HEAD'} --name-only` to get changed files
2. Run detect_changes with those files
3. For each changed symbol in critical processes, run context()
4. For high-risk items, run impact(direction: "upstream")
5. Summarize: changes, affected processes, risk level, actions"""


@mcp.prompt("generate_map")
async def prompt_generate_map(repo: str = "") -> str:
    r = repo or "{name}"
    return f"""Generate architecture documentation from the knowledge graph.

1. READ codebase://repo/{r}/context
2. READ codebase://repo/{r}/clusters
3. READ codebase://repo/{r}/processes
4. For top 5 processes, READ codebase://repo/{r}/process/{{name}}
5. Generate mermaid architecture diagram
6. Write ARCHITECTURE.md"""


def main() -> None:
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(backend.init())
    mcp.run()


if __name__ == "__main__":
    main()
