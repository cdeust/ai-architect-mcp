"""Graph models — claim relationship graphs and thought graphs.

ClaimRelationshipGraph represents relationships between verification claims
(used by graph-constrained verifier). ThoughtGraph represents reasoning
paths (used by adaptive expansion and tree/graph-of-thoughts algorithms).
"""

from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class NodeType(str, Enum):
    """Type classification for claim graph nodes."""

    REQUIREMENT = "requirement"
    SPECIFICATION = "specification"
    IMPLEMENTATION = "implementation"
    TEST = "test"
    CONSTRAINT = "constraint"


class RelationshipType(str, Enum):
    """Relationship types between claim graph nodes."""

    IMPLIES = "implies"
    REQUIRES = "requires"
    IMPLEMENTS = "implements"
    CONTRADICTS = "contradicts"
    DEPENDS = "depends"
    TESTS = "tests"


class ClaimGraphNode(BaseModel):
    """A node in the claim relationship graph.

    Represents a single claim or requirement that participates
    in relationships with other claims.
    """

    node_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this graph node",
    )
    claim_id: UUID = Field(
        description="ID of the verification claim this node represents",
    )
    label: str = Field(
        description="Human-readable label for the node",
    )
    node_type: NodeType = Field(
        description="Classification of this node",
    )


class ClaimGraphEdge(BaseModel):
    """An edge in the claim relationship graph.

    Represents a directed relationship between two claim nodes.
    """

    source_id: UUID = Field(
        description="ID of the source node",
    )
    target_id: UUID = Field(
        description="ID of the target node",
    )
    relationship: RelationshipType = Field(
        description="Type of relationship from source to target",
    )
    weight: float = Field(
        ge=0.0,
        le=1.0,
        description="Strength of the relationship (0.0-1.0)",
    )


class ClaimRelationshipGraph(BaseModel):
    """Graph of relationships between verification claims.

    Used by the graph-constrained verifier (ALG-003) to detect
    cycles, contradictions, and orphans in claim networks.
    """

    nodes: list[ClaimGraphNode] = Field(
        default_factory=list,
        description="All nodes in the graph",
    )
    edges: list[ClaimGraphEdge] = Field(
        default_factory=list,
        description="All edges in the graph",
    )

    @model_validator(mode="after")
    def validate_edge_references(self) -> ClaimRelationshipGraph:
        """Ensure all edge source/target IDs reference existing nodes."""
        node_ids = {node.node_id for node in self.nodes}
        for edge in self.edges:
            if edge.source_id not in node_ids:
                msg = f"Edge source_id {edge.source_id} does not reference any node in the graph"
                raise ValueError(msg)
            if edge.target_id not in node_ids:
                msg = f"Edge target_id {edge.target_id} does not reference any node in the graph"
                raise ValueError(msg)
        return self


class ThoughtNode(BaseModel):
    """A node in a thought graph (Tree/Graph of Thoughts).

    Represents a single reasoning step or thought in the
    exploration of a problem space.
    """

    node_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this thought node",
    )
    content: str = Field(
        description="The reasoning content of this thought",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this thought (0.0-1.0)",
    )
    depth: int = Field(
        ge=0,
        description="Depth in the thought tree (0 = root)",
    )


class ThoughtEdge(BaseModel):
    """An edge in a thought graph.

    Represents a reasoning connection between two thoughts.
    """

    source_id: UUID = Field(
        description="ID of the source thought node",
    )
    target_id: UUID = Field(
        description="ID of the target thought node",
    )
    relationship: str = Field(
        description="Description of the reasoning connection",
    )
    weight: float = Field(
        ge=0.0,
        le=1.0,
        description="Strength of the connection (0.0-1.0)",
    )


class ThoughtGraph(BaseModel):
    """Graph of reasoning paths for Tree/Graph of Thoughts algorithms.

    Used by adaptive expansion (ALG-008) and related algorithms
    to explore solution spaces through structured reasoning.
    """

    nodes: list[ThoughtNode] = Field(
        default_factory=list,
        description="All thought nodes in the graph",
    )
    edges: list[ThoughtEdge] = Field(
        default_factory=list,
        description="All edges connecting thought nodes",
    )
    root_id: UUID = Field(
        description="ID of the root thought node",
    )

    @model_validator(mode="after")
    def validate_root_exists(self) -> ThoughtGraph:
        """Ensure root_id references an existing node."""
        node_ids = {node.node_id for node in self.nodes}
        if self.nodes and self.root_id not in node_ids:
            msg = f"root_id {self.root_id} does not reference any node in the graph"
            raise ValueError(msg)
        return self
