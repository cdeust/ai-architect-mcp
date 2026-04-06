from __future__ import annotations

from ..._models.graph_types import (
    GraphNode, GraphRelationship, NodeLabel, RelationshipType,
)
from ...lib.utils import generate_id
from ..graph.graph import KnowledgeGraph


def process_structure(graph: KnowledgeGraph, paths: list[str]) -> None:
    for file_path in paths:
        parts = file_path.split("/")
        current_path = ""
        parent_id = ""

        for index, part in enumerate(parts):
            is_file = index == len(parts) - 1
            label = NodeLabel.FILE if is_file else NodeLabel.FOLDER
            current_path = f"{current_path}/{part}" if current_path else part
            node_id = generate_id(label.value, current_path)

            graph.add_node(GraphNode(
                id=node_id, label=label,
                name=part, file_path=current_path,
            ))

            if parent_id:
                graph.add_relationship(GraphRelationship(
                    source_id=parent_id, target_id=node_id,
                    relationship_type=RelationshipType.CONTAINS,
                    confidence=1.0,
                ))

            parent_id = node_id
