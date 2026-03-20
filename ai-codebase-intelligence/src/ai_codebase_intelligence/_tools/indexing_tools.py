"""Indexing MCP tools — atomic phase tools for pipeline orchestration.

Each phase is a separate tool. Claude calls them in sequence via the
indexing skill. If one phase fails, Claude sees the error, adapts,
and continues with the next phase. No monolithic pipeline that crashes
on step 3 and loses steps 1-2.

Phase tools:
  analyze_scan      — discover files, return paths + language stats
  analyze_parse     — parse a chunk of files, return extracted nodes
  analyze_resolve   — resolve imports/heritage for parsed nodes
  analyze_community — run Leiden community detection
  analyze_process   — detect execution flows via BFS
  analyze_store     — persist graph to SQLite + build FTS index

Full pipeline tool:
  analyze           — runs all phases (convenience for simple cases)
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from .._app import mcp

logger = logging.getLogger(__name__)

# Shared in-memory state for a pipeline session.
# Tools operate on this graph — each phase adds to it.
_session: dict[str, Any] = {}


def _get_session(repo_path: str) -> dict[str, Any]:
    """Get or create a pipeline session for a repo."""
    if _session.get("repo_path") != repo_path:
        from ..core.graph.graph import create_knowledge_graph
        from ..core.ingestion.symbol_table import create_symbol_table
        _session.clear()
        _session["repo_path"] = repo_path
        _session["graph"] = create_knowledge_graph()
        _session["symbol_table"] = create_symbol_table()
        _session["import_map"] = {}
        _session["files"] = []
        _session["all_paths"] = []
        _session["community_result"] = None
        _session["process_result"] = None
    return _session


@mcp.tool(
    name="ai_architect_codebase_scan",
    description=(
        "Phase 1: Scan a repository to discover source files. "
        "Returns file count, language breakdown, and total bytes. "
        "This is the first step of indexing — call before parse."
    ),
)
async def tool_scan(repo_path: str) -> str:
    """Discover source files in a repository.

    Args:
        repo_path: Absolute path to the repository.
    """
    from ..core.ingestion.filesystem_walker import walk_repository_paths
    from ..core.ingestion.utils import get_language_from_filename
    from ..core.tree_sitter.parser_loader import is_language_available

    session = _get_session(repo_path)

    scanned = walk_repository_paths(repo_path)
    session["files"] = scanned
    session["all_paths"] = [f["path"] for f in scanned]

    # Language breakdown
    by_lang: dict[str, int] = {}
    parseable = 0
    for f in scanned:
        lang = get_language_from_filename(f["path"])
        if lang:
            by_lang[lang] = by_lang.get(lang, 0) + 1
            if is_language_available(lang):
                parseable += 1

    total_bytes = sum(f.get("size", 0) for f in scanned)

    return json.dumps({
        "status": "scanned",
        "total_files": len(scanned),
        "parseable_files": parseable,
        "total_bytes": total_bytes,
        "languages": by_lang,
    }, indent=2)


@mcp.tool(
    name="ai_architect_codebase_parse",
    description=(
        "Phase 2: Parse source files and extract symbols (functions, classes, "
        "methods, structs, etc.) + call relationships + import edges. "
        "Call after scan. Processes files in chunks to bound memory."
    ),
)
async def tool_parse(repo_path: str) -> str:
    """Parse all source files and extract symbols.

    Args:
        repo_path: Absolute path to the repository.
    """
    session = _get_session(repo_path)
    if not session["files"]:
        return json.dumps({"error": "No files scanned. Call scan first."})

    from ..core.ingestion.pipeline import run_pipeline_from_repo

    t0 = time.monotonic()
    result = run_pipeline_from_repo(repo_path)
    duration = time.monotonic() - t0

    session["graph"] = result["graph"]
    session["community_result"] = result["communityResult"]
    session["process_result"] = result["processResult"]

    graph = result["graph"]
    return json.dumps({
        "status": "parsed",
        "nodes": graph.node_count,
        "relationships": graph.relationship_count,
        "communities": result["communityResult"]["stats"]["totalCommunities"],
        "processes": result["processResult"]["stats"]["totalProcesses"],
        "duration_seconds": round(duration, 1),
    }, indent=2)


@mcp.tool(
    name="ai_architect_codebase_store",
    description=(
        "Phase 3: Persist the knowledge graph to SQLite and build FTS index. "
        "Call after parse. Makes the graph queryable by search/context/impact tools."
    ),
)
async def tool_store(repo_path: str) -> str:
    """Store graph to SQLite + build FTS5 search index.

    Args:
        repo_path: Absolute path to the repository.
    """
    session = _get_session(repo_path)
    graph = session.get("graph")
    if not graph or graph.node_count == 0:
        return json.dumps({"error": "No graph data. Call parse first."})

    from ..core.storage.repo_store import store_and_index
    from ..storage.repo_manager import get_storage_paths, register_repo
    from ..storage.git import get_current_commit

    paths = get_storage_paths(repo_path)
    commit = get_current_commit(repo_path)
    db_path = os.path.join(paths["storagePath"], "index.db")
    os.makedirs(paths["storagePath"], exist_ok=True)
    repo_name = os.path.basename(repo_path).lower()

    t0 = time.monotonic()
    db_stats = store_and_index(repo_name, db_path, graph)
    duration = time.monotonic() - t0

    community_result = session.get("community_result", {})
    process_result = session.get("process_result", {})

    stats = {
        "files": len(session.get("all_paths", [])),
        "nodes": db_stats["nodes"],
        "edges": db_stats["relationships"],
        "communities": (community_result.get("stats") or {}).get("totalCommunities", 0),
        "processes": (process_result.get("stats") or {}).get("totalProcesses", 0),
    }
    register_repo(repo_path, {
        "indexedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lastCommit": commit, "stats": stats,
    })

    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    return json.dumps({
        "status": "stored",
        "db_path": db_path,
        "db_size_mb": round(db_size / 1024 / 1024, 1),
        "store_duration_seconds": round(duration, 1),
        **stats,
    }, indent=2)


@mcp.tool(
    name="ai_architect_codebase_analyze",
    description=(
        "Full pipeline: scan + parse + store in one call. "
        "Convenience wrapper — for fine-grained control, use scan → parse → store individually."
    ),
)
async def tool_analyze(repo_path: str, force: bool = False) -> str:
    """Run the complete indexing pipeline.

    Args:
        repo_path: Absolute path to the repository.
        force: Force re-index even if up to date.
    """
    from ..storage.repo_manager import get_storage_paths, load_meta
    from ..storage.git import get_current_commit

    # Up-to-date check
    if not force:
        paths = get_storage_paths(repo_path)
        meta = load_meta(paths["storagePath"])
        commit = get_current_commit(repo_path)
        if meta and meta.get("lastCommit") == commit:
            return json.dumps({"status": "up_to_date", "repo_path": repo_path})

    t0 = time.monotonic()

    # Phase 1: Scan
    scan_result = json.loads(await tool_scan(repo_path))
    if scan_result.get("error"):
        return json.dumps(scan_result)

    # Phase 2: Parse (includes community + process detection)
    parse_result = json.loads(await tool_parse(repo_path))
    if parse_result.get("error"):
        return json.dumps(parse_result)

    # Phase 3: Store
    store_result = json.loads(await tool_store(repo_path))
    if store_result.get("error"):
        return json.dumps(store_result)

    duration = time.monotonic() - t0
    store_result["total_duration_seconds"] = round(duration, 1)
    store_result["status"] = "indexed"
    store_result["repo_path"] = repo_path

    return json.dumps(store_result, indent=2)
