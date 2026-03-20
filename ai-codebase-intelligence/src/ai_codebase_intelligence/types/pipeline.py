from __future__ import annotations
from typing import Any

from ..core.graph.graph import KnowledgeGraph, create_knowledge_graph


def serialize_pipeline_result(result: dict[str, Any]) -> dict[str, Any]:
    graph: KnowledgeGraph = result["graph"]
    return {
        "nodes": list(graph.iter_nodes()),
        "relationships": list(graph.iter_relationships()),
        "repoPath": result["repoPath"],
        "totalFileCount": result["totalFileCount"],
    }


def deserialize_pipeline_result(serialized: dict[str, Any]) -> dict[str, Any]:
    graph = create_knowledge_graph()
    for node in serialized["nodes"]:
        graph.add_node(node)
    for rel in serialized["relationships"]:
        graph.add_relationship(rel)
    return {
        "graph": graph,
        "repoPath": serialized["repoPath"],
        "totalFileCount": serialized["totalFileCount"],
    }
