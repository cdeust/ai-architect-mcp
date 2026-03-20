"""Tests for schema completeness — all 27+ node labels and relationship types.

Validates that the schema covers all required node/relationship tables,
relationship types, and model definitions.
"""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._models.graph_types import (
    NodeLabel,
    RelationshipType,
)
from ai_codebase_intelligence._models.tool_types_ext import (
    RenameInput,
    RenameOutput,
)
from ai_codebase_intelligence._storage.kuzu_schema import (
    ALL_SCHEMAS,
    FTS_INDEX_SCHEMAS,
    NODE_TABLE_SCHEMAS,
    REL_TABLE_SCHEMAS,
    VECTOR_INDEX_SCHEMAS,
)


# --- NodeLabel completeness ---

EXPECTED_NODE_LABELS: set[str] = {
    "File", "Folder", "Class", "Function", "Method",
    "Interface", "Enum", "Variable", "TypeAlias",
    "Namespace", "Module",
    "Struct", "Macro", "Typedef", "Union", "Trait", "Impl",
    "Const", "Static", "Property", "Record", "Delegate",
    "Annotation", "Constructor", "Template",
    "Process", "Community",
}


def test_node_label_count() -> None:
    """NodeLabel enum has at least 27 values."""
    assert len(NodeLabel) >= 27


def test_all_expected_node_labels_exist() -> None:
    """Every expected label is present in the NodeLabel enum."""
    actual = {member.value for member in NodeLabel}
    missing = EXPECTED_NODE_LABELS - actual
    assert not missing, f"Missing NodeLabel values: {missing}"


# --- Relationship type completeness ---

EXPECTED_REL_TYPES: set[str] = {
    "CONTAINS", "CALLS", "IMPORTS", "EXTENDS", "IMPLEMENTS",
    "HAS_TYPE", "RETURNS_TYPE", "PARAM_TYPE",
    "MEMBER_OF", "BELONGS_TO_COMMUNITY", "PART_OF_PROCESS",
    "DEFINES", "OVERRIDES", "EXPORTS",
}


def test_all_expected_relationship_types_exist() -> None:
    """Every expected relationship type is in the RelationshipType enum."""
    actual = {member.value for member in RelationshipType}
    missing = EXPECTED_REL_TYPES - actual
    assert not missing, f"Missing RelationshipType values: {missing}"


# --- Schema SQL validity ---


def test_node_schemas_start_with_create() -> None:
    """Every node table schema is a valid CREATE statement."""
    for schema in NODE_TABLE_SCHEMAS:
        assert schema.strip().startswith("CREATE"), (
            f"Schema does not start with CREATE: {schema[:60]}"
        )


def test_rel_schemas_start_with_create() -> None:
    """Every relationship table schema is a valid CREATE statement."""
    for schema in REL_TABLE_SCHEMAS:
        assert schema.strip().startswith("CREATE"), (
            f"Schema does not start with CREATE: {schema[:60]}"
        )


def test_all_schemas_combines_nodes_and_rels() -> None:
    """SCHEMA_QUERIES includes nodes, rels, and embedding table."""
    from ai_codebase_intelligence._storage.kuzu_schema import SCHEMA_QUERIES
    assert len(SCHEMA_QUERIES) > len(NODE_TABLE_SCHEMAS)


def test_fts_index_schemas_are_call_statements() -> None:
    """FTS index schemas use CALL CREATE_FTS_INDEX."""
    for schema in FTS_INDEX_SCHEMAS:
        assert "CREATE_FTS_INDEX" in schema


def test_vector_index_schemas_are_call_statements() -> None:
    """Vector index schemas use CALL CREATE_VECTOR_INDEX."""
    for schema in VECTOR_INDEX_SCHEMAS:
        assert "CREATE_VECTOR_INDEX" in schema


# --- Node table coverage for new labels ---

_NODE_SCHEMA_TEXT: str = "\n".join(NODE_TABLE_SCHEMAS)

NEW_TABLE_NAMES: list[str] = [
    "Struct", "Macro", "Typedef", "Union", "Trait", "Impl",
    "Const", "Static", "Property", "Record", "Delegate",
    "Annotation", "Constructor", "Template",
]


@pytest.mark.parametrize("table_name", NEW_TABLE_NAMES)
def test_node_table_exists_for(table_name: str) -> None:
    """Node table CREATE statement exists for each new table."""
    # Multi-language tables are backtick-escaped
    assert (
        f"CREATE NODE TABLE IF NOT EXISTS {table_name}" in _NODE_SCHEMA_TEXT
        or f"CREATE NODE TABLE IF NOT EXISTS `{table_name}`" in _NODE_SCHEMA_TEXT
    )


# --- Relationship table coverage ---

_REL_SCHEMA_TEXT: str = "\n".join(REL_TABLE_SCHEMAS)


def test_coderelation_table_exists() -> None:
    """Single CodeRelation table exists in rel schema."""
    assert "CodeRelation" in _REL_SCHEMA_TEXT

def test_coderelation_has_type_property() -> None:
    """CodeRelation table has type STRING property."""
    assert "type STRING" in _REL_SCHEMA_TEXT

def test_coderelation_has_confidence() -> None:
    """CodeRelation table has confidence DOUBLE property."""
    assert "confidence DOUBLE" in _REL_SCHEMA_TEXT


# --- RenameInput / RenameOutput model validation ---


def test_rename_input_defaults() -> None:
    """RenameInput accepts old_name and new_name with default repo_path."""
    inp = RenameInput(old_name="foo", new_name="bar")
    assert inp.old_name == "foo"
    assert inp.new_name == "bar"
    assert inp.repo_path == ""


def test_rename_output_defaults() -> None:
    """RenameOutput defaults to empty lists and zero counts."""
    out = RenameOutput()
    assert out.files_affected == []
    assert out.symbols_renamed == 0
    assert out.relationships_updated == 0


def test_rename_output_with_data() -> None:
    """RenameOutput populates correctly with explicit data."""
    out = RenameOutput(
        files_affected=["/a.py", "/b.py"],
        symbols_renamed=3,
        relationships_updated=5,
    )
    assert len(out.files_affected) == 2
    assert out.symbols_renamed == 3
    assert out.relationships_updated == 5
