"""Tests for MCPClientBase — mocked fastmcp.Client."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_architect_mcp._adapters.mcp_client_base import (
    MCPClientBase,
    MCPClientError,
)


class TestMCPClientBase:
    """Test MCPClientBase connection and tool calling."""

    @pytest.mark.asyncio
    async def test_call_tool_success(self) -> None:
        """Successful tool call returns parsed result."""
        base = MCPClientBase(command="echo", args=["hello"])

        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value={"status": "ok"})
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ai_architect_mcp._adapters.mcp_client_base.Client",
            return_value=mock_client,
        ):
            result = await base._call_tool("my_tool", {"key": "val"})

        assert result == {"status": "ok"}
        mock_client.call_tool.assert_called_once_with("my_tool", {"key": "val"})

    @pytest.mark.asyncio
    async def test_call_tool_timeout(self) -> None:
        """Tool call that exceeds timeout raises MCPClientError."""
        base = MCPClientBase(command="echo", timeout=0.01)

        mock_client = AsyncMock()

        async def slow_call(name: str, args: dict) -> dict:  # noqa: ARG001
            await asyncio.sleep(1.0)
            return {}

        mock_client.call_tool = slow_call
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ai_architect_mcp._adapters.mcp_client_base.Client",
            return_value=mock_client,
        ):
            with pytest.raises(MCPClientError, match="timed out"):
                await base._call_tool("slow_tool")

    @pytest.mark.asyncio
    async def test_call_tool_error_wrapping(self) -> None:
        """Exceptions from the client are wrapped in MCPClientError."""
        base = MCPClientBase(command="echo")

        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(
            side_effect=RuntimeError("connection lost")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ai_architect_mcp._adapters.mcp_client_base.Client",
            return_value=mock_client,
        ):
            with pytest.raises(MCPClientError, match="connection lost"):
                await base._call_tool("broken_tool")

    @pytest.mark.asyncio
    async def test_lazy_connection(self) -> None:
        """Client connects lazily on first call, reuses on second."""
        base = MCPClientBase(command="echo")

        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value="ok")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ai_architect_mcp._adapters.mcp_client_base.Client",
            return_value=mock_client,
        ) as mock_cls:
            await base._call_tool("tool_a")
            await base._call_tool("tool_b")

        # Client constructor called only once (lazy init)
        assert mock_cls.call_count == 1

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Close terminates the subprocess."""
        base = MCPClientBase(command="echo")

        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value="ok")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ai_architect_mcp._adapters.mcp_client_base.Client",
            return_value=mock_client,
        ):
            await base._call_tool("init_tool")
            await base.close()

        mock_client.__aexit__.assert_called_once()
        assert base._client is None

    @pytest.mark.asyncio
    async def test_close_without_connect(self) -> None:
        """Close before any connection is a no-op."""
        base = MCPClientBase(command="echo")
        await base.close()
        assert base._client is None

    @pytest.mark.asyncio
    async def test_default_empty_arguments(self) -> None:
        """Calling with no arguments passes empty dict."""
        base = MCPClientBase(command="echo")

        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value="ok")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "ai_architect_mcp._adapters.mcp_client_base.Client",
            return_value=mock_client,
        ):
            await base._call_tool("tool_no_args")

        mock_client.call_tool.assert_called_once_with("tool_no_args", {})
