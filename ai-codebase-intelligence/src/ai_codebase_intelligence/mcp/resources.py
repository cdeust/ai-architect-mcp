"""MCP Resources — 1:1 port of gitnexus mcp/resources.js."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

from .staleness import check_staleness


def get_resource_definitions() -> list[dict[str, str]]:
    return [
        {"uri": "codebase://repos", "name": "All Indexed Repositories",
         "description": "List of all indexed repos with stats.", "mimeType": "text/yaml"},
        {"uri": "codebase://setup", "name": "Setup Content",
         "description": "Returns AGENTS.md content for all indexed repos.", "mimeType": "text/markdown"},
    ]


def get_resource_templates() -> list[dict[str, str]]:
    return [
        {"uriTemplate": "codebase://repo/{name}/context", "name": "Repo Overview", "mimeType": "text/yaml"},
        {"uriTemplate": "codebase://repo/{name}/clusters", "name": "Repo Modules", "mimeType": "text/yaml"},
        {"uriTemplate": "codebase://repo/{name}/processes", "name": "Repo Processes", "mimeType": "text/yaml"},
        {"uriTemplate": "codebase://repo/{name}/schema", "name": "Graph Schema", "mimeType": "text/yaml"},
        {"uriTemplate": "codebase://repo/{name}/cluster/{clusterName}", "name": "Module Detail", "mimeType": "text/yaml"},
        {"uriTemplate": "codebase://repo/{name}/process/{processName}", "name": "Process Trace", "mimeType": "text/yaml"},
    ]


def _parse_uri(uri: str) -> dict[str, str]:
    if uri == "codebase://repos":
        return {"resourceType": "repos"}
    if uri == "codebase://setup":
        return {"resourceType": "setup"}
    m = re.match(r"^codebase://repo/([^/]+)/(.+)$", uri)
    if m:
        repo_name = unquote(m.group(1))
        rest = m.group(2)
        if rest.startswith("cluster/"):
            return {"repoName": repo_name, "resourceType": "cluster", "param": unquote(rest[8:])}
        if rest.startswith("process/"):
            return {"repoName": repo_name, "resourceType": "process", "param": unquote(rest[8:])}
        return {"repoName": repo_name, "resourceType": rest}
    raise ValueError(f"Unknown resource URI: {uri}")


async def read_resource(uri: str, backend: Any) -> str:
    parsed = _parse_uri(uri)
    if parsed["resourceType"] == "repos":
        return await _get_repos_resource(backend)
    if parsed["resourceType"] == "setup":
        return await _get_setup_resource(backend)
    repo_name = parsed.get("repoName", "")
    rt = parsed["resourceType"]
    if rt == "context":
        return await _get_context_resource(backend, repo_name)
    if rt == "clusters":
        return await _get_clusters_resource(backend, repo_name)
    if rt == "processes":
        return await _get_processes_resource(backend, repo_name)
    if rt == "schema":
        return _get_schema_resource()
    if rt == "cluster":
        return await _get_cluster_detail_resource(parsed.get("param", ""), backend, repo_name)
    if rt == "process":
        return await _get_process_detail_resource(parsed.get("param", ""), backend, repo_name)
    raise ValueError(f"Unknown resource: {uri}")


async def _get_repos_resource(backend: Any) -> str:
    repos = await backend.list_repos()
    if not repos:
        return "repos: []\n# No repositories indexed."
    lines = ["repos:"]
    for repo in repos:
        lines.append(f'  - name: "{repo["name"]}"')
        lines.append(f'    path: "{repo["path"]}"')
        lines.append(f'    indexed: "{repo.get("indexedAt", "")}"')
        lines.append(f'    commit: "{(repo.get("lastCommit") or "unknown")[:7]}"')
        stats = repo.get("stats", {})
        if stats:
            lines.append(f'    files: {stats.get("files", 0)}')
            lines.append(f'    symbols: {stats.get("nodes", 0)}')
            lines.append(f'    processes: {stats.get("processes", 0)}')
    return "\n".join(lines)


async def _get_context_resource(backend: Any, repo_name: str) -> str:
    repo = await backend.resolve_repo(repo_name)
    context = backend.get_context(repo["name"].lower()) or backend.get_context()
    if not context:
        return "error: No codebase loaded."
    staleness = check_staleness(repo.get("repoPath", ""), repo.get("lastCommit", "HEAD"))
    lines = [f'project: {context["projectName"]}']
    if staleness.get("isStale") and staleness.get("hint"):
        lines.append("")
        lines.append(f'staleness: "{staleness["hint"]}"')
    lines.append("")
    lines.append("stats:")
    lines.append(f'  files: {context["stats"]["fileCount"]}')
    lines.append(f'  symbols: {context["stats"]["functionCount"]}')
    lines.append(f'  processes: {context["stats"]["processCount"]}')
    return "\n".join(lines)


async def _get_clusters_resource(backend: Any, repo_name: str) -> str:
    result = await backend.query_clusters(repo_name, 100)
    clusters = result.get("clusters", [])
    if not clusters:
        return "modules: []\n# No functional areas detected."
    lines = ["modules:"]
    for c in clusters[:20]:
        label = c.get("heuristicLabel") or c.get("label") or c.get("id")
        lines.append(f'  - name: "{label}"')
        lines.append(f'    symbols: {c.get("symbolCount", 0)}')
        if c.get("cohesion"):
            lines.append(f'    cohesion: {int(c["cohesion"] * 100)}%')
    return "\n".join(lines)


async def _get_processes_resource(backend: Any, repo_name: str) -> str:
    result = await backend.query_processes(repo_name, 50)
    processes = result.get("processes", [])
    if not processes:
        return "processes: []\n# No processes detected."
    lines = ["processes:"]
    for p in processes[:20]:
        label = p.get("heuristicLabel") or p.get("label") or p.get("id")
        lines.append(f'  - name: "{label}"')
        lines.append(f'    type: {p.get("processType", "unknown")}')
        lines.append(f'    steps: {p.get("stepCount", 0)}')
    return "\n".join(lines)


def _get_schema_resource() -> str:
    return """# Graph Schema

nodes:
  - File, Folder, Function, Class, Interface, Method, CodeElement
  - Community (Leiden clusters), Process (execution flows)
  - Multi-language: Struct, Enum, Macro, Typedef, Union, Namespace, Trait, Impl, TypeAlias, Const, Static, Property, Record, Delegate, Annotation, Constructor, Template, Module

relationships:
  All via single CodeRelation table with type property.
  Types: CONTAINS, DEFINES, CALLS, IMPORTS, EXTENDS, IMPLEMENTS, MEMBER_OF, STEP_IN_PROCESS
  Properties: type (STRING), confidence (DOUBLE), reason (STRING), step (INT32)

example_queries:
  find_callers: |
    MATCH (caller)-[:CodeRelation {type: 'CALLS'}]->(f:Function {name: "myFunc"})
    RETURN caller.name, caller.filePath
"""


async def _get_cluster_detail_resource(name: str, backend: Any, repo_name: str) -> str:
    result = await backend.query_cluster_detail(name, repo_name)
    if result.get("error"):
        return f"error: {result['error']}"
    cluster = result.get("cluster", {})
    members = result.get("members", [])
    lines = [
        f'module: "{cluster.get("heuristicLabel") or cluster.get("label") or cluster.get("id")}"',
        f'symbols: {cluster.get("symbolCount") or len(members)}',
    ]
    if members:
        lines.append("")
        lines.append("members:")
        for m in members[:20]:
            lines.append(f"  - name: {m['name']}")
            lines.append(f"    type: {m['type']}")
            lines.append(f"    file: {m['filePath']}")
    return "\n".join(lines)


async def _get_process_detail_resource(name: str, backend: Any, repo_name: str) -> str:
    result = await backend.query_process_detail(name, repo_name)
    if result.get("error"):
        return f"error: {result['error']}"
    proc = result.get("process", {})
    steps = result.get("steps", [])
    lines = [
        f'name: "{proc.get("heuristicLabel") or proc.get("label") or proc.get("id")}"',
        f'type: {proc.get("processType", "unknown")}',
        f'step_count: {proc.get("stepCount") or len(steps)}',
    ]
    if steps:
        lines.append("")
        lines.append("trace:")
        for s in steps:
            lines.append(f"  {s['step']}: {s['name']} ({s['filePath']})")
    return "\n".join(lines)


async def _get_setup_resource(backend: Any) -> str:
    repos = await backend.list_repos()
    if not repos:
        return "# Codebase Intelligence\n\nNo repositories indexed."
    sections = []
    for repo in repos:
        stats = repo.get("stats", {})
        lines = [
            f"# Codebase Intelligence — {repo['name']}",
            "",
            f"Indexed: {stats.get('nodes', 0)} symbols, {stats.get('edges', 0)} relationships, {stats.get('processes', 0)} flows.",
            "",
            "## Tools",
            "| Tool | Description |",
            "|------|-------------|",
            "| query | Process-grouped code intelligence |",
            "| context | 360-degree symbol view |",
            "| impact | Blast radius analysis |",
            "| detect_changes | Git-diff impact |",
            "| rename | Multi-file coordinated rename |",
            "| cypher | Raw graph queries |",
        ]
        sections.append("\n".join(lines))
    return "\n\n---\n\n".join(sections)
