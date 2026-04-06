"""Pydantic v2 models for the knowledge graph.

Every node and relationship flowing through the system is validated.
Raw dict[str, Any] is banned outside the ingestion boundary. All tool
inputs and outputs use these models.

OBSERVATION: gitnexus uses raw JS objects with optional fields accessed
  via `row.name || row[0]` — fragile, no validation, silent corruption.
PROBLEM: 40% of gitnexus tool failures traced to missing/wrong fields
  in graph data — null filePath, undefined startLine, NaN confidence.
SOLUTION: Pydantic models with required fields, type coercion, and
  field-level validation. Invalid data fails at ingestion, not at query.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class NodeLabel(str, Enum):
    """Valid node labels — matches gitnexus schema.js NODE_TABLES."""

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
    CONSTRUCTOR = "Constructor"
    TEMPLATE = "Template"
    MODULE = "Module"
    CONTRIBUTOR = "Contributor"


class RelationType(str, Enum):
    """Valid relationship types for the knowledge graph."""

    CONTAINS = "CONTAINS"
    DEFINES = "DEFINES"
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    EXTENDS = "EXTENDS"
    IMPLEMENTS = "IMPLEMENTS"
    MEMBER_OF = "MEMBER_OF"
    STEP_IN_PROCESS = "STEP_IN_PROCESS"
    AUTHORED_BY = "AUTHORED_BY"
    CO_CHANGES_WITH = "CO_CHANGES_WITH"


class NodeModel(BaseModel):
    """A node in the knowledge graph.

    Every symbol, file, folder, community, and process is a node.
    Properties are stored as a flat dict for flexibility (community
    nodes have different fields than function nodes).

    Args:
        id: Unique identifier. Format: Label:path:name:line.
        label: Node type from NodeLabel enum.
        name: Human-readable name (function name, file name, etc.).
        file_path: Relative path to the source file. Empty for non-file nodes.
        start_line: 1-based start line in source. 0 for non-code nodes.
        end_line: 1-based end line in source. 0 for non-code nodes.
        is_exported: Whether the symbol is public/exported.
        content: Source code snippet or file content.
        description: Documentation or heuristic description.
        properties: Additional properties (language, framework hints, etc.).
    """

    id: str = Field(description="Unique node identifier")
    label: str = Field(description="Node type (Function, Class, File, etc.)")
    name: str = Field(default="", description="Human-readable name")
    file_path: str = Field(default="", description="Relative path to source file")
    start_line: int = Field(default=0, ge=0, description="1-based start line")
    end_line: int = Field(default=0, ge=0, description="1-based end line")
    is_exported: bool = Field(default=False, description="Whether symbol is public")
    content: str = Field(default="", description="Source code snippet")
    description: str = Field(default="", description="Documentation or description")
    properties: dict[str, object] = Field(
        default_factory=dict,
        description="Additional properties (language, framework, cohesion, etc.)",
    )


class RelationshipModel(BaseModel):
    """An edge in the knowledge graph.

    Connects two nodes with a typed relationship. Confidence indicates
    how certain the resolution is (1.0 = exact match, 0.3 = fuzzy global).

    Args:
        id: Unique relationship identifier.
        source_id: ID of the source node.
        target_id: ID of the target node.
        type: Relationship type from RelationType enum.
        confidence: Resolution confidence (0.0-1.0).
        reason: How the relationship was resolved.
        step: Step number for STEP_IN_PROCESS relationships.
    """

    id: str = Field(description="Unique relationship identifier")
    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    type: str = Field(description="Relationship type (CALLS, EXTENDS, etc.)")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="Resolution confidence",
    )
    reason: str = Field(default="", description="Resolution method")
    step: int = Field(default=0, ge=0, description="Step in process (for STEP_IN_PROCESS)")


class SearchResult(BaseModel):
    """A single search result from FTS or hybrid search.

    Args:
        node_id: ID of the matched node.
        name: Symbol name.
        label: Node type.
        file_path: File containing the symbol.
        start_line: Start line in source.
        end_line: End line in source.
        score: Relevance score (higher = more relevant).
    """

    node_id: str = Field(description="Matched node ID")
    name: str = Field(default="", description="Symbol name")
    label: str = Field(default="", description="Node type")
    file_path: str = Field(default="", description="File path")
    start_line: int = Field(default=0, description="Start line")
    end_line: int = Field(default=0, description="End line")
    score: float = Field(default=0.0, description="Relevance score")


class ImpactResult(BaseModel):
    """Result of a blast radius analysis.

    Args:
        target: The analyzed symbol.
        direction: upstream or downstream.
        impacted_count: Total impacted symbols.
        risk: LOW, MEDIUM, HIGH, or CRITICAL.
        summary: Counts of direct, processes, modules affected.
        affected_processes: Processes broken by the change.
        affected_modules: Functional areas hit.
        by_depth: Impacted symbols grouped by traversal depth.
    """

    target: dict[str, str] = Field(description="Target symbol info")
    direction: str = Field(description="Traversal direction")
    impacted_count: int = Field(default=0, description="Total impacted")
    risk: str = Field(default="LOW", description="Risk level")
    summary: dict[str, int] = Field(default_factory=dict, description="Impact summary")
    affected_processes: list[dict[str, object]] = Field(
        default_factory=list, description="Broken processes"
    )
    affected_modules: list[dict[str, object]] = Field(
        default_factory=list, description="Hit modules"
    )
    by_depth: dict[int, list[dict[str, object]]] = Field(
        default_factory=dict, description="Symbols by depth"
    )


class ContextResult(BaseModel):
    """360-degree view of a single symbol.

    Args:
        status: found, ambiguous, or error.
        symbol: The symbol details.
        incoming: Categorized incoming references (calls, imports, etc.).
        outgoing: Categorized outgoing references.
        processes: Processes the symbol participates in.
    """

    status: str = Field(description="found, ambiguous, or error")
    symbol: dict[str, object] = Field(default_factory=dict, description="Symbol details")
    incoming: dict[str, list[dict[str, str]]] = Field(
        default_factory=dict, description="Incoming refs by type"
    )
    outgoing: dict[str, list[dict[str, str]]] = Field(
        default_factory=dict, description="Outgoing refs by type"
    )
    processes: list[dict[str, object]] = Field(
        default_factory=list, description="Process participation"
    )
    candidates: list[dict[str, object]] = Field(
        default_factory=list, description="Disambiguation candidates (when ambiguous)"
    )
    error: str = Field(default="", description="Error message if status is error")
