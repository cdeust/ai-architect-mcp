"""Embedder — core embedding implementation.

Uses sentence-transformers. Optional dependency — degrades gracefully
if not installed.
"""
from __future__ import annotations

from typing import Any

from .types import DEFAULT_EMBEDDING_CONFIG

_embedder: Any = None
_current_device: str | None = None


def get_current_device() -> str | None:
    return _current_device


def init_embedder(config: dict[str, Any] | None = None) -> Any:
    global _embedder, _current_device
    if _embedder is not None:
        return _embedder

    cfg = {**DEFAULT_EMBEDDING_CONFIG, **(config or {})}

    try:
        from sentence_transformers import SentenceTransformer
        model_id = str(cfg.get("modelId", "all-MiniLM-L6-v2"))
        _embedder = SentenceTransformer(model_id)
        _current_device = "cpu"
        return _embedder
    except ImportError:
        raise ImportError(
            "sentence-transformers not installed. "
            "Install with: pip install sentence-transformers"
        )


def is_embedder_ready() -> bool:
    return _embedder is not None


def get_embedder() -> Any:
    if _embedder is None:
        raise RuntimeError("Embedder not initialized. Call init_embedder() first.")
    return _embedder


def embed_text(text: str) -> list[float]:
    embedder = get_embedder()
    result = embedder.encode(text, normalize_embeddings=True)
    return result.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    embedder = get_embedder()
    results = embedder.encode(texts, normalize_embeddings=True)
    return [r.tolist() for r in results]


def embedding_to_array(embedding: list[float]) -> list[float]:
    return list(embedding)


def dispose_embedder() -> None:
    global _embedder, _current_device
    _embedder = None
    _current_device = None


def get_embedding_dims() -> int:
    return int(DEFAULT_EMBEDDING_CONFIG.get("dimensions", 384))
