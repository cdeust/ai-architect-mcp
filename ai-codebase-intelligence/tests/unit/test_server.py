"""Tests for server modules (Epic 17)."""

from __future__ import annotations

import time
from unittest.mock import patch, AsyncMock

import pytest

from ai_codebase_intelligence._server.api import (
    APIRequest,
    APIResponse,
    route_request,
    handle_list_repos,
    handle_context,
    handle_query,
    handle_analyze,
    _match_route,
)
from ai_codebase_intelligence._server.mcp_http import (
    MCPSession,
    SessionManager,
    build_cors_headers,
    CORS_HEADERS,
    DEFAULT_SESSION_TTL_SECONDS,
)

_STATS_PATCH = "ai_codebase_intelligence._server.api._query_repo_stats"
_SEARCH_PATCH = "ai_codebase_intelligence._server.api._run_search"
_ANALYZE_PATCH = "ai_codebase_intelligence._tools.codebase_tools.analyze"
_EMPTY_STATS = {"node_count": 0, "edge_count": 0}


def _mock_analyze_output() -> AsyncMock:
    """Create a mock analyze output with zero metrics."""
    m = AsyncMock()
    m.total_nodes = 0
    m.total_relationships = 0
    m.total_files = 0
    m.total_communities = 0
    m.total_processes = 0
    m.duration_seconds = 0.0
    return m


class TestRouteMatching:
    """Tests for URL pattern matching."""

    def test_exact_match(self) -> None:
        result = _match_route("/repos", "/repos")
        assert result == {}

    def test_param_match(self) -> None:
        result = _match_route("/repos/myrepo/context", "/repos/{name}/context")
        assert result == {"name": "myrepo"}

    def test_no_match_different_length(self) -> None:
        result = _match_route("/repos/a/b/c", "/repos/{name}/context")
        assert result is None

    def test_no_match_different_literal(self) -> None:
        result = _match_route("/repos/myrepo/other", "/repos/{name}/context")
        assert result is None

    def test_trailing_slashes_handled(self) -> None:
        result = _match_route("/repos/", "/repos/")
        # Both stripped to "repos" -> match
        assert result is not None


class TestAPIDataclasses:
    """Tests for API request and response dataclasses."""

    def test_request_defaults(self) -> None:
        req = APIRequest(method="GET", path="/repos")
        assert req.query_params == {}
        assert req.body == {}

    def test_response_defaults(self) -> None:
        resp = APIResponse(status=200)
        assert resp.body == {}
        assert resp.headers == {}


class TestAPIHandlers:
    """Tests for REST API handlers."""

    @pytest.mark.asyncio
    async def test_list_repos(self) -> None:
        req = APIRequest(method="GET", path="/repos")
        index = {"myrepo": "/path/to/myrepo"}
        resp = await handle_list_repos(req, index)
        assert resp.status == 200
        assert len(resp.body["repos"]) == 1
        assert resp.body["repos"][0]["name"] == "myrepo"

    @pytest.mark.asyncio
    async def test_context_found(self) -> None:
        req = APIRequest(method="GET", path="/repos/myrepo/context")
        index = {"myrepo": "/path/to/myrepo"}
        with patch(_STATS_PATCH, return_value=_EMPTY_STATS):
            resp = await handle_context(req, "myrepo", index)
        assert resp.status == 200
        assert resp.body["name"] == "myrepo"

    @pytest.mark.asyncio
    async def test_context_not_found(self) -> None:
        req = APIRequest(method="GET", path="/repos/missing/context")
        resp = await handle_context(req, "missing", {})
        assert resp.status == 404

    @pytest.mark.asyncio
    async def test_query_success(self) -> None:
        req = APIRequest(
            method="GET",
            path="/repos/myrepo/query",
            query_params={"q": "search term"},
        )
        index = {"myrepo": "/path/to/myrepo"}
        with patch(_SEARCH_PATCH, return_value=[]):
            resp = await handle_query(req, "myrepo", index)
        assert resp.status == 200
        assert resp.body["query"] == "search term"

    @pytest.mark.asyncio
    async def test_query_missing_q(self) -> None:
        req = APIRequest(method="GET", path="/repos/myrepo/query")
        index = {"myrepo": "/path"}
        resp = await handle_query(req, "myrepo", index)
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_analyze_accepted(self) -> None:
        req = APIRequest(method="POST", path="/repos/myrepo/analyze")
        index = {"myrepo": "/path"}
        with patch(_ANALYZE_PATCH, return_value=_mock_analyze_output()):
            resp = await handle_analyze(req, "myrepo", index)
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_analyze_not_found(self) -> None:
        req = APIRequest(method="POST", path="/repos/missing/analyze")
        resp = await handle_analyze(req, "missing", {})
        assert resp.status == 404


class TestRouter:
    """Tests for the request router."""

    @pytest.mark.asyncio
    async def test_route_list_repos(self) -> None:
        req = APIRequest(method="GET", path="/repos")
        resp = await route_request(req, {"r": "/p"})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_route_context(self) -> None:
        req = APIRequest(method="GET", path="/repos/r/context")
        with patch(_STATS_PATCH, return_value=_EMPTY_STATS):
            resp = await route_request(req, {"r": "/p"})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_route_query(self) -> None:
        req = APIRequest(
            method="GET", path="/repos/r/query",
            query_params={"q": "test"},
        )
        with patch(_SEARCH_PATCH, return_value=[]):
            resp = await route_request(req, {"r": "/p"})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_route_analyze(self) -> None:
        req = APIRequest(method="POST", path="/repos/r/analyze")
        with patch(_ANALYZE_PATCH, return_value=_mock_analyze_output()):
            resp = await route_request(req, {"r": "/p"})
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_route_not_found(self) -> None:
        req = APIRequest(method="GET", path="/unknown")
        resp = await route_request(req, {})
        assert resp.status == 404


class TestMCPSession:
    """Tests for MCP session management."""

    def test_session_not_expired(self) -> None:
        session = MCPSession(
            session_id="abc",
            created_at=time.time(),
            last_active=time.time(),
            ttl_seconds=300,
        )
        assert session.is_expired is False

    def test_session_expired(self) -> None:
        old_time = time.time() - 600
        session = MCPSession(
            session_id="abc",
            created_at=old_time,
            last_active=old_time,
            ttl_seconds=300,
        )
        assert session.is_expired is True

    def test_session_touch(self) -> None:
        old_time = time.time() - 100
        session = MCPSession(
            session_id="abc",
            created_at=old_time,
            last_active=old_time,
        )
        session.touch()
        assert (time.time() - session.last_active) < 1


class TestSessionManager:
    """Tests for the SessionManager."""

    def test_create_session(self) -> None:
        mgr = SessionManager()
        session = mgr.create_session()
        assert session.session_id
        assert mgr.active_count() == 1

    def test_get_session(self) -> None:
        mgr = SessionManager()
        session = mgr.create_session()
        retrieved = mgr.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    def test_get_nonexistent_session(self) -> None:
        mgr = SessionManager()
        assert mgr.get_session("nonexistent") is None

    def test_remove_session(self) -> None:
        mgr = SessionManager()
        session = mgr.create_session()
        assert mgr.remove_session(session.session_id) is True
        assert mgr.active_count() == 0

    def test_remove_nonexistent(self) -> None:
        mgr = SessionManager()
        assert mgr.remove_session("nope") is False

    def test_expired_session_evicted(self) -> None:
        mgr = SessionManager(ttl_seconds=0)
        session = mgr.create_session()
        # Session TTL is 0 so it's immediately expired
        retrieved = mgr.get_session(session.session_id)
        assert retrieved is None

    def test_max_sessions_enforced(self) -> None:
        mgr = SessionManager(max_sessions=2)
        mgr.create_session()
        mgr.create_session()
        with pytest.raises(RuntimeError, match="Maximum session limit"):
            mgr.create_session()

    def test_metadata_stored(self) -> None:
        mgr = SessionManager()
        session = mgr.create_session(metadata={"user": "test"})
        assert session.metadata["user"] == "test"


class TestCORSHeaders:
    """Tests for CORS header generation."""

    def test_default_cors_headers(self) -> None:
        headers = build_cors_headers()
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "POST" in headers["Access-Control-Allow-Methods"]

    def test_cors_with_extras(self) -> None:
        headers = build_cors_headers({"X-Custom": "value"})
        assert headers["X-Custom"] == "value"
        # Original headers still present
        assert "Access-Control-Allow-Origin" in headers

    def test_default_ttl_value(self) -> None:
        assert DEFAULT_SESSION_TTL_SECONDS == 1800
