"""Embedding phase of the ingestion pipeline.

Orchestrates embedding generation and persistence via the storage port.
Handles graceful degradation when sentence-transformers is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from .._models.graph_types import GraphNode

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


async def run_embedding_phase(
    nodes: list[GraphNode],
    storage: Any,
    model_name: str = DEFAULT_MODEL_NAME,
) -> int:
    """Generate embeddings for nodes and persist via storage.

    Args:
        nodes: Graph nodes to embed.
        storage: Storage port with store_embeddings(embeddings, model) method.
        model_name: Sentence-transformer model name.

    Returns:
        Number of embeddings stored (0 on error or empty input).
    """
    if not nodes:
        return 0

    try:
        from .._embeddings.embedding_pipeline import EmbeddingPipeline

        pipeline = EmbeddingPipeline()
        embeddings = pipeline.embed_nodes(nodes)
    except ImportError:
        logger.warning("Embedding library unavailable — skipping embedding phase")
        return 0
    except RuntimeError:
        logger.warning("Embedding pipeline failed — skipping embedding phase")
        return 0

    count = await storage.store_embeddings(embeddings, model_name)
    return count
