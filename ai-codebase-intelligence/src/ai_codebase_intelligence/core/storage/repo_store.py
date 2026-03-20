"""Per-repo store manager — lazy-loaded SQLite + GraphIndex.

SQLite store is opened immediately (cheap — just a file handle).
GraphIndex is built lazily on first traversal request (expensive —
loads all nodes/edges into memory). FTS search goes directly to
SQLite without loading the graph.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .sqlite_store import SQLiteStore
from .graph_index import GraphIndex
from ..graph.graph import KnowledgeGraph

logger = logging.getLogger(__name__)

_stores: dict[str, dict[str, Any]] = {}


def init_repo(repo_id: str, db_path: str) -> None:
    """Open a repo's SQLite store. Does NOT load graph into memory."""
    if repo_id in _stores:
        return

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    store = SQLiteStore(db_path)
    store.initialize()

    _stores[repo_id] = {
        "store": store,
        "graph": None,  # lazy
        "index": None,  # lazy
        "db_path": db_path,
    }

    stats = store.get_stats()
    logger.info("Opened repo %s: %d nodes, %d edges (graph not loaded yet)",
                repo_id, stats["nodes"], stats["edges"])


def get_store(repo_id: str) -> SQLiteStore:
    """Get the SQLite store for a repo."""
    entry = _stores.get(repo_id)
    if not entry:
        raise RuntimeError(f"Repo {repo_id} not initialized")
    return entry["store"]


def get_index(repo_id: str) -> GraphIndex:
    """Get the in-memory graph index — built lazily on first call.

    This loads ALL nodes and relationships into memory. Only call
    for tools that need traversal (context, impact). FTS search
    should use search_fts() instead.
    """
    entry = _stores.get(repo_id)
    if not entry:
        raise RuntimeError(f"Repo {repo_id} not initialized")

    if entry["index"] is None:
        logger.info("Loading graph into memory for %s...", repo_id)
        store = entry["store"]
        graph = store.load_graph()
        entry["graph"] = graph
        entry["index"] = GraphIndex(graph)
        logger.info("Graph loaded: %d nodes, %d edges",
                    entry["index"].node_count, entry["index"].relationship_count)

    return entry["index"]


def get_graph(repo_id: str) -> KnowledgeGraph:
    """Get the KnowledgeGraph — loads lazily via get_index."""
    entry = _stores.get(repo_id)
    if not entry:
        raise RuntimeError(f"Repo {repo_id} not initialized")
    if entry["graph"] is None:
        get_index(repo_id)  # triggers lazy load
    return entry["graph"]


def search_fts(repo_id: str, query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Full-text search — goes directly to SQLite, no graph load needed."""
    return get_store(repo_id).search_fts(query, limit)


def query_sql(repo_id: str, sql: str) -> list[dict[str, Any]]:
    """Execute a read-only SQL query against SQLite."""
    return get_store(repo_id).query_sql(sql)


def is_ready(repo_id: str) -> bool:
    """Check if a repo is opened."""
    return repo_id in _stores


def close_repo(repo_id: str) -> None:
    """Close a repo's store and free memory."""
    entry = _stores.pop(repo_id, None)
    if entry:
        entry["store"].close()


def close_all() -> None:
    """Close all repo stores."""
    for repo_id in list(_stores.keys()):
        close_repo(repo_id)


def store_and_index(
    repo_id: str, db_path: str, graph: KnowledgeGraph
) -> dict[str, int]:
    """Store a graph to SQLite and make it available for queries.

    Does NOT build GraphIndex — that's lazy-loaded on first traversal.
    """
    store = SQLiteStore(db_path)
    store.initialize()
    stats = store.store_graph(graph)

    _stores[repo_id] = {
        "store": store,
        "graph": graph,
        "index": None,  # lazy — only built when traversal needed
        "db_path": db_path,
    }

    return stats
