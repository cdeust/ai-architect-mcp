"""SQLite concrete adapter implementing GraphStoragePort.

Zero external dependencies — uses Python stdlib sqlite3.
Single .db file. WAL mode for concurrent reads.

JUSTIFICATION: SQLite chosen over KuzuDB after 5 sessions of crashes
  caused by: stale directories, extension loading failures, schema
  version mismatches, and v0.11 API breaking changes. SQLite ships
  with Python, has zero native dependencies, and is tested at
  billions of deployments. Graph traversal runs in-memory via
  GraphIndex — SQLite is persistence + FTS only.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from typing import Any

from .ports import GraphStoragePort
from .._models.graph_models import NodeModel, RelationshipModel

logger = logging.getLogger(__name__)

_CREATE_NODES = """CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    file_path TEXT NOT NULL DEFAULT '',
    start_line INTEGER DEFAULT 0,
    end_line INTEGER DEFAULT 0,
    is_exported INTEGER DEFAULT 0,
    content TEXT DEFAULT '',
    description TEXT DEFAULT '',
    properties TEXT DEFAULT '{}'
)"""

_CREATE_RELS = """CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    reason TEXT DEFAULT '',
    step INTEGER DEFAULT 0
)"""

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id)",
    "CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id)",
    "CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(type)",
    "CREATE INDEX IF NOT EXISTS idx_node_label ON nodes(label)",
    "CREATE INDEX IF NOT EXISTS idx_node_file ON nodes(file_path)",
    "CREATE INDEX IF NOT EXISTS idx_node_name ON nodes(name)",
]


class SQLiteGraphStorage(GraphStoragePort):
    """SQLite-backed graph persistence.

    Args:
        db_path: Absolute path to the .db file.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Create database, tables, and indexes."""
        os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(_CREATE_NODES)
        self._conn.execute(_CREATE_RELS)
        for idx in _INDEXES:
            self._conn.execute(idx)
        self._conn.commit()

    def store_nodes(self, nodes: list[NodeModel]) -> int:
        """Bulk insert nodes via executemany."""
        if not self._conn or not nodes:
            return 0
        rows = [
            (n.id, n.label, n.name, n.file_path, n.start_line,
             n.end_line, 1 if n.is_exported else 0, n.content,
             n.description, json.dumps(n.properties))
            for n in nodes
        ]
        self._conn.executemany(
            "INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        self._conn.commit()
        return len(rows)

    def store_relationships(self, relationships: list[RelationshipModel]) -> int:
        """Bulk insert relationships via executemany."""
        if not self._conn or not relationships:
            return 0
        rows = [
            (r.id, r.source_id, r.target_id, r.type,
             r.confidence, r.reason, r.step)
            for r in relationships
        ]
        self._conn.executemany(
            "INSERT OR REPLACE INTO relationships VALUES (?,?,?,?,?,?,?)",
            rows,
        )
        self._conn.commit()
        return len(rows)

    def load_all_nodes(self) -> list[NodeModel]:
        """Load all nodes from the database."""
        if not self._conn:
            return []
        rows = self._conn.execute(
            "SELECT id, label, name, file_path, start_line, end_line, "
            "is_exported, content, description, properties FROM nodes"
        ).fetchall()
        return [
            NodeModel(
                id=r[0], label=r[1], name=r[2], file_path=r[3],
                start_line=r[4], end_line=r[5], is_exported=bool(r[6]),
                content=r[7], description=r[8],
                properties=json.loads(r[9]) if r[9] else {},
            )
            for r in rows
        ]

    def load_all_relationships(self) -> list[RelationshipModel]:
        """Load all relationships from the database."""
        if not self._conn:
            return []
        rows = self._conn.execute(
            "SELECT id, source_id, target_id, type, confidence, reason, step "
            "FROM relationships"
        ).fetchall()
        return [
            RelationshipModel(
                id=r[0], source_id=r[1], target_id=r[2], type=r[3],
                confidence=r[4], reason=r[5], step=r[6],
            )
            for r in rows
        ]

    def get_stats(self) -> dict[str, int]:
        """Get node and relationship counts."""
        if not self._conn:
            return {"nodes": 0, "edges": 0}
        nodes = self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edges = self._conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
        return {"nodes": nodes, "edges": edges}

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
