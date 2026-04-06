"""Typed graph models — the target API for ai-codebase-intelligence.

Domain value objects (Evans 2003, DDD Ch. 5) implemented as Pydantic
BaseModel. Validation at construction time eliminates an entire class
of "missing field" errors that plagued the raw-dict API.

GraphNode fields are flattened from the legacy nested dict format
(node["properties"]["name"]) per the Law of Demeter (Lieberherr et al.
1988, OOPSLA). The `properties` catch-all dict handles label-specific
extra fields without polluting the core schema.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeLabel(str, Enum):
    """Valid node labels in the knowledge graph."""

    FILE = "File"
    FOLDER = "Folder"
    FUNCTION = "Function"
    CLASS = "Class"
    INTERFACE = "Interface"
    METHOD = "Method"
    CODE_ELEMENT = "CodeElement"
    COMMUNITY = "Community"
    PROCESS = "Process"
    STRUCT = "Struct"
    ENUM = "Enum"
    MACRO = "Macro"
    TYPEDEF = "Typedef"
    UNION = "Union"
    NAMESPACE = "Namespace"
    TRAIT = "Trait"
    IMPL = "Impl"
    TYPE_ALIAS = "TypeAlias"
    CONST = "Const"
    STATIC = "Static"
    PROPERTY = "Property"
    RECORD = "Record"
    DELEGATE = "Delegate"
    ANNOTATION = "Annotation"
    VARIABLE = "Variable"
    CONTRIBUTOR = "Contributor"
    CONSTRUCTOR = "Constructor"
    TEMPLATE = "Template"
    MODULE = "Module"


class RelationshipType(str, Enum):
    """Valid relationship types in the knowledge graph."""

    CONTAINS = "CONTAINS"
    DEFINES = "DEFINES"
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    EXTENDS = "EXTENDS"
    IMPLEMENTS = "IMPLEMENTS"
    MEMBER_OF = "MEMBER_OF"
    STEP_IN_PROCESS = "STEP_IN_PROCESS"
    EXPORTS = "EXPORTS"
    AUTHORED_BY = "AUTHORED_BY"
    CO_CHANGES_WITH = "CO_CHANGES_WITH"
    OVERRIDES = "OVERRIDES"
    USES = "USES"
    TYPE_OF = "TYPE_OF"
    HAS_TYPE = "HAS_TYPE"
    RETURNS_TYPE = "RETURNS_TYPE"
    PARAM_TYPE = "PARAM_TYPE"
    BELONGS_TO_COMMUNITY = "BELONGS_TO_COMMUNITY"
    PART_OF_PROCESS = "PART_OF_PROCESS"


class GraphNode(BaseModel):
    """A node in the knowledge graph.

    Flat attribute access replaces the legacy nested dict pattern
    (node["properties"]["name"] → node.name). The `properties` dict
    is a catch-all for label-specific extra fields.

    Args:
        id: Unique identifier. Format: "filePath:name:Label".
        label: Node type from NodeLabel enum.
        name: Human-readable name (function name, class name, etc.).
        qualified_name: Fully qualified name (e.g., "module.Class.method").
        file_path: Relative path to the source file.
        start_line: 1-based start line. 0 for non-code nodes.
        end_line: 1-based end line. 0 for non-code nodes.
        language: Programming language.
        signature: Function/method signature.
        docstring: Documentation string.
        is_exported: Whether the symbol is public/exported.
        properties: Additional label-specific properties.
    """

    id: str = Field(description="Unique node identifier")
    label: NodeLabel = Field(description="Node type")
    name: str = Field(default="", description="Human-readable name")
    qualified_name: str = Field(default="", description="Fully qualified name")
    file_path: str = Field(default="", description="Relative path to source file")
    start_line: int = Field(default=0, ge=0, description="1-based start line")
    end_line: int = Field(default=0, ge=0, description="1-based end line")
    language: str = Field(default="", description="Programming language")
    signature: str = Field(default="", description="Function/method signature")
    docstring: str = Field(default="", description="Documentation string")
    is_exported: bool = Field(default=False, description="Whether symbol is public")
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional label-specific properties",
    )


class GraphRelationship(BaseModel):
    """An edge in the knowledge graph.

    Args:
        source_id: ID of the source node.
        target_id: ID of the target node.
        relationship_type: Edge type from RelationshipType enum.
        confidence: Resolution confidence (0.0-1.0).
        properties: Additional edge-specific properties.
    """

    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    relationship_type: RelationshipType = Field(description="Edge type")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="Resolution confidence",
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional edge properties",
    )


class KnowledgeGraph:
    """In-memory knowledge graph with typed nodes and relationships.

    This is a behavioral class (not a Pydantic BaseModel) because it
    has graph operations: add, remove, traverse. Internal storage uses
    typed models (GraphNode, GraphRelationship).

    Args:
        repo_path: Absolute path to the repository.
        nodes: Initial nodes keyed by ID.
        relationships: Initial relationships.
        commit_hash: Git commit hash at indexing time.
    """

    def __init__(
        self,
        repo_path: str = "",
        nodes: dict[str, GraphNode] | None = None,
        relationships: list[GraphRelationship] | None = None,
        commit_hash: str = "",
    ) -> None:
        self.repo_path = repo_path
        self.nodes: dict[str, GraphNode] = dict(nodes) if nodes else {}
        self.relationships: list[GraphRelationship] = list(relationships) if relationships else []
        self.commit_hash = commit_hash
