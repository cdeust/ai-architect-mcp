"""MCP embedder (read-only).

Singleton factory. Only computes query embeddings for semantic search.
"""
from __future__ import annotations

from typing import Any

MODEL_ID = "Snowflake/snowflake-arctic-embed-xs"
EMBEDDING_DIMS = 384

_embedder: Any = None


def init_embedder() -> Any:
    global _embedder
    if _embedder is not None:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(MODEL_ID)
        return _embedder
    except ImportError:
        raise ImportError("sentence-transformers not installed")


def is_embedder_ready() -> bool:
    return _embedder is not None


def embed_query(query: str) -> list[float]:
    embedder = init_embedder()
    result = embedder.encode(query, normalize_embeddings=True)
    return result.tolist()


def get_embedding_dims() -> int:
    return EMBEDDING_DIMS


def dispose_embedder() -> None:
    global _embedder
    _embedder = None
