"""KuzuDB connection pool for the MCP server.

Python is single-threaded (GIL), so we use a simple single-connection
per repo approach instead of a multi-connection pool.
"""
from __future__ import annotations

import os
import time
from typing import Any

_pool: dict[str, dict[str, Any]] = {}
MAX_POOL_SIZE = 15
IDLE_TIMEOUT_S = 300  # 5 minutes


def init_kuzu(repo_id: str, db_path: str) -> None:
    if repo_id in _pool:
        _pool[repo_id]["lastUsed"] = time.time()
        return

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"KuzuDB not found at {db_path}. Run: analyze")

    import kuzu

    _evict_lru()

    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    # Load FTS extension
    try:
        conn.execute("INSTALL fts")
    except Exception:
        pass
    try:
        conn.execute("LOAD EXTENSION fts")
    except Exception:
        pass

    _pool[repo_id] = {
        "db": db,
        "conn": conn,
        "lastUsed": time.time(),
    }


def execute_query(repo_id: str, cypher: str) -> list[dict[str, Any]]:
    entry = _pool.get(repo_id)
    if entry is None:
        raise RuntimeError(f"Repo {repo_id} not initialized. Call init_kuzu first.")

    entry["lastUsed"] = time.time()
    conn = entry["conn"]

    result = conn.execute(cypher)
    rows: list[dict[str, Any]] = []
    columns = result.get_column_names()
    while result.has_next():
        values = result.get_next()
        rows.append(dict(zip(columns, values)))
    return rows


def close_repo(repo_id: str) -> None:
    entry = _pool.pop(repo_id, None)
    if entry is None:
        return
    try:
        entry["conn"].close()
    except Exception:
        pass
    try:
        entry["db"].close()
    except Exception:
        pass


def close_all() -> None:
    for repo_id in list(_pool.keys()):
        close_repo(repo_id)


def _evict_lru() -> None:
    if len(_pool) < MAX_POOL_SIZE:
        return
    oldest_id = None
    oldest_time = float("inf")
    for rid, entry in _pool.items():
        if entry["lastUsed"] < oldest_time:
            oldest_time = entry["lastUsed"]
            oldest_id = rid
    if oldest_id:
        close_repo(oldest_id)
