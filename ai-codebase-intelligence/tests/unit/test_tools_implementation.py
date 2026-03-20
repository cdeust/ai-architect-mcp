"""Tests for the MCP tool implementations."""

from __future__ import annotations

import pytest

from ai_codebase_intelligence._tools.codebase_tools import (
    cypher_query,
    list_indexed_repos,
)


class TestListIndexedRepos:
    """Tests for list_indexed_repos."""

    async def test_returns_correct_format(self) -> None:
        """list_indexed_repos should return ListReposOutput with repos list."""
        result = await list_indexed_repos()

        assert hasattr(result, "repos")
        assert isinstance(result.repos, list)
        for repo in result.repos:
            assert "name" in repo
            assert "path" in repo


class TestCypherQuery:
    """Tests for cypher_query write-operation blocking."""

    async def test_blocks_create(self) -> None:
        """CREATE statements should be blocked."""
        with pytest.raises(ValueError, match="prohibited keyword"):
            await cypher_query("CREATE (n:Node {name: 'test'})")

    async def test_blocks_delete(self) -> None:
        """DELETE statements should be blocked."""
        with pytest.raises(ValueError, match="prohibited keyword"):
            await cypher_query("MATCH (n) DELETE n")

    async def test_blocks_merge(self) -> None:
        """MERGE statements should be blocked."""
        with pytest.raises(ValueError, match="prohibited keyword"):
            await cypher_query("MERGE (n:Node {name: 'test'})")

    async def test_blocks_set(self) -> None:
        """SET statements should be blocked."""
        with pytest.raises(ValueError, match="prohibited keyword"):
            await cypher_query("MATCH (n) SET n.name = 'new'")

    async def test_blocks_drop(self) -> None:
        """DROP statements should be blocked."""
        with pytest.raises(ValueError, match="prohibited keyword"):
            await cypher_query("DROP TABLE Node")

    async def test_blocks_remove(self) -> None:
        """REMOVE statements should be blocked."""
        with pytest.raises(ValueError, match="prohibited keyword"):
            await cypher_query("MATCH (n) REMOVE n.name")

    async def test_allows_read_query_no_repo(self) -> None:
        """Read-only query with no repo_path should return empty result."""
        result = await cypher_query("MATCH (n) RETURN n LIMIT 10")

        assert result.columns == []
        assert result.rows == []
        assert result.total_rows == 0

    async def test_case_insensitive_blocking(self) -> None:
        """Write keyword detection should be case-insensitive."""
        with pytest.raises(ValueError, match="prohibited keyword"):
            await cypher_query("match (n) create (m)")


class TestQueryTool:
    """Tests for query tool."""

    async def test_no_repo_returns_empty(self) -> None:
        """Query with no repo_path should return empty results."""
        from ai_codebase_intelligence._tools.codebase_tools import query

        result = await query("test_query")

        assert result.query == "test_query"
        assert result.results == []
        assert result.total_matches == 0


class TestContextTool:
    """Tests for context tool."""

    async def test_no_repo_returns_unknown(self) -> None:
        """Context with no repo_path should return unknown kind."""
        from ai_codebase_intelligence._tools.codebase_tools import context

        result = await context("my_func")

        assert result.name == "my_func"
        assert result.kind == "unknown"


class TestImpactTool:
    """Tests for impact tool."""

    async def test_no_repo_returns_empty(self) -> None:
        """Impact with no repo_path should return empty result."""
        from ai_codebase_intelligence._tools.codebase_tools import impact

        result = await impact("my_func")

        assert result.target == "my_func"
        assert result.symbols == []
        assert result.total_impacted == 0
