"""Tests for the _embeddings subsystem."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai_codebase_intelligence._embeddings.embedder import (
    EmbeddingModel,
    _SENTENCE_TRANSFORMERS_AVAILABLE,
)
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
    name: str = "my_func",
    label: NodeLabel = NodeLabel.FUNCTION,
    file_path: str = "/src/app.py",
    signature: str = "def my_func(x: int) -> str",
    docstring: str = "Does something useful.",
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
# text_generator: node_to_text
# ---------------------------------------------------------------------------

class TestNodeToText:
    """Tests for node_to_text formatting."""

    def test_full_node(self) -> None:
        node = _make_node()
        text = node_to_text(node)
        assert text == (
            "Function my_func in /src/app.py\n"
            "def my_func(x: int) -> str\n"
            "Does something useful."
        )

    def test_no_signature(self) -> None:
        node = _make_node(signature="")
        text = node_to_text(node)
        assert "def my_func" not in text
        assert "Does something useful." in text

    def test_no_docstring(self) -> None:
        node = _make_node(docstring="")
        text = node_to_text(node)
        assert text.endswith("def my_func(x: int) -> str")

    def test_no_signature_no_docstring(self) -> None:
        node = _make_node(signature="", docstring="")
        text = node_to_text(node)
        assert text == "Function my_func in /src/app.py"

    def test_class_node(self) -> None:
        node = _make_node(
            name="MyClass",
            label=NodeLabel.CLASS,
            signature="class MyClass(Base):",
            docstring="A class.",
        )
        text = node_to_text(node)
        assert text.startswith("Class MyClass in")

    def test_file_node(self) -> None:
        node = _make_node(
            name="utils.py",
            label=NodeLabel.FILE,
            signature="",
            docstring="Utility functions.",
        )
        text = node_to_text(node)
        assert text.startswith("File utils.py in")


# ---------------------------------------------------------------------------
# text_generator: nodes_to_texts
# ---------------------------------------------------------------------------

class TestNodesToTexts:
    """Tests for batch conversion."""

    def test_returns_id_text_pairs(self) -> None:
        nodes = [
            _make_node(name="a", node_id="id-a"),
            _make_node(name="b", node_id="id-b"),
        ]
        pairs = nodes_to_texts(nodes)
        assert len(pairs) == 2
        assert pairs[0][0] == "id-a"
        assert pairs[1][0] == "id-b"
        assert "a" in pairs[0][1]
        assert "b" in pairs[1][1]

    def test_empty_list(self) -> None:
        assert nodes_to_texts([]) == []


# ---------------------------------------------------------------------------
# embedding_pipeline: incremental skipping
# ---------------------------------------------------------------------------

class TestEmbeddingPipelineIncremental:
    """Tests for EmbeddingPipeline.embed_incremental."""

    def test_skips_existing_ids(self) -> None:
        """Nodes whose IDs are in existing_ids must not be embedded."""
        mock_model = MagicMock(spec=EmbeddingModel)
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]

        pipeline = EmbeddingPipeline(model=mock_model)

        nodes = [
            _make_node(name="old", node_id="id-old"),
            _make_node(name="new", node_id="id-new"),
        ]
        result = pipeline.embed_incremental(
            nodes, existing_ids={"id-old"}
        )

        assert "id-old" not in result
        assert "id-new" in result
        # encode should have been called once with only the new node's text
        mock_model.encode.assert_called_once()
        call_texts = mock_model.encode.call_args[0][0]
        assert len(call_texts) == 1

    def test_all_existing_returns_empty(self) -> None:
        mock_model = MagicMock(spec=EmbeddingModel)
        pipeline = EmbeddingPipeline(model=mock_model)

        nodes = [_make_node(name="a", node_id="id-a")]
        result = pipeline.embed_incremental(nodes, existing_ids={"id-a"})

        assert result == {}
        mock_model.encode.assert_not_called()

    def test_none_existing_embeds_all(self) -> None:
        mock_model = MagicMock(spec=EmbeddingModel)
        mock_model.encode.return_value = [[0.1], [0.2]]

        pipeline = EmbeddingPipeline(model=mock_model)

        nodes = [
            _make_node(name="a", node_id="id-a"),
            _make_node(name="b", node_id="id-b"),
        ]
        result = pipeline.embed_incremental(nodes, existing_ids=set())

        assert len(result) == 2


# ---------------------------------------------------------------------------
# embedder: graceful ImportError handling
# ---------------------------------------------------------------------------

class TestEmbedderImportError:
    """Tests for EmbeddingModel when sentence-transformers is missing."""

    def test_load_raises_import_error_when_missing(self) -> None:
        with patch(
            "ai_codebase_intelligence._embeddings.embedder._SENTENCE_TRANSFORMERS_AVAILABLE",
            False,
        ):
            model = EmbeddingModel()
            with pytest.raises(ImportError, match="sentence-transformers"):
                model.load()

    def test_encode_raises_import_error_when_missing(self) -> None:
        with patch(
            "ai_codebase_intelligence._embeddings.embedder._SENTENCE_TRANSFORMERS_AVAILABLE",
            False,
        ):
            model = EmbeddingModel()
            with pytest.raises(ImportError, match="sentence-transformers"):
                model.encode(["hello"])

    def test_encode_empty_returns_empty(self) -> None:
        """Empty input should return empty list without loading model."""
        model = EmbeddingModel()
        assert model.encode([]) == []
