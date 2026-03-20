"""Tests for in-memory search, RRF fusion, and the unified search engine."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._models.graph_types import GraphNode, NodeLabel
from ai_codebase_intelligence._models.search_types import (
    BM25Result,
    HybridSearchResult,
    SearchResultKind,
)
from ai_codebase_intelligence._search.hybrid_search import (
    RRF_K,
    _build_ranked_items,
    _compute_rrf,
)
from ai_codebase_intelligence._search.in_memory_search import search_nodes
from ai_codebase_intelligence._search.search_engine import search
from ai_codebase_intelligence._storage.in_memory_graph import (
    InMemoryGraphStorage,
)


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


def _build_nodes(*specs: tuple[str, str, str]) -> dict[str, GraphNode]:
    """Build a dict of nodes from (name, signature, docstring) tuples."""
    nodes: dict[str, GraphNode] = {}
    for name, sig, doc in specs:
        node = _make_node(name=name, signature=sig, docstring=doc)
        nodes[node.id] = node
    return nodes


# ---------------------------------------------------------------------------
# In-memory search: basic matching
# ---------------------------------------------------------------------------


class TestInMemorySearchBasic:
    """Tests for in-memory text search finding nodes by name."""

    def test_finds_node_by_exact_name(self) -> None:
        nodes = _build_nodes(
            ("process_data", "def process_data(items)", "Process items"),
            ("send_email", "def send_email(to)", "Send an email"),
        )
        results = search_nodes("process_data", nodes)
        assert len(results) >= 1
        assert results[0].snippet == "process_data"

    def test_finds_node_by_partial_name(self) -> None:
        nodes = _build_nodes(
            ("process_data", "def process_data(items)", ""),
            ("data_loader", "def data_loader(path)", ""),
        )
        results = search_nodes("data", nodes)
        assert len(results) == 2

    def test_empty_query_returns_empty(self) -> None:
        nodes = _build_nodes(("foo", "", ""))
        results = search_nodes("", nodes)
        assert results == []

    def test_empty_nodes_returns_empty(self) -> None:
        results = search_nodes("foo", {})
        assert results == []

    def test_no_match_returns_empty(self) -> None:
        nodes = _build_nodes(("alpha", "", ""))
        results = search_nodes("zzzznotfound", nodes)
        assert results == []


# ---------------------------------------------------------------------------
# In-memory search: ranking
# ---------------------------------------------------------------------------


class TestInMemorySearchRanking:
    """Tests for in-memory search ranking exact matches higher."""

    def test_exact_name_ranks_higher_than_partial(self) -> None:
        nodes = _build_nodes(
            ("parse", "def parse(text)", "Parse input text"),
            ("parse_json", "def parse_json(data)", "Parse JSON data"),
            ("unrelated", "def unrelated()", "Does parsing internally"),
        )
        results = search_nodes("parse", nodes)
        assert len(results) >= 2
        # The node named exactly "parse" should rank first
        assert results[0].snippet == "parse"

    def test_respects_limit(self) -> None:
        nodes = _build_nodes(
            ("a_func", "", "a keyword"),
            ("b_func", "", "a keyword"),
            ("c_func", "", "a keyword"),
        )
        results = search_nodes("keyword", nodes, limit=2)
        assert len(results) <= 2

    def test_signature_match_contributes_to_score(self) -> None:
        nodes = _build_nodes(
            ("foo", "def foo(widget: Widget)", ""),
            ("bar", "", "Uses widget parameter"),
        )
        results = search_nodes("widget", nodes)
        assert len(results) >= 1
        # "foo" has widget in signature (weight 2.0) vs "bar" in docstring (1.0)
        assert results[0].snippet == "foo"


# ---------------------------------------------------------------------------
# RRF fusion with multiple result lists
# ---------------------------------------------------------------------------


class TestRRFFusion:
    """Tests for RRF fusion across BM25 and process rankings."""

    def test_rrf_single_list_scores(self) -> None:
        bm25 = [
            BM25Result(node_id="a", score=5.0, matched_field="name"),
            BM25Result(node_id="b", score=3.0, matched_field="name"),
        ]
        ranked = _build_ranked_items(bm25)
        scores = _compute_rrf(ranked)
        expected_a = 1.0 / (RRF_K + 0 + 1)
        expected_b = 1.0 / (RRF_K + 1 + 1)
        assert abs(scores["a"] - expected_a) < 1e-9
        assert abs(scores["b"] - expected_b) < 1e-9

    def test_rrf_preserves_ordering(self) -> None:
        bm25 = [
            BM25Result(node_id="x", score=10.0, matched_field="name"),
            BM25Result(node_id="y", score=5.0, matched_field="name"),
            BM25Result(node_id="z", score=1.0, matched_field="name"),
        ]
        ranked = _build_ranked_items(bm25)
        scores = _compute_rrf(ranked)
        assert scores["x"] > scores["y"] > scores["z"]

    def test_metadata_populated_from_snippet(self) -> None:
        bm25 = [
            BM25Result(
                node_id="n1",
                score=2.0,
                matched_field="name",
                snippet="my_function",
                table_name="Function",
            ),
        ]
        ranked = _build_ranked_items(bm25)
        item = ranked["n1"]
        assert item.metadata is not None
        assert item.metadata["name"] == "my_function"


# ---------------------------------------------------------------------------
# Unified search engine with process boost
# ---------------------------------------------------------------------------


class TestSearchEngineWithProcessBoost:
    """Tests for the unified search engine with process members."""

    @pytest.mark.asyncio
    async def test_search_with_process_boost(self) -> None:
        nodes = _build_nodes(
            ("handle_request", "def handle_request(req)", "Handle HTTP"),
            ("validate_input", "def validate_input(data)", "Validate"),
            ("unrelated_func", "def unrelated_func()", "Unrelated"),
        )
        process_members = {
            "http_flow": [
                "/src/app.py:handle_request:Function",
                "/src/app.py:validate_input:Function",
            ]
        }
        storage = InMemoryGraphStorage()

        results = await search(
            "handle",
            storage,
            nodes=nodes,
            process_members=process_members,
        )
        assert len(results) >= 1
        top = results[0]
        assert top.name == "handle_request"
        assert top.process_score > 0.0

    @pytest.mark.asyncio
    async def test_search_empty_query(self) -> None:
        storage = InMemoryGraphStorage()
        results = await search("", storage)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_community_cohesion(self) -> None:
        nodes = _build_nodes(
            ("alpha", "def alpha()", "Alpha function"),
            ("beta", "def beta()", "Beta function"),
        )
        node_community = {
            "/src/app.py:alpha:Function": "comm-1",
            "/src/app.py:beta:Function": "comm-2",
        }
        community_cohesion = {
            "comm-1": 0.9,
            "comm-2": 0.1,
        }
        storage = InMemoryGraphStorage()

        results = await search(
            "alpha",
            storage,
            nodes=nodes,
            community_cohesion=community_cohesion,
            node_community=node_community,
        )
        assert len(results) >= 1
        # alpha is in comm-1 with cohesion 0.9
        assert results[0].cohesion_score == 0.9

    @pytest.mark.asyncio
    async def test_search_returns_hybrid_results(self) -> None:
        nodes = _build_nodes(
            ("my_func", "def my_func()", "A function"),
        )
        storage = InMemoryGraphStorage()

        results = await search("my_func", storage, nodes=nodes)
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, HybridSearchResult)
        assert result.name == "my_func"
        assert result.rrf_score > 0.0
        assert result.bm25_score > 0.0
