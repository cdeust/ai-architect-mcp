"""Tests for XcodeMCPBridgeAdapter — mocked MCP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ai_architect_mcp._adapters.xcode_mcpbridge_adapter import (
    MCPBRIDGE_TOOL_BUILD,
    MCPBRIDGE_TOOL_GREP,
    MCPBRIDGE_TOOL_READ,
    MCPBRIDGE_TOOL_RENDER_PREVIEW,
    MCPBRIDGE_TOOL_RUN_ALL_TESTS,
    MCPBRIDGE_TOOL_RUN_SOME_TESTS,
    MCPBRIDGE_TOOL_WRITE,
    XcodeMCPBridgeAdapter,
)


class TestXcodeMCPBridgeAdapter:
    """Test XcodeMCPBridgeAdapter with mocked _call_tool."""

    @pytest.fixture
    def adapter(self) -> XcodeMCPBridgeAdapter:
        """Create adapter with mocked connection."""
        return XcodeMCPBridgeAdapter(xcrun_path="xcrun")

    @pytest.mark.asyncio
    async def test_build_success(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw_response = {
            "succeeded": True,
            "output": "Build complete!",
            "warnings": ["unused variable"],
            "errors": [],
        }
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value=raw_response):
            result = await adapter.build("MyApp", "Release")

        assert result["success"] is True
        assert result["scheme"] == "MyApp"
        assert result["configuration"] == "Release"
        assert result["warnings"] == ["unused variable"]

    @pytest.mark.asyncio
    async def test_build_failure(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw_response = {
            "succeeded": False,
            "output": "error: missing import",
            "warnings": [],
            "errors": ["missing import"],
        }
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value=raw_response):
            result = await adapter.build("MyApp")

        assert result["success"] is False
        assert result["errors"] == ["missing import"]

    @pytest.mark.asyncio
    async def test_run_tests_all(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw_response = {
            "passed": 42,
            "failed": 0,
            "output": "All tests passed",
            "failures": [],
        }
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value=raw_response) as mock:
            result = await adapter.run_tests("MyApp")

        mock.assert_called_once_with(
            MCPBRIDGE_TOOL_RUN_ALL_TESTS, {"scheme": "MyApp"}
        )
        assert result["success"] is True
        assert result["passed"] == 42
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_run_tests_with_plan(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw_response = {
            "passed": 10,
            "failed": 2,
            "output": "2 failures",
            "failures": ["testA", "testB"],
        }
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value=raw_response) as mock:
            result = await adapter.run_tests("MyApp", test_plan="UnitTests")

        mock.assert_called_once_with(
            MCPBRIDGE_TOOL_RUN_SOME_TESTS,
            {"scheme": "MyApp", "testPlan": "UnitTests"},
        )
        assert result["success"] is False
        assert result["failed"] == 2
        assert result["failures"] == ["testA", "testB"]

    @pytest.mark.asyncio
    async def test_preview(self, adapter: XcodeMCPBridgeAdapter) -> None:
        import base64

        png_bytes = b"\x89PNG\r\n\x1a\n"
        raw_response = {
            "imageData": base64.b64encode(png_bytes).decode(),
        }
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value=raw_response):
            result = await adapter.preview("ContentView")

        assert result == png_bytes

    @pytest.mark.asyncio
    async def test_read_via_bridge(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw_response = {"content": "let x = 1"}
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value=raw_response) as mock:
            result = await adapter.read("Sources/main.swift")

        mock.assert_called_once_with(
            MCPBRIDGE_TOOL_READ, {"path": "Sources/main.swift"}
        )
        assert result == "let x = 1"

    @pytest.mark.asyncio
    async def test_write_via_bridge(self, adapter: XcodeMCPBridgeAdapter) -> None:
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value={}) as mock:
            await adapter.write("out.swift", "let y = 2")

        mock.assert_called_once_with(
            MCPBRIDGE_TOOL_WRITE,
            {"path": "out.swift", "content": "let y = 2"},
        )

    @pytest.mark.asyncio
    async def test_grep_via_bridge(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw_response = {
            "matches": [
                {"file": "a.swift", "line": 1, "content": "let foo = 1"},
            ],
        }
        with patch.object(adapter, "_call_tool", new_callable=AsyncMock, return_value=raw_response) as mock:
            result = await adapter.grep("foo", path="Sources")

        mock.assert_called_once_with(
            MCPBRIDGE_TOOL_GREP,
            {"pattern": "foo", "path": "Sources"},
        )
        assert len(result) == 1
        assert result[0]["file"] == "a.swift"

    @pytest.mark.asyncio
    async def test_extract_data_string_json(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw = '{"success": true, "output": "done"}'
        data = adapter._extract_data(raw)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_extract_data_plain_string(self, adapter: XcodeMCPBridgeAdapter) -> None:
        raw = "not json"
        data = adapter._extract_data(raw)
        assert data["output"] == "not json"

    @pytest.mark.asyncio
    async def test_extract_data_content_block(self, adapter: XcodeMCPBridgeAdapter) -> None:
        """Content blocks (list with .text attr) are parsed."""

        class FakeContent:
            text = '{"key": "value"}'

        data = adapter._extract_data([FakeContent()])
        assert data["key"] == "value"
