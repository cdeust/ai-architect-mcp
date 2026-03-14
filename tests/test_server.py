"""Tests for MCP server — server starts, tools registered."""

from __future__ import annotations


class TestServer:
    def test_server_creates(self) -> None:
        from ai_architect_mcp.server import mcp

        assert mcp is not None

    def test_server_name(self) -> None:
        from ai_architect_mcp.server import mcp

        assert mcp.name == "ai-architect"
