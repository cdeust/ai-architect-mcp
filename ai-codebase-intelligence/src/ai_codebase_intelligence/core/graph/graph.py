from __future__ import annotations
from typing import Any, Callable, Iterator


class KnowledgeGraph:
    def __init__(self) -> None:
        self._node_map: dict[str, dict[str, Any]] = {}
        self._relationship_map: dict[str, dict[str, Any]] = {}

    def add_node(self, node: dict[str, Any]) -> None:
        if node["id"] not in self._node_map:
            self._node_map[node["id"]] = node

    def add_relationship(self, relationship: dict[str, Any]) -> None:
        if relationship["id"] not in self._relationship_map:
            self._relationship_map[relationship["id"]] = relationship

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._node_map:
            return False
        del self._node_map[node_id]
        # Remove all relationships involving this node
        to_remove = [
            rel_id
            for rel_id, rel in self._relationship_map.items()
            if rel["sourceId"] == node_id or rel["targetId"] == node_id
        ]
        for rel_id in to_remove:
            del self._relationship_map[rel_id]
        return True

    def remove_nodes_by_file(self, file_path: str) -> int:
        removed = 0
        node_ids = [
            nid
            for nid, node in self._node_map.items()
            if node.get("properties", {}).get("filePath") == file_path
        ]
        for nid in node_ids:
            self.remove_node(nid)
            removed += 1
        return removed

    @property
    def nodes(self) -> list[dict[str, Any]]:
        return list(self._node_map.values())

    @property
    def relationships(self) -> list[dict[str, Any]]:
        return list(self._relationship_map.values())

    def iter_nodes(self) -> Iterator[dict[str, Any]]:
        return iter(self._node_map.values())

    def iter_relationships(self) -> Iterator[dict[str, Any]]:
        return iter(self._relationship_map.values())

    def for_each_node(self, fn: Callable[[dict[str, Any]], None]) -> None:
        for node in self._node_map.values():
            fn(node)

    def for_each_relationship(self, fn: Callable[[dict[str, Any]], None]) -> None:
        for rel in self._relationship_map.values():
            fn(rel)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        return self._node_map.get(node_id)

    @property
    def node_count(self) -> int:
        return len(self._node_map)

    @property
    def relationship_count(self) -> int:
        return len(self._relationship_map)


def create_knowledge_graph() -> KnowledgeGraph:
    return KnowledgeGraph()
