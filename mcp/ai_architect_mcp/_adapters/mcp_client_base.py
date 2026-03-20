"""Base class for MCP-client-backed adapters.

Provides lazy connection management and tool invocation over stdio transport.
Concrete adapters (mcpbridge, SwiftData MCP) inherit from this base and
map port methods to specific MCP tool calls.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS: float = 30.0


class MCPClientError(Exception):
    """Raised when an MCP tool call fails.

    Attributes:
        tool_name: The MCP tool that was called.
        detail: Error detail from the server.
    """

    def __init__(self, tool_name: str, detail: str) -> None:
        self.tool_name = tool_name
        self.detail = detail
        super().__init__(
            f"MCP tool '{tool_name}' failed: {detail}"
        )


class MCPClientBase:
    """Base class for adapters that delegate to an external MCP server.

    Manages a single stdio subprocess connection with lazy initialisation.
    Subclasses call ``_call_tool`` to invoke named tools on the remote server.

    Args:
        command: Executable to launch (e.g. ``xcrun``, path to Swift binary).
        args: Arguments passed to the command.
        timeout: Per-call timeout in seconds.
    """

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._command = command
        self._args = args or []
        self._timeout = timeout
        self._client: Client | None = None
        self._lock = asyncio.Lock()

    async def _ensure_connected(self) -> Client:
        """Return the active client, connecting lazily on first call.

        Returns:
            Connected ``fastmcp.Client`` instance.
        """
        if self._client is not None:
            return self._client

        async with self._lock:
            if self._client is not None:
                return self._client

            transport = StdioTransport(
                command=self._command,
                args=self._args,
            )
            self._client = Client(transport=transport)
            await self._client.__aenter__()
            logger.info(
                "MCP client connected: %s %s",
                self._command,
                " ".join(self._args),
            )

        return self._client

    async def _call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> object:
        """Invoke a tool on the remote MCP server.

        Args:
            tool_name: Name of the MCP tool to call.
            arguments: Tool arguments as a dictionary.

        Returns:
            The tool's result payload (pass to extract_mcp_data to parse).

        Raises:
            MCPClientError: If the call fails or times out.
        """
        client = await self._ensure_connected()
        try:
            result = await asyncio.wait_for(
                client.call_tool(tool_name, arguments or {}),
                timeout=self._timeout,
            )
            return result
        except asyncio.TimeoutError as exc:
            raise MCPClientError(
                tool_name,
                f"timed out after {self._timeout}s",
            ) from exc
        except Exception as exc:
            raise MCPClientError(
                tool_name,
                str(exc),
            ) from exc

    async def close(self) -> None:
        """Terminate the MCP subprocess and release resources."""
        if self._client is not None:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:
                logger.warning("Error closing MCP client", exc_info=True)
            finally:
                self._client = None
