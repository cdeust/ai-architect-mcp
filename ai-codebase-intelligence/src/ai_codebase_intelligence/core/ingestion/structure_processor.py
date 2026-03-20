from __future__ import annotations

from ...lib.utils import generate_id
from ..graph.graph import KnowledgeGraph


def process_structure(graph: KnowledgeGraph, paths: list[str]) -> None:
    for file_path in paths:
        parts = file_path.split("/")
        current_path = ""
        parent_id = ""

        for index, part in enumerate(parts):
            is_file = index == len(parts) - 1
            label = "File" if is_file else "Folder"
            current_path = f"{current_path}/{part}" if current_path else part
            node_id = generate_id(label, current_path)

            node = {
                "id": node_id,
                "label": label,
                "properties": {
                    "name": part,
                    "filePath": current_path,
                },
            }
            graph.add_node(node)

            if parent_id:
                rel_id = generate_id("CONTAINS", f"{parent_id}->{node_id}")
                relationship = {
                    "id": rel_id,
                    "type": "CONTAINS",
                    "sourceId": parent_id,
                    "targetId": node_id,
                    "confidence": 1.0,
                    "reason": "",
                }
                graph.add_relationship(relationship)

            parent_id = node_id
