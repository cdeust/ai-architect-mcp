"""Local backend — 1:1 port of gitnexus mcp/local/local-backend.js (init, resolve, dispatch)."""
from __future__ import annotations

import os
import re
from typing import Any

from ...storage.repo_manager import list_registered_repos
from ...core.storage.repo_store import (
    init_repo, get_index, get_store, search_fts, query_sql,
    is_ready, close_all,
)

VALID_NODE_LABELS: frozenset[str] = frozenset({
    "File", "Folder", "Function", "Class", "Interface", "Method", "CodeElement",
    "Community", "Process", "Contributor", "Struct", "Enum", "Macro", "Typedef",
    "Union", "Namespace", "Trait", "Impl", "TypeAlias", "Const", "Static",
    "Property", "Record", "Delegate", "Annotation", "Constructor", "Template",
    "Module",
})

VALID_RELATION_TYPES: frozenset[str] = frozenset({
    "CALLS", "IMPORTS", "EXTENDS", "IMPLEMENTS", "AUTHORED_BY", "CO_CHANGES_WITH",
})

CYPHER_WRITE_RE = re.compile(r"\b(CREATE|DELETE|SET|MERGE|REMOVE|DROP|ALTER|COPY|DETACH)\b", re.I)


def is_test_file_path(file_path: str) -> bool:
    p = file_path.lower().replace("\\", "/")
    return (".test." in p or ".spec." in p or "__tests__/" in p or "__mocks__/" in p
            or "/test/" in p or "/tests/" in p or "/testing/" in p or "/fixtures/" in p
            or p.endswith("_test.go") or p.endswith("_test.py")
            or "/test_" in p or "/conftest." in p)


class LocalBackend:
    def __init__(self) -> None:
        self.repos: dict[str, dict[str, Any]] = {}
        self.context_cache: dict[str, dict[str, Any]] = {}
        self.initialized_repos: set[str] = set()

    async def init(self) -> bool:
        await self.refresh_repos()
        return len(self.repos) > 0

    async def refresh_repos(self) -> None:
        entries = list_registered_repos(validate=True)
        fresh_ids: set[str] = set()
        for entry in entries:
            rid = self._repo_id(entry["name"], entry["path"])
            fresh_ids.add(rid)
            storage_path = entry.get("storagePath", "")
            kuzu_path = os.path.join(storage_path, "kuzu")
            self.repos[rid] = {
                "id": rid, "name": entry["name"],
                "repoPath": entry["path"], "storagePath": storage_path,
                "kuzuPath": kuzu_path, "indexedAt": entry.get("indexedAt", ""),
                "lastCommit": entry.get("lastCommit", ""),
                "stats": entry.get("stats", {}),
            }
            s = entry.get("stats", {})
            self.context_cache[rid] = {
                "projectName": entry["name"],
                "stats": {
                    "fileCount": s.get("files", 0),
                    "functionCount": s.get("nodes", 0),
                    "communityCount": s.get("communities", 0),
                    "processCount": s.get("processes", 0),
                },
            }
        for rid in list(self.repos.keys()):
            if rid not in fresh_ids:
                self.repos.pop(rid, None)
                self.context_cache.pop(rid, None)
                self.initialized_repos.discard(rid)

    def _repo_id(self, name: str, repo_path: str) -> str:
        base = name.lower()
        for rid, handle in self.repos.items():
            if rid == base and handle["repoPath"] != os.path.abspath(repo_path):
                import hashlib
                h = hashlib.sha256(repo_path.encode()).hexdigest()[:6]
                return f"{base}-{h}"
        return base

    async def resolve_repo(self, repo_param: str | None = None) -> dict[str, Any]:
        result = self._resolve_from_cache(repo_param)
        if result:
            return result
        await self.refresh_repos()
        result = self._resolve_from_cache(repo_param)
        if result:
            return result
        if not self.repos:
            raise RuntimeError("No indexed repositories.")
        if repo_param:
            names = [h["name"] for h in self.repos.values()]
            raise RuntimeError(f"Repo '{repo_param}' not found. Available: {names}")
        raise RuntimeError("Multiple repos indexed. Specify repo parameter.")

    def _resolve_from_cache(self, repo_param: str | None) -> dict[str, Any] | None:
        if repo_param:
            rp = repo_param.lower()
            for rid, handle in self.repos.items():
                if rid == rp or handle["name"].lower() == rp:
                    return handle
                if os.path.abspath(handle["repoPath"]) == os.path.abspath(repo_param):
                    return handle
            return None
        if len(self.repos) == 1:
            return next(iter(self.repos.values()))
        return None

    async def ensure_initialized(self, repo_id: str) -> None:
        if repo_id in self.initialized_repos:
            return
        handle = self.repos.get(repo_id)
        if not handle:
            raise RuntimeError(f"Repo {repo_id} not registered.")
        db_path = os.path.join(handle["storagePath"], "index.db")
        init_repo(repo_id, db_path)
        self.initialized_repos.add(repo_id)

    def get_context(self, repo_id: str | None = None) -> dict[str, Any] | None:
        if repo_id:
            return self.context_cache.get(repo_id)
        if len(self.context_cache) == 1:
            return next(iter(self.context_cache.values()))
        return None

    async def list_repos(self) -> list[dict[str, Any]]:
        await self.refresh_repos()
        return [
            {"name": h["name"], "path": h["repoPath"],
             "indexedAt": h["indexedAt"], "lastCommit": h["lastCommit"],
             "stats": h["stats"]}
            for h in self.repos.values()
        ]

    async def call_tool(self, method: str, params: dict[str, Any]) -> Any:
        if method == "list_repos":
            return await self.list_repos()
        repo = await self.resolve_repo(params.get("repo"))
        if method == "query":
            from .local_backend_query import query_tool
            return await query_tool(self, repo, params)
        if method == "cypher":
            return await self._cypher(repo, params)
        if method == "context":
            from .local_backend_context import context_tool
            return await context_tool(self, repo, params)
        if method == "impact":
            from .local_backend_impact import impact_tool
            return await impact_tool(self, repo, params)
        if method == "detect_changes":
            from .local_backend_changes import detect_changes_tool
            return await detect_changes_tool(self, repo, params)
        if method == "rename":
            from .local_backend_rename import rename_tool
            return await rename_tool(self, repo, params)
        if method == "ownership":
            from .local_backend_ownership import ownership_tool
            return await ownership_tool(self, repo, params)
        if method == "bus_factor":
            from .local_backend_bus_factor import bus_factor_tool
            return await bus_factor_tool(self, repo, params)
        if method == "churn":
            from .local_backend_churn import churn_tool
            return await churn_tool(self, repo, params)
        if method == "cochange":
            from .local_backend_cochange import cochange_tool
            return await cochange_tool(self, repo, params)
        if method == "dead_code":
            from .local_backend_dead_code import dead_code_tool
            return await dead_code_tool(self, repo, params)
        raise RuntimeError(f"Unknown tool: {method}")

    async def _cypher(self, repo: dict[str, Any], params: dict[str, Any]) -> Any:
        await self.ensure_initialized(repo["id"])
        sql = params.get("query", "")
        if CYPHER_WRITE_RE.search(sql):
            return {"error": "Write operations not allowed. Graph is read-only."}
        try:
            rows = query_sql(repo["id"], sql)
            return self._format_cypher_markdown(rows)
        except Exception as e:
            return {"error": str(e)}

    def _format_cypher_markdown(self, result: list[dict[str, Any]]) -> Any:
        if not result:
            return result
        first = result[0]
        if not isinstance(first, dict):
            return result
        keys = list(first.keys())
        if not keys:
            return result
        header = "| " + " | ".join(keys) + " |"
        sep = "| " + " | ".join("---" for _ in keys) + " |"
        rows = []
        for row in result:
            cells = []
            for k in keys:
                v = row.get(k)
                if v is None:
                    cells.append("")
                elif isinstance(v, dict):
                    import json
                    cells.append(json.dumps(v))
                else:
                    cells.append(str(v))
            rows.append("| " + " | ".join(cells) + " |")
        return {"markdown": "\n".join([header, sep, *rows]), "row_count": len(result)}

    async def disconnect(self) -> None:
        close_all()
        self.repos.clear()
        self.context_cache.clear()
        self.initialized_repos.clear()

    # Resource query helpers — delegated to local_backend_resources.py
    async def query_clusters(self, repo_name: str, limit: int = 100) -> dict[str, Any]:
        from .local_backend_resources import query_clusters
        return await query_clusters(self, repo_name, limit)

    async def query_processes(self, repo_name: str, limit: int = 50) -> dict[str, Any]:
        from .local_backend_resources import query_processes
        return await query_processes(self, repo_name, limit)

    async def query_cluster_detail(self, name: str, repo_name: str) -> dict[str, Any]:
        from .local_backend_resources import query_cluster_detail
        return await query_cluster_detail(self, name, repo_name)

    async def query_process_detail(self, name: str, repo_name: str) -> dict[str, Any]:
        from .local_backend_resources import query_process_detail
        return await query_process_detail(self, name, repo_name)
