"""Tests for the REST API HTTP server handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ai_codebase_intelligence._server.api import (
    APIRequest,
    APIResponse,
    _match_route,
    handle_context,
    handle_query,
    handle_analyze,
    route_request,
    ROUTE_CONTEXT,
    ROUTE_QUERY,
    ROUTE_ANALYZE,
)


class TestRouteMatchingDetailed:
    """Tests for route pattern matching."""

    def test_repos_route(self) -> None:
        """Exact /repos match returns empty params."""
        result = _match_route("/repos", "/repos")
        assert result == {}

    def test_context_route_extracts_name(self) -> None:
        """Context route extracts repo name."""
        result = _match_route("/repos/myrepo/context", ROUTE_CONTEXT)
        assert result == {"name": "myrepo"}

    def test_query_route_extracts_name(self) -> None:
        """Query route extracts repo name."""
        result = _match_route("/repos/foo/query", ROUTE_QUERY)
        assert result == {"name": "foo"}

    def test_analyze_route_extracts_name(self) -> None:
        """Analyze route extracts repo name."""
        result = _match_route("/repos/bar/analyze", ROUTE_ANALYZE)
        assert result == {"name": "bar"}

    def test_no_match_wrong_path(self) -> None:
        """Mismatched path returns None."""
        result = _match_route("/unknown/path", ROUTE_CONTEXT)
        assert result is None


class TestHandleQueryCallsSearch:
    """Verify handle_query calls the hybrid search engine."""

    @pytest.mark.asyncio
    async def test_calls_search_for_valid_query(self) -> None:
        """handle_query invokes _run_search with correct args."""
        req = APIRequest(
            method="GET",
            path="/repos/myrepo/query",
            query_params={"q": "hello"},
        )
        index = {"myrepo": "/path/to/myrepo"}

        mock_output = AsyncMock()
        mock_output.results = []
        mock_output.total_matches = 0

        with patch(
            "ai_codebase_intelligence._server.handlers._run_search",
            return_value=[],
        ) as mock_search:
            resp = await handle_query(req, "myrepo", index)

        assert resp.status == 200
        assert resp.body["query"] == "hello"
        assert resp.body["total_matches"] == 0
        mock_search.assert_called_once_with("/path/to/myrepo", "hello")

    @pytest.mark.asyncio
    async def test_returns_400_for_missing_query(self) -> None:
        """Missing q param returns 400."""
        req = APIRequest(method="GET", path="/repos/r/query")
        resp = await handle_query(req, "r", {"r": "/p"})
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_repo(self) -> None:
        """Unknown repo returns 404."""
        req = APIRequest(
            method="GET",
            path="/repos/unknown/query",
            query_params={"q": "test"},
        )
        resp = await handle_query(req, "unknown", {})
        assert resp.status == 404


class TestHandleContextCallsGraph:
    """Verify handle_context queries graph for stats."""

    @pytest.mark.asyncio
    async def test_returns_stats(self) -> None:
        """handle_context includes node/edge counts."""
        req = APIRequest(method="GET", path="/repos/r/context")
        index = {"r": "/path/to/r"}

        fake_stats = {"node_count": 42, "edge_count": 10}
        with patch(
            "ai_codebase_intelligence._server.handlers._query_repo_stats",
            return_value=fake_stats,
        ):
            resp = await handle_context(req, "r", index)

        assert resp.status == 200
        assert resp.body["node_count"] == 42
        assert resp.body["edge_count"] == 10
        assert resp.body["name"] == "r"


class TestHandleAnalyzeTriggersIndexing:
    """Verify handle_analyze calls the real analyze function."""

    @pytest.mark.asyncio
    async def test_successful_analysis(self) -> None:
        """Successful analysis returns 200 with metrics."""
        req = APIRequest(
            method="POST",
            path="/repos/r/analyze",
            body={},
        )
        index = {"r": "/path/to/r"}

        mock_output = AsyncMock()
        mock_output.total_nodes = 100
        mock_output.total_relationships = 50
        mock_output.total_files = 10
        mock_output.total_communities = 3
        mock_output.total_processes = 2
        mock_output.duration_seconds = 1.5

        with patch(
            "ai_codebase_intelligence._tools.codebase_tools.analyze",
            return_value=mock_output,
        ):
            resp = await handle_analyze(req, "r", index)

        assert resp.status == 200
        assert resp.body["total_nodes"] == 100
        assert resp.body["status"] == "completed"

    @pytest.mark.asyncio
    async def test_analysis_failure_returns_500(self) -> None:
        """Failed analysis returns 500 with error."""
        req = APIRequest(method="POST", path="/repos/r/analyze")
        index = {"r": "/path/to/r"}

        with patch(
            "ai_codebase_intelligence._tools.codebase_tools.analyze",
            side_effect=RuntimeError("index failed"),
        ):
            resp = await handle_analyze(req, "r", index)

        assert resp.status == 500
        assert "index failed" in resp.body["error"]


class TestRouterDispatch:
    """Verify route_request dispatches to correct handlers."""

    @pytest.mark.asyncio
    async def test_routes_to_query(self) -> None:
        """GET /repos/{name}/query routes to handle_query."""
        req = APIRequest(
            method="GET",
            path="/repos/r/query",
            query_params={"q": "test"},
        )
        with patch(
            "ai_codebase_intelligence._server.handlers._run_search",
            return_value=[],
        ):
            resp = await route_request(req, {"r": "/p"})
        assert resp.status == 200
        assert resp.body["query"] == "test"
