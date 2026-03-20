"""SQLite + FTS5 storage for the knowledge graph.

Zero external dependencies. Persists the in-memory KnowledgeGraph
to a single .db file. FTS5 provides full-text search.

Schema:
  nodes(id TEXT PK, label TEXT, name TEXT, filePath TEXT, startLine INT,
        endLine INT, isExported INT, content TEXT, description TEXT)
  relationships(id TEXT PK, sourceId TEXT, targetId TEXT, type TEXT,
                confidence REAL, reason TEXT, step INT)
  nodes_fts(name, content) USING fts5
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from typing import Any

from ..graph.graph import KnowledgeGraph

logger = logging.getLogger(__name__)

_CREATE_NODES = """CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    filePath TEXT NOT NULL DEFAULT '',
    startLine INTEGER DEFAULT 0,
    endLine INTEGER DEFAULT 0,
    isExported INTEGER DEFAULT 0,
    content TEXT DEFAULT '',
    description TEXT DEFAULT '',
    properties TEXT DEFAULT '{}'
)"""

_CREATE_RELS = """CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    sourceId TEXT NOT NULL,
    targetId TEXT NOT NULL,
    type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    reason TEXT DEFAULT '',
    step INTEGER DEFAULT 0
)"""

_CREATE_FTS = """CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts
    USING fts5(name, content, filePath, content=nodes, content_rowid=rowid)"""

_CREATE_IDX_SRC = "CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(sourceId)"
_CREATE_IDX_TGT = "CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(targetId)"
_CREATE_IDX_TYPE = "CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(type)"
_CREATE_IDX_LABEL = "CREATE INDEX IF NOT EXISTS idx_node_label ON nodes(label)"
_CREATE_IDX_FILE = "CREATE INDEX IF NOT EXISTS idx_node_file ON nodes(filePath)"


class SQLiteStore:
    """SQLite-backed persistence for KnowledgeGraph."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Create database and tables."""
        os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(_CREATE_NODES)
        self._conn.execute(_CREATE_RELS)
        self._conn.execute(_CREATE_IDX_SRC)
        self._conn.execute(_CREATE_IDX_TGT)
        self._conn.execute(_CREATE_IDX_TYPE)
        self._conn.execute(_CREATE_IDX_LABEL)
        self._conn.execute(_CREATE_IDX_FILE)
        try:
            self._conn.execute(_CREATE_FTS)
        except sqlite3.OperationalError:
            logger.debug("FTS5 table may already exist")
        self._conn.commit()

    def store_graph(self, graph: KnowledgeGraph) -> dict[str, int]:
        """Bulk insert a KnowledgeGraph into SQLite."""
        if not self._conn:
            raise RuntimeError("Store not initialized")

        c = self._conn
        c.execute("DELETE FROM nodes")
        c.execute("DELETE FROM relationships")

        node_rows = []
        for node in graph.iter_nodes():
            props = node.get("properties", {})
            node_rows.append((
                node["id"],
                node.get("label", ""),
                props.get("name", ""),
                props.get("filePath", ""),
                props.get("startLine", 0),
                props.get("endLine", 0),
                1 if props.get("isExported") else 0,
                props.get("content", ""),
                props.get("description", ""),
                json.dumps(props),
            ))

        c.executemany(
            "INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?)",
            node_rows,
        )

        rel_rows = []
        for rel in graph.iter_relationships():
            rel_rows.append((
                rel.get("id", ""),
                rel.get("sourceId", ""),
                rel.get("targetId", ""),
                rel.get("type", ""),
                rel.get("confidence", 1.0),
                rel.get("reason", ""),
                rel.get("step", 0),
            ))

        c.executemany(
            "INSERT OR REPLACE INTO relationships VALUES (?,?,?,?,?,?,?)",
            rel_rows,
        )

        # Rebuild FTS index
        try:
            c.execute("DROP TABLE IF EXISTS nodes_fts")
            c.execute(_CREATE_FTS)
            c.execute(
                "INSERT INTO nodes_fts(rowid, name, content, filePath) "
                "SELECT rowid, name, content, filePath FROM nodes"
            )
        except sqlite3.OperationalError as e:
            logger.debug("FTS rebuild: %s", e)

        c.commit()
        return {"nodes": len(node_rows), "relationships": len(rel_rows)}

    def load_graph(self) -> KnowledgeGraph:
        """Load the full graph from SQLite into memory."""
        if not self._conn:
            raise RuntimeError("Store not initialized")

        graph = KnowledgeGraph()
        c = self._conn

        for row in c.execute("SELECT id, label, properties FROM nodes"):
            node_id, label, props_json = row
            props = json.loads(props_json) if props_json else {}
            graph.add_node({"id": node_id, "label": label, "properties": props})

        for row in c.execute(
            "SELECT id, sourceId, targetId, type, confidence, reason, step "
            "FROM relationships"
        ):
            graph.add_relationship({
                "id": row[0], "sourceId": row[1], "targetId": row[2],
                "type": row[3], "confidence": row[4],
                "reason": row[5], "step": row[6],
            })

        return graph

    def search_fts(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Full-text search via FTS5."""
        if not self._conn:
            return []

        # FTS5 query — escape special chars
        safe_query = query.replace('"', '""')
        try:
            rows = self._conn.execute(
                "SELECT n.id, n.label, n.name, n.filePath, "
                "n.startLine, n.endLine, rank "
                "FROM nodes_fts f "
                "JOIN nodes n ON n.rowid = f.rowid "
                f'WHERE nodes_fts MATCH \'"{safe_query}"\' '
                f"ORDER BY rank LIMIT {limit}"
            ).fetchall()
        except sqlite3.OperationalError:
            # Fallback: LIKE search if FTS fails
            like = f"%{query}%"
            rows = self._conn.execute(
                "SELECT id, label, name, filePath, startLine, endLine, 0 "
                "FROM nodes WHERE name LIKE ? OR content LIKE ? "
                f"LIMIT {limit}",
                (like, like),
            ).fetchall()

        return [
            {
                "id": r[0], "label": r[1], "name": r[2],
                "filePath": r[3], "startLine": r[4],
                "endLine": r[5], "score": -r[6] if r[6] else 0,
            }
            for r in rows
        ]

    def query_sql(self, sql: str) -> list[dict[str, Any]]:
        """Execute a read-only SQL query."""
        if not self._conn:
            return []

        upper = sql.strip().upper()
        if any(upper.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE")):
            raise ValueError("Write operations not allowed")

        cursor = self._conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

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
