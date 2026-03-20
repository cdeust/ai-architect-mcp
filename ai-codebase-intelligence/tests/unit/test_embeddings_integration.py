"""Tests for text_generator format and embedding_pipeline with mock embedder."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai_codebase_intelligence._embeddings.embedder import EmbeddingModel
from ai_codebase_intelligence._embeddings.embedding_pipeline import (
    EmbeddingPipeline,
)
from ai_codebase_intelligence._embeddings.text_generator import (
    node_to_text,
    nodes_to_texts,
)
from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_node(
    name: str,
    label: NodeLabel = NodeLabel.FUNCTION,
    file_path: str = "/src/app.py",
    signature: str = "",
    docstring: str = "",
    node_id: str | None = None,
) -> GraphNode:
    """Create a GraphNode for testing."""
    return GraphNode(
        id=node_id or f"{file_path}:{name}:{label.value}",
        label=label,
        name=name,
        file_path=file_path,
        signature=signature,
        docstring=docstring,
    )


# ---------------------------------------------------------------------------
# text_generator: correct format for Function, Class, Method
# ---------------------------------------------------------------------------


class TestTextGeneratorFormats:
    """Test that text_generator produces correct format per node type."""

    def test_function_format(self) -> None:
        node = _make_node(
            name="process_data",
            label=NodeLabel.FUNCTION,
            signature="def process_data(items: list[str]) -> int",
            docstring="Process a list of data items.",
        )
        text = node_to_text(node)
        lines = text.split("\n")
        assert lines[0] == "Function process_data in /src/app.py"
        assert lines[1] == "def process_data(items: list[str]) -> int"
        assert lines[2] == "Process a list of data items."

    def test_class_format(self) -> None:
        node = _make_node(
            name="DataProcessor",
            label=NodeLabel.CLASS,
            signature="class DataProcessor(BaseProcessor):",
            docstring="Handles data processing.",
        )
        text = node_to_text(node)
        lines = text.split("\n")
        assert lines[0] == "Class DataProcessor in /src/app.py"
        assert lines[1] == "class DataProcessor(BaseProcessor):"
        assert lines[2] == "Handles data processing."

    def test_method_format(self) -> None:
        node = _make_node(
            name="run",
            label=NodeLabel.METHOD,
            signature="def run(self, config: Config) -> Result",
            docstring="Execute the processing pipeline.",
        )
        text = node_to_text(node)
        lines = text.split("\n")
        assert lines[0] == "Method run in /src/app.py"
        assert lines[1] == "def run(self, config: Config) -> Result"
        assert lines[2] == "Execute the processing pipeline."

    def test_minimal_node_no_sig_no_doc(self) -> None:
        node = _make_node(
            name="helper",
            label=NodeLabel.FUNCTION,
            signature="",
            docstring="",
        )
        text = node_to_text(node)
        assert text == "Function helper in /src/app.py"

    def test_node_with_signature_only(self) -> None:
        node = _make_node(
            name="calc",
            label=NodeLabel.FUNCTION,
            signature="def calc(x: int) -> int",
            docstring="",
        )
        text = node_to_text(node)
        assert text == (
            "Function calc in /src/app.py\n"
            "def calc(x: int) -> int"
        )


# ---------------------------------------------------------------------------
# text_generator: batch nodes_to_texts
# ---------------------------------------------------------------------------


class TestNodesToTextsBatch:
    """Test batch conversion preserves order and IDs."""

    def test_preserves_node_order(self) -> None:
        nodes = [
            _make_node(name="first", node_id="id-1"),
            _make_node(name="second", node_id="id-2"),
            _make_node(name="third", node_id="id-3"),
        ]
        pairs = nodes_to_texts(nodes)
        assert [p[0] for p in pairs] == ["id-1", "id-2", "id-3"]

    def test_text_contains_node_name(self) -> None:
        nodes = [
            _make_node(name="unique_symbol", node_id="id-u"),
        ]
        pairs = nodes_to_texts(nodes)
        assert "unique_symbol" in pairs[0][1]


# ---------------------------------------------------------------------------
# EmbeddingPipeline with mock embedder
# ---------------------------------------------------------------------------


class TestEmbeddingPipelineMock:
    """Test EmbeddingPipeline without loading a real model."""

    def test_embed_nodes_returns_vectors(self) -> None:
        mock_model = MagicMock(spec=EmbeddingModel)
        mock_model.encode.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        pipeline = EmbeddingPipeline(model=mock_model)
        nodes = [
            _make_node(name="func_a", node_id="id-a"),
            _make_node(name="func_b", node_id="id-b"),
        ]
        result = pipeline.embed_nodes(nodes)

        assert len(result) == 2
        assert "id-a" in result
        assert "id-b" in result
        assert result["id-a"] == [0.1, 0.2, 0.3]
        assert result["id-b"] == [0.4, 0.5, 0.6]

    def test_embed_empty_nodes(self) -> None:
        mock_model = MagicMock(spec=EmbeddingModel)
        pipeline = EmbeddingPipeline(model=mock_model)
        result = pipeline.embed_nodes([])
        assert result == {}
        mock_model.encode.assert_not_called()

    def test_embed_passes_texts_to_model(self) -> None:
        mock_model = MagicMock(spec=EmbeddingModel)
        mock_model.encode.return_value = [[0.1]]

        pipeline = EmbeddingPipeline(model=mock_model)
        nodes = [
            _make_node(
                name="my_func",
                signature="def my_func()",
                docstring="Does stuff",
                node_id="id-1",
            ),
        ]
        pipeline.embed_nodes(nodes)

        mock_model.encode.assert_called_once()
        texts = mock_model.encode.call_args[0][0]
        assert len(texts) == 1
        assert "my_func" in texts[0]

    def test_incremental_embed_skips_existing(self) -> None:
        mock_model = MagicMock(spec=EmbeddingModel)
        mock_model.encode.return_value = [[0.9, 0.8]]

        pipeline = EmbeddingPipeline(model=mock_model)
        nodes = [
            _make_node(name="old_func", node_id="id-old"),
            _make_node(name="new_func", node_id="id-new"),
        ]
        result = pipeline.embed_incremental(
            nodes, existing_ids={"id-old"}
        )

        assert "id-old" not in result
        assert "id-new" in result

    def test_batch_size_passed_through(self) -> None:
        mock_model = MagicMock(spec=EmbeddingModel)
        mock_model.encode.return_value = [[0.1]]

        pipeline = EmbeddingPipeline(model=mock_model)
        nodes = [_make_node(name="x", node_id="id-x")]
        pipeline.embed_nodes(nodes, batch_size=64)

        call_kwargs = mock_model.encode.call_args[1]
        assert call_kwargs.get("batch_size") == 64
