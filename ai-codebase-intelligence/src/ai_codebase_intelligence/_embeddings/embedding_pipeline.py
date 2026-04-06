"""Embedding pipeline — orchestrates text generation and model encoding.

Converts GraphNodes to text, encodes via EmbeddingModel, and returns
a mapping of node_id -> vector. Supports incremental embedding by
skipping nodes whose IDs already exist.
"""

from __future__ import annotations

from .._models.graph_types import GraphNode
from .embedder import EmbeddingModel
from .text_generator import nodes_to_texts


class EmbeddingPipeline:
    """Orchestrates node-to-vector embedding.

    Args:
        model: EmbeddingModel instance (can be a mock for testing).
    """

    def __init__(self, model: EmbeddingModel | None = None) -> None:
        self._model = model or EmbeddingModel()

    def embed_nodes(
        self,
        nodes: list[GraphNode],
        batch_size: int = 32,
    ) -> dict[str, list[float]]:
        """Embed all nodes and return id -> vector mapping.

        Args:
            nodes: Nodes to embed.
            batch_size: Encoding batch size.

        Returns:
            Mapping of node_id to embedding vector.
        """
        if not nodes:
            return {}

        pairs = nodes_to_texts(nodes)
        ids = [p[0] for p in pairs]
        texts = [p[1] for p in pairs]

        vectors = self._model.encode(texts, batch_size=batch_size)
        return dict(zip(ids, vectors))

    def embed_incremental(
        self,
        nodes: list[GraphNode],
        existing_ids: set[str] | None = None,
        batch_size: int = 32,
    ) -> dict[str, list[float]]:
        """Embed only nodes not in existing_ids.

        Args:
            nodes: All candidate nodes.
            existing_ids: IDs to skip (already embedded).
            batch_size: Encoding batch size.

        Returns:
            Mapping of new node_id to embedding vector.
        """
        skip = existing_ids or set()
        new_nodes = [n for n in nodes if n.id not in skip]
        if not new_nodes:
            return {}
        return self.embed_nodes(new_nodes, batch_size=batch_size)
