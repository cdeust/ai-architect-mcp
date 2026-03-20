"""Tests for embedding persistence in the ingestion pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel
from ai_codebase_intelligence._pipeline.embedding_phase import (
    DEFAULT_MODEL_NAME,
    run_embedding_phase,
)
from ai_codebase_intelligence._storage.in_memory_graph import (
    InMemoryGraphStorage,
)


def _make_node(
    name: str = "my_func",
    node_id: str = "id-1",
) -> GraphNode:
    """Create a minimal GraphNode for testing.

    Args:
        name: Node name.
        node_id: Unique node ID.

    Returns:
        A GraphNode instance.
    """
    return GraphNode(
        id=node_id,
        label=NodeLabel.FUNCTION,
        name=name,
        file_path="/src/app.py",
    )


class TestRunEmbeddingPhaseStoresVectors:
    """Verify embedding_phase stores vectors via storage port."""

    @pytest.mark.asyncio
    async def test_stores_embeddings_via_storage(self) -> None:
        """Embeddings produced by the pipeline are persisted."""
        nodes = [_make_node("a", "id-a"), _make_node("b", "id-b")]
        fake_embeddings = {"id-a": [0.1, 0.2], "id-b": [0.3, 0.4]}

        mock_pipeline = MagicMock()
        mock_pipeline.embed_nodes.return_value = fake_embeddings

        storage = InMemoryGraphStorage()

        with patch(
            "ai_codebase_intelligence._embeddings.embedding_pipeline.EmbeddingPipeline",
            return_value=mock_pipeline,
        ):
            count = await run_embedding_phase(nodes, storage)

        assert count == 2
        assert storage._embeddings["id-a"] == [0.1, 0.2]
        assert storage._embeddings["id-b"] == [0.3, 0.4]
        assert storage._embedding_model == DEFAULT_MODEL_NAME

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_nodes(self) -> None:
        """Empty node list returns 0 without calling storage."""
        storage = InMemoryGraphStorage()
        count = await run_embedding_phase([], storage)
        assert count == 0
        assert len(storage._embeddings) == 0

    @pytest.mark.asyncio
    async def test_graceful_import_error(self) -> None:
        """Returns 0 when sentence-transformers is not installed."""
        nodes = [_make_node()]
        storage = InMemoryGraphStorage()

        with patch(
            "ai_codebase_intelligence._embeddings.embedding_pipeline.EmbeddingPipeline",
            side_effect=ImportError("no module"),
        ):
            count = await run_embedding_phase(nodes, storage)

        assert count == 0

    @pytest.mark.asyncio
    async def test_graceful_runtime_error(self) -> None:
        """Returns 0 when embedding pipeline raises RuntimeError."""
        nodes = [_make_node()]
        storage = InMemoryGraphStorage()

        mock_pipeline = MagicMock()
        mock_pipeline.embed_nodes.side_effect = RuntimeError("fail")

        with patch(
            "ai_codebase_intelligence._embeddings.embedding_pipeline.EmbeddingPipeline",
            return_value=mock_pipeline,
        ):
            count = await run_embedding_phase(nodes, storage)

        assert count == 0


class TestStoreEmbeddingsPort:
    """Verify store_embeddings on InMemoryGraphStorage."""

    @pytest.mark.asyncio
    async def test_stores_and_counts(self) -> None:
        """store_embeddings returns correct count."""
        storage = InMemoryGraphStorage()
        embeddings = {"a": [1.0, 2.0], "b": [3.0, 4.0]}
        count = await storage.store_embeddings(embeddings, "test-model")
        assert count == 2
        assert storage._embeddings == embeddings
        assert storage._embedding_model == "test-model"

    @pytest.mark.asyncio
    async def test_empty_embeddings(self) -> None:
        """Empty dict returns 0."""
        storage = InMemoryGraphStorage()
        count = await storage.store_embeddings({}, "test-model")
        assert count == 0

    @pytest.mark.asyncio
    async def test_clear_removes_embeddings(self) -> None:
        """clear() also removes stored embeddings."""
        storage = InMemoryGraphStorage()
        await storage.store_embeddings({"a": [1.0]}, "m")
        await storage.clear()
        assert len(storage._embeddings) == 0
