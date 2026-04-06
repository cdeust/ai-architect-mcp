from __future__ import annotations

import csv
import os
import shutil
from pathlib import Path
from typing import Any

from ..graph.graph import KnowledgeGraph

FLUSH_EVERY: int = 500
MAX_FILE_CONTENT: int = 10000
MAX_SNIPPET: int = 5000


def sanitize_utf8(s: str) -> str:
    return (
        s.replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def escape_csv_field(value: Any) -> str:
    if value is None:
        return '""'
    s = sanitize_utf8(str(value))
    return '"' + s.replace('"', '""') + '"'


def escape_csv_number(value: Any, default: int | float = -1) -> str:
    if value is None:
        return str(default)
    return str(value)


def is_binary_content(content: str) -> bool:
    if not content:
        return False
    sample = content[:1000]
    non_printable = sum(
        1 for c in sample
        if (ord(c) < 9) or (13 < ord(c) < 32) or ord(c) == 127
    )
    return (non_printable / len(sample)) > 0.1 if sample else False


class FileContentCache:
    def __init__(self, repo_path: str, max_size: int = 3000) -> None:
        self._cache: dict[str, str] = {}
        self._access_order: list[str] = []
        self._max_size = max_size
        self._repo_path = repo_path

    def get(self, relative_path: str) -> str:
        if not relative_path:
            return ""
        if relative_path in self._cache:
            self._access_order.remove(relative_path)
            self._access_order.append(relative_path)
            return self._cache[relative_path]
        try:
            full_path = os.path.join(self._repo_path, relative_path)
            with open(full_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
            self._set(relative_path, content)
            return content
        except OSError:
            self._set(relative_path, "")
            return ""

    def _set(self, key: str, value: str) -> None:
        if len(self._cache) >= self._max_size:
            oldest = self._access_order.pop(0)
            self._cache.pop(oldest, None)
        self._cache[key] = value
        self._access_order.append(key)


def extract_content(node: Any, content_cache: FileContentCache) -> str:
    """Extract source content for a graph node."""
    content = content_cache.get(node.file_path)
    if not content:
        return ""
    if node.label.value == "Folder":
        return ""
    if is_binary_content(content):
        return "[Binary file - content not stored]"
    if node.label.value == "File":
        if len(content) > MAX_FILE_CONTENT:
            return content[:MAX_FILE_CONTENT] + "\n... [truncated]"
        return content
    if not node.start_line or not node.end_line:
        return ""
    lines = content.split("\n")
    start = max(0, node.start_line - 2)
    end = min(len(lines) - 1, node.end_line + 2)
    snippet = "\n".join(lines[start : end + 1])
    if len(snippet) > MAX_SNIPPET:
        return snippet[:MAX_SNIPPET] + "\n... [truncated]"
    return snippet


class BufferedCSVWriter:
    def __init__(self, file_path: str, header: str) -> None:
        self._file_path = file_path
        self._fh = open(file_path, "w", encoding="utf-8", newline="")
        self._buffer: list[str] = [header]
        self.rows: int = 0

    def add_row(self, row: str) -> None:
        self._buffer.append(row)
        self.rows += 1
        if len(self._buffer) >= FLUSH_EVERY:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        self._fh.write("\n".join(self._buffer) + "\n")
        self._buffer.clear()

    def finish(self) -> None:
        self.flush()
        self._fh.close()


TABLES_WITH_EXPORTED: frozenset[str] = frozenset({
    "Function", "Class", "Interface", "Method", "CodeElement",
})

MULTI_LANG_TYPES: list[str] = [
    "Struct", "Enum", "Macro", "Typedef", "Union", "Namespace",
    "Trait", "Impl", "TypeAlias", "Const", "Static", "Property",
    "Record", "Delegate", "Annotation", "Constructor", "Template",
    "Module",
]


def stream_all_csvs_to_disk(
    graph: KnowledgeGraph,
    repo_path: str,
    csv_dir: str,
) -> dict[str, Any]:
    shutil.rmtree(csv_dir, ignore_errors=True)
    os.makedirs(csv_dir, exist_ok=True)

    content_cache = FileContentCache(repo_path)

    file_writer = BufferedCSVWriter(os.path.join(csv_dir, "file.csv"), "id,name,filePath,content")
    folder_writer = BufferedCSVWriter(os.path.join(csv_dir, "folder.csv"), "id,name,filePath")

    code_element_header = "id,name,filePath,startLine,endLine,isExported,content,description"
    function_writer = BufferedCSVWriter(os.path.join(csv_dir, "function.csv"), code_element_header)
    class_writer = BufferedCSVWriter(os.path.join(csv_dir, "class.csv"), code_element_header)
    interface_writer = BufferedCSVWriter(os.path.join(csv_dir, "interface.csv"), code_element_header)
    method_writer = BufferedCSVWriter(os.path.join(csv_dir, "method.csv"), code_element_header)
    code_elem_writer = BufferedCSVWriter(os.path.join(csv_dir, "codeelement.csv"), code_element_header)

    community_writer = BufferedCSVWriter(
        os.path.join(csv_dir, "community.csv"),
        "id,label,heuristicLabel,keywords,description,enrichedBy,cohesion,symbolCount",
    )
    process_writer = BufferedCSVWriter(
        os.path.join(csv_dir, "process.csv"),
        "id,label,heuristicLabel,processType,stepCount,communities,entryPointId,terminalId",
    )

    multi_lang_header = "id,name,filePath,startLine,endLine,content,description"
    multi_lang_writers: dict[str, BufferedCSVWriter] = {}
    for t in MULTI_LANG_TYPES:
        multi_lang_writers[t] = BufferedCSVWriter(
            os.path.join(csv_dir, f"{t.lower()}.csv"), multi_lang_header
        )

    code_writer_map: dict[str, BufferedCSVWriter] = {
        "Function": function_writer,
        "Class": class_writer,
        "Interface": interface_writer,
        "Method": method_writer,
        "CodeElement": code_elem_writer,
    }

    seen_file_ids: set[str] = set()

    for node in graph.iter_nodes():
        label = node.label.value
        props = node.properties

        if label == "File":
            if node.id in seen_file_ids:
                continue
            seen_file_ids.add(node.id)
            content = extract_content(node, content_cache)
            file_writer.add_row(",".join([
                escape_csv_field(node.id),
                escape_csv_field(node.name),
                escape_csv_field(node.file_path),
                escape_csv_field(content),
            ]))

        elif label == "Folder":
            folder_writer.add_row(",".join([
                escape_csv_field(node.id),
                escape_csv_field(node.name),
                escape_csv_field(node.file_path),
            ]))

        elif label == "Community":
            keywords = props.get("keywords", [])
            keywords_str = "[" + ",".join(
                "'" + k.replace("\\", "\\\\").replace("'", "''").replace(",", "\\,") + "'"
                for k in keywords
            ) + "]"
            community_writer.add_row(",".join([
                escape_csv_field(node.id),
                escape_csv_field(node.name),
                escape_csv_field(props.get("heuristicLabel", "")),
                keywords_str,
                escape_csv_field(node.docstring),
                escape_csv_field(props.get("enrichedBy", "heuristic")),
                escape_csv_number(props.get("cohesion"), 0),
                escape_csv_number(props.get("symbolCount"), 0),
            ]))

        elif label == "Process":
            communities = props.get("communities", [])
            communities_str = "[" + ",".join(
                "'" + c.replace("'", "''") + "'" for c in communities
            ) + "]"
            process_writer.add_row(",".join([
                escape_csv_field(node.id),
                escape_csv_field(node.name),
                escape_csv_field(props.get("heuristicLabel", "")),
                escape_csv_field(props.get("processType", "")),
                escape_csv_number(props.get("stepCount"), 0),
                escape_csv_field(communities_str),
                escape_csv_field(props.get("entryPointId", "")),
                escape_csv_field(props.get("terminalId", "")),
            ]))

        else:
            writer = code_writer_map.get(label)
            if writer:
                content = extract_content(node, content_cache)
                writer.add_row(",".join([
                    escape_csv_field(node.id),
                    escape_csv_field(node.name),
                    escape_csv_field(node.file_path),
                    escape_csv_number(node.start_line, -1),
                    escape_csv_number(node.end_line, -1),
                    "true" if node.is_exported else "false",
                    escape_csv_field(content),
                    escape_csv_field(node.docstring),
                ]))
            else:
                ml_writer = multi_lang_writers.get(label)
                if ml_writer:
                    content = extract_content(node, content_cache)
                    ml_writer.add_row(",".join([
                        escape_csv_field(node.id),
                        escape_csv_field(node.name),
                        escape_csv_field(node.file_path),
                        escape_csv_number(node.start_line, -1),
                        escape_csv_number(node.end_line, -1),
                        escape_csv_field(content),
                        escape_csv_field(node.docstring),
                    ]))

    all_writers = [
        file_writer, folder_writer, function_writer, class_writer,
        interface_writer, method_writer, code_elem_writer,
        community_writer, process_writer,
        *multi_lang_writers.values(),
    ]
    for w in all_writers:
        w.finish()

    rel_csv_path = os.path.join(csv_dir, "relations.csv")
    rel_writer = BufferedCSVWriter(rel_csv_path, "from,to,type,confidence,reason,step")
    for rel in graph.iter_relationships():
        rel_writer.add_row(",".join([
            escape_csv_field(rel.source_id),
            escape_csv_field(rel.target_id),
            escape_csv_field(rel.relationship_type.value),
            escape_csv_number(rel.confidence, 1.0),
            escape_csv_field(rel.properties.get("reason", "")),
            escape_csv_number(rel.properties.get("step"), 0),
        ]))
    rel_writer.finish()

    node_files: dict[str, dict[str, Any]] = {}
    table_map: list[tuple[str, BufferedCSVWriter]] = [
        ("File", file_writer), ("Folder", folder_writer),
        ("Function", function_writer), ("Class", class_writer),
        ("Interface", interface_writer), ("Method", method_writer),
        ("CodeElement", code_elem_writer),
        ("Community", community_writer), ("Process", process_writer),
        *[(name, w) for name, w in multi_lang_writers.items()],
    ]
    for name, writer in table_map:
        if writer.rows > 0:
            node_files[name] = {
                "csvPath": os.path.join(csv_dir, f"{name.lower()}.csv"),
                "rows": writer.rows,
            }

    return {
        "nodeFiles": node_files,
        "relCsvPath": rel_csv_path,
        "relRows": rel_writer.rows,
    }
