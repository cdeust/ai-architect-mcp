"""Embedding model wrapper with graceful degradation.

Wraps sentence-transformers with lazy loading. When the library
is not installed, load() and encode() raise ImportError with a
clear message.
"""

from __future__ import annotations

from typing import Any

try:
    import sentence_transformers as _st
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingModel:
    """Wrapper around sentence-transformers SentenceTransformer.

    Lazy-loads the model on first encode(). If sentence-transformers
    is not installed, raises ImportError with install instructions.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: Any = None

    def load(self) -> None:
        """Load the embedding model into memory.

        Raises:
            ImportError: If sentence-transformers is not installed.
        """
        if not _SENTENCE_TRANSFORMERS_AVAILABLE:
            msg = (
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )
            raise ImportError(msg)
        self._model = _st.SentenceTransformer(self._model_name)

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[list[float]]:
        """Encode texts into embedding vectors.

        Args:
            texts: Strings to embed.
            batch_size: Batch size for encoding.

        Returns:
            List of float vectors, one per input text.

        Raises:
            ImportError: If sentence-transformers is not installed.
        """
        if not texts:
            return []

        if not _SENTENCE_TRANSFORMERS_AVAILABLE:
            msg = (
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )
            raise ImportError(msg)

        if self._model is None:
            self.load()

        embeddings = self._model.encode(
            texts, batch_size=batch_size, show_progress_bar=False,
        )
        return [vec.tolist() for vec in embeddings]
