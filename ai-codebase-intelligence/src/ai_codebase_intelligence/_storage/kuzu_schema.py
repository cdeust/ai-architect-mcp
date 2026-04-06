"""Kuzu graph database schema definitions.

Defines CREATE TABLE statements for all node types, the unified
CodeRelation relationship table, FTS indexes, vector indexes,
and the embedding storage table.
"""

from __future__ import annotations

_BASE_NODE_PROPS = (
    "id STRING, name STRING, file_path STRING, "
    "start_line INT64, end_line INT64, language STRING, "
    "signature STRING, docstring STRING, is_exported BOOLEAN, "
    "qualified_name STRING, content STRING, "
    "PRIMARY KEY (id)"
)

_CORE_TABLES = [
    "File", "Folder", "Class", "Function", "Method",
    "Interface", "Enum", "Variable", "TypeAlias",
    "Namespace", "Module", "Community", "Process",
]

_MULTI_LANG_TABLES = [
    "Struct", "Macro", "Typedef", "Union", "Trait", "Impl",
    "Const", "Static", "Property", "Record", "Delegate",
    "Annotation", "Constructor", "Template",
]

NODE_TABLE_SCHEMAS: list[str] = [
    f"CREATE NODE TABLE IF NOT EXISTS {t}({_BASE_NODE_PROPS})"
    for t in _CORE_TABLES
] + [
    f"CREATE NODE TABLE IF NOT EXISTS {t}({_BASE_NODE_PROPS})"
    for t in _MULTI_LANG_TABLES
]

_CODE_REL_PROPS = (
    "type STRING, confidence DOUBLE, reason STRING, step INT64"
)

_ALL_NODE_NAMES = _CORE_TABLES + _MULTI_LANG_TABLES

REL_TABLE_SCHEMAS: list[str] = [
    "CREATE REL TABLE IF NOT EXISTS CodeRelation("
    f"FROM {src} TO {dst}, {_CODE_REL_PROPS})"
    for src in _ALL_NODE_NAMES
    for dst in _ALL_NODE_NAMES
]

_EMBEDDING_TABLE = (
    "CREATE NODE TABLE IF NOT EXISTS Embedding("
    "id STRING, node_id STRING, model STRING, "
    "vector DOUBLE[], PRIMARY KEY (id))"
)

FTS_INDEX_SCHEMAS: list[str] = [
    f"CALL CREATE_FTS_INDEX('{t}', 'name', 'content', 'docstring')"
    for t in _CORE_TABLES[:5]
]

VECTOR_INDEX_SCHEMAS: list[str] = [
    "CALL CREATE_VECTOR_INDEX('Embedding', 'vector', 384)",
]

ALL_SCHEMAS: list[str] = (
    NODE_TABLE_SCHEMAS + REL_TABLE_SCHEMAS + [_EMBEDDING_TABLE]
)

SCHEMA_QUERIES: list[str] = ALL_SCHEMAS + FTS_INDEX_SCHEMAS + VECTOR_INDEX_SCHEMAS
