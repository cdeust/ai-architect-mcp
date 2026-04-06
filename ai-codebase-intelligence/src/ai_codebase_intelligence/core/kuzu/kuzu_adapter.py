"""KuzuDB adapter.

Single CodeRelation table. CSV bulk loading. FTS extension management.
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from .schema import SCHEMA_QUERIES, REL_TABLE_NAME, NODE_TABLES, FTS_INDEX_SCHEMAS
from .csv_generator import stream_all_csvs_to_disk
from ..graph.graph import KnowledgeGraph

logger = logging.getLogger(__name__)

BACKTICK_TABLES: frozenset[str] = frozenset({
    "Struct", "Enum", "Macro", "Typedef", "Union", "Namespace", "Trait", "Impl",
    "TypeAlias", "Const", "Static", "Property", "Record", "Delegate", "Annotation",
    "Constructor", "Template", "Module",
})


def _esc_table(table: str) -> str:
    return f"`{table}`" if table in BACKTICK_TABLES else table


class KuzuAdapter:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: Any = None
        self._conn: Any = None
        self._fts_loaded = False

    async def initialize(self) -> None:
        import kuzu
        db_p = Path(self._db_path)
        if db_p.is_dir():
            shutil.rmtree(db_p, ignore_errors=True)
        db_p.parent.mkdir(parents=True, exist_ok=True)
        self._db = kuzu.Database(self._db_path)
        self._conn = kuzu.Connection(self._db)
        for sq in SCHEMA_QUERIES:
            try:
                self._conn.execute(sq)
            except Exception as exc:
                msg = str(exc)
                if "already exists" not in msg:
                    logger.debug("Schema: %s", msg[:120])
        try:
            self._conn.execute("INSTALL fts")
            self._conn.execute("LOAD EXTENSION fts")
            self._fts_loaded = True
        except Exception:
            pass

    async def store_graph(self, graph: KnowledgeGraph) -> dict[str, Any]:
        """Bulk load a KnowledgeGraph via CSV COPY."""
        if not self._conn:
            raise RuntimeError("KuzuDB not initialized")

        csv_dir = os.path.join(os.path.dirname(self._db_path), "csv")
        repo_path = ""  # CSV generator reads from graph, not disk
        csv_result = stream_all_csvs_to_disk(graph, repo_path, csv_dir)

        # Bulk COPY node CSVs
        for table_name, info in csv_result["nodeFiles"].items():
            csv_path = info["csvPath"].replace("\\", "/")
            t = _esc_table(table_name)
            copy_q = self._get_copy_query(table_name, csv_path)
            try:
                self._conn.execute(copy_q)
            except Exception:
                try:
                    retry_q = copy_q.replace("auto_detect=false)", "auto_detect=false, IGNORE_ERRORS=true)")
                    self._conn.execute(retry_q)
                except Exception as exc:
                    logger.warning("COPY failed for %s: %s", table_name, str(exc)[:200])

        # Bulk COPY relationships by FROM→TO pair
        rel_csv = csv_result["relCsvPath"]
        if csv_result["relRows"] > 0:
            self._copy_relationships(csv_dir, rel_csv)

        # Cleanup CSVs
        shutil.rmtree(csv_dir, ignore_errors=True)

        return {"success": True, "insertedRels": csv_result["relRows"]}

    def _get_copy_query(self, table: str, file_path: str) -> str:
        opts = '(HEADER=true, ESCAPE=\'"\', DELIM=\',\', QUOTE=\'"\', PARALLEL=false, auto_detect=false)'
        t = _esc_table(table)
        if table == "File":
            return f'COPY {t}(id, name, filePath, content) FROM "{file_path}" {opts}'
        if table == "Folder":
            return f'COPY {t}(id, name, filePath) FROM "{file_path}" {opts}'
        if table == "Community":
            return f'COPY {t}(id, label, heuristicLabel, keywords, description, enrichedBy, cohesion, symbolCount) FROM "{file_path}" {opts}'
        if table == "Process":
            return f'COPY {t}(id, label, heuristicLabel, processType, stepCount, communities, entryPointId, terminalId) FROM "{file_path}" {opts}'
        if table in ("Function", "Class", "Interface", "Method", "CodeElement"):
            return f'COPY {t}(id, name, filePath, startLine, endLine, isExported, content, description) FROM "{file_path}" {opts}'
        return f'COPY {t}(id, name, filePath, startLine, endLine, content, description) FROM "{file_path}" {opts}'

    def _copy_relationships(self, csv_dir: str, rel_csv: str) -> None:
        """Split relationships by FROM→TO label pair and COPY each."""
        import csv as csv_mod
        header = ""
        rels_by_pair: dict[str, list[str]] = {}

        with open(rel_csv, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == 0:
                    header = line.strip()
                    continue
                line = line.strip()
                if not line:
                    continue
                # Extract from/to IDs to determine labels
                parts = line.split(",", 2)
                if len(parts) < 2:
                    continue
                from_id = parts[0].strip('"')
                to_id = parts[1].strip('"')
                from_label = self._get_node_label(from_id)
                to_label = self._get_node_label(to_id)
                if from_label and to_label:
                    key = f"{from_label}|{to_label}"
                    rels_by_pair.setdefault(key, []).append(line)

        for pair_key, lines in rels_by_pair.items():
            from_label, to_label = pair_key.split("|")
            pair_csv = os.path.join(csv_dir, f"rel_{from_label}_{to_label}.csv")
            with open(pair_csv, "w", encoding="utf-8") as f:
                f.write(header + "\n" + "\n".join(lines) + "\n")
            norm_path = pair_csv.replace("\\", "/")
            fl = _esc_table(from_label)
            tl = _esc_table(to_label)
            copy_q = (
                f'COPY {REL_TABLE_NAME} FROM "{norm_path}" '
                f'(from="{from_label}", to="{to_label}", HEADER=true, '
                f'ESCAPE=\'"\', DELIM=\',\', QUOTE=\'"\', PARALLEL=false, auto_detect=false)'
            )
            try:
                self._conn.execute(copy_q)
            except Exception as exc:
                logger.debug("Rel COPY %s: %s", pair_key, str(exc)[:100])
            try:
                os.unlink(pair_csv)
            except OSError:
                pass

    def _get_node_label(self, node_id: str) -> str | None:
        if node_id.startswith("comm_"):
            return "Community"
        if node_id.startswith("proc_"):
            return "Process"
        colon = node_id.find(":")
        if colon > 0:
            label = node_id[:colon]
            if label in NODE_TABLES:
                return label
        return None

    async def create_fts_indexes(self) -> None:
        if not self._conn:
            return
        if not self._fts_loaded:
            try:
                self._conn.execute("LOAD EXTENSION fts")
                self._fts_loaded = True
            except Exception:
                pass
        for stmt in FTS_INDEX_SCHEMAS:
            try:
                self._conn.execute(stmt)
            except Exception as exc:
                if "already exists" not in str(exc):
                    logger.debug("FTS: %s", exc)

    def execute_query(self, cypher: str) -> list[dict[str, Any]]:
        if not self._conn:
            return []
        result = self._conn.execute(cypher)
        rows: list[dict[str, Any]] = []
        cols = result.get_column_names()
        while result.has_next():
            vals = result.get_next()
            rows.append(dict(zip(cols, vals)))
        return rows
