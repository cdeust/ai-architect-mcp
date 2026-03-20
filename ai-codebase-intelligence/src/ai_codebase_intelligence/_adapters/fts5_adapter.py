"""FTS5 concrete adapter implementing SearchPort.

Uses SQLite FTS5 — built into Python stdlib. Zero dependencies.
Indexes node names, content, and file paths for keyword search.
"""

from __future__ import annotations

import logging
import sqlite3

from .ports import SearchPort
from .._models.graph_models import NodeModel, SearchResult

logger = logging.getLogger(__name__)

_CREATE_FTS = """CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts
    USING fts5(name, content, file_path, content=nodes, content_rowid=rowid)"""


class FTS5Search(SearchPort):
    """FTS5-backed full-text search.

    Args:
        db_path: Path to the SQLite database (same as GraphStorage).
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _ensure_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
        return self._conn

    def index_nodes(self, nodes: list[NodeModel]) -> int:
        """Rebuild FTS index from nodes.

        Drops and recreates the FTS table, then populates from
        the nodes table. Must be called after store_nodes().

        Args:
            nodes: Not used directly — reads from the nodes table.

        Returns:
            Number of nodes indexed.
        """
        conn = self._ensure_conn()
        try:
            conn.execute("DROP TABLE IF EXISTS nodes_fts")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(_CREATE_FTS)
            conn.execute(
                "INSERT INTO nodes_fts(rowid, name, content, file_path) "
                "SELECT rowid, name, content, file_path FROM nodes"
            )
            conn.commit()
            count = conn.execute("SELECT COUNT(*) FROM nodes_fts").fetchone()[0]
            return count
        except sqlite3.OperationalError as e:
            logger.warning("FTS5 index build failed: %s", e)
            return 0

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Full-text search via FTS5.

        Falls back to LIKE search if FTS5 query fails (e.g., syntax error).

        Args:
            query: Search query string.
            limit: Maximum results.

        Returns:
            Ranked search results.
        """
        conn = self._ensure_conn()
        safe = query.replace('"', '""')

        try:
            rows = conn.execute(
                "SELECT n.id, n.label, n.name, n.file_path, "
                "n.start_line, n.end_line, rank "
                "FROM nodes_fts f "
                "JOIN nodes n ON n.rowid = f.rowid "
                f'WHERE nodes_fts MATCH \'"{safe}"\' '
                f"ORDER BY rank LIMIT ?",
                (limit,),
            ).fetchall()
        except sqlite3.OperationalError:
            # Fallback: LIKE search
            like = f"%{query}%"
            rows = conn.execute(
                "SELECT id, label, name, file_path, start_line, end_line, 0 "
                "FROM nodes WHERE name LIKE ? OR content LIKE ? "
                "ORDER BY CASE WHEN name LIKE ? THEN 0 ELSE 1 END "
                "LIMIT ?",
                (like, like, like, limit),
            ).fetchall()

        return [
            SearchResult(
                node_id=r[0], label=r[1], name=r[2],
                file_path=r[3], start_line=r[4], end_line=r[5],
                score=-r[6] if r[6] else 0.0,
            )
            for r in rows
        ]
