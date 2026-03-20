"""Xcode MCP bridge adapter — XcodeOperationsPort via xcrun mcpbridge.

Replaces the xcodebuild CLI wrapper with Apple's native MCP bridge
(Xcode 26.3+). Falls back handled at the composition root level —
this adapter assumes mcpbridge is available.
"""

from __future__ import annotations

import logging
from typing import Any

from ai_architect_mcp._adapters.mcp_client_base import MCPClientBase, MCPClientError
from ai_architect_mcp._adapters.mcp_result_parser import extract_mcp_data
from ai_architect_mcp._adapters.ports import XcodeOperationsPort

logger = logging.getLogger(__name__)

MCPBRIDGE_TOOL_BUILD: str = "BuildProject"
MCPBRIDGE_TOOL_BUILD_LOG: str = "GetBuildLog"
MCPBRIDGE_TOOL_RUN_ALL_TESTS: str = "RunAllTests"
MCPBRIDGE_TOOL_RUN_SOME_TESTS: str = "RunSomeTests"
MCPBRIDGE_TOOL_RENDER_PREVIEW: str = "RenderPreview"
MCPBRIDGE_TOOL_READ: str = "XcodeRead"
MCPBRIDGE_TOOL_WRITE: str = "XcodeWrite"
MCPBRIDGE_TOOL_GREP: str = "XcodeGrep"


class XcodeMCPBridgeAdapter(XcodeOperationsPort, MCPClientBase):
    """Xcode adapter using xcrun mcpbridge over stdio.

    Delegates build, test, preview, read, write, and grep operations
    to the native MCP tools exposed by Xcode's built-in MCP bridge.

    Auto-discovers the tabIdentifier from the first error response
    when Xcode has a project open.

    Args:
        xcrun_path: Path to the xcrun binary.
        tab_identifier: Optional explicit tab identifier.
    """

    def __init__(
        self,
        xcrun_path: str = "xcrun",
        tab_identifier: str | None = None,
    ) -> None:
        """Initialize the mcpbridge adapter.

        Args:
            xcrun_path: Path to the xcrun executable.
            tab_identifier: Explicit Xcode window tab ID.
        """
        MCPClientBase.__init__(
            self,
            command=xcrun_path,
            args=["mcpbridge"],
            timeout=120.0,
        )
        self._tab_identifier: str | None = tab_identifier
        self._tab_discovered = tab_identifier is not None

    async def _discover_tab(self) -> str | None:
        """Discover the active Xcode tab identifier.

        Calls a lightweight tool to trigger the tabIdentifier error,
        then parses the available tab from the error message.

        Returns:
            The discovered tabIdentifier, or None.
        """
        if self._tab_discovered:
            return self._tab_identifier
        self._tab_discovered = True
        try:
            await self._call_tool(
                MCPBRIDGE_TOOL_BUILD_LOG, {},
            )
        except MCPClientError as exc:
            import re
            match = re.search(r"tabIdentifier:\s*(\S+)", exc.detail)
            if match:
                self._tab_identifier = match.group(1).rstrip(",")
                logger.info(
                    "Discovered Xcode tabIdentifier: %s",
                    self._tab_identifier,
                )
        return self._tab_identifier

    async def _call_with_tab(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> object:
        """Call a mcpbridge tool, injecting tabIdentifier.

        Args:
            tool_name: MCP tool name.
            arguments: Tool arguments.

        Returns:
            Tool result.
        """
        tab = await self._discover_tab()
        if tab and "tabIdentifier" not in arguments:
            arguments["tabIdentifier"] = tab
        return await self._call_tool(tool_name, arguments)

    async def build(
        self, scheme: str, configuration: str = "Debug"
    ) -> dict[str, Any]:
        """Build an Xcode scheme via mcpbridge.

        Args:
            scheme: The Xcode scheme to build.
            configuration: Build configuration (Debug/Release).

        Returns:
            Build result with success status, warnings, errors.
        """
        result = await self._call_with_tab(
            MCPBRIDGE_TOOL_BUILD,
            {"scheme": scheme, "configuration": configuration},
        )
        return self._parse_build_result(result, scheme, configuration)

    async def run_tests(
        self, scheme: str, test_plan: str | None = None
    ) -> dict[str, Any]:
        """Run tests via mcpbridge.

        Args:
            scheme: The Xcode scheme to test.
            test_plan: Optional test plan name. Runs all if None.

        Returns:
            Test results with pass/fail counts and failure details.
        """
        if test_plan:
            result = await self._call_with_tab(
                MCPBRIDGE_TOOL_RUN_SOME_TESTS,
                {"scheme": scheme, "testPlan": test_plan},
            )
        else:
            result = await self._call_with_tab(
                MCPBRIDGE_TOOL_RUN_ALL_TESTS,
                {"scheme": scheme},
            )
        return self._parse_test_result(result, scheme, test_plan)

    async def preview(self, view_name: str) -> bytes:
        """Capture a SwiftUI preview snapshot via mcpbridge.

        Args:
            view_name: The SwiftUI view to preview.

        Returns:
            PNG image bytes of the rendered preview.
        """
        result = await self._call_with_tab(
            MCPBRIDGE_TOOL_RENDER_PREVIEW,
            {"viewName": view_name},
        )
        return self._parse_preview_result(result)

    async def read(self, path: str) -> str:
        """Read a file via XcodeRead bridge tool.

        Args:
            path: Path to the file to read.

        Returns:
            File contents as a string.
        """
        result = await self._call_with_tab(
            MCPBRIDGE_TOOL_READ, {"path": path},
        )
        data = extract_mcp_data(result)
        return str(data.get("content", data.get("output", "")))

    async def write(self, path: str, content: str) -> None:
        """Write a file via XcodeWrite bridge tool.

        Args:
            path: Path to write to.
            content: Content to write.
        """
        await self._call_with_tab(
            MCPBRIDGE_TOOL_WRITE,
            {"path": path, "content": content},
        )

    async def grep(
        self, pattern: str, path: str | None = None
    ) -> list[dict[str, Any]]:
        """Search codebase via XcodeGrep bridge tool.

        Args:
            pattern: Search pattern.
            path: Optional path to restrict search.

        Returns:
            List of match results with file, line, and content.
        """
        params: dict[str, str] = {"pattern": pattern}
        if path is not None:
            params["path"] = path
        result = await self._call_with_tab(MCPBRIDGE_TOOL_GREP, params)
        data = extract_mcp_data(result)
        return list(data.get("matches", []))

    def _parse_build_result(
        self,
        raw: Any,
        scheme: str,
        configuration: str,
    ) -> dict[str, Any]:
        """Parse mcpbridge build response into standard format.

        Args:
            raw: Raw tool result from mcpbridge.
            scheme: Scheme that was built.
            configuration: Build configuration used.

        Returns:
            Normalized build result dictionary.
        """
        data = extract_mcp_data(raw)
        build_result = data.get("buildResult", "")
        success = data.get(
            "succeeded",
            data.get("success", "successfully" in str(build_result).lower()),
        )
        errors = list(data.get("errors", []))
        if errors:
            success = False
        return {
            "success": bool(success),
            "scheme": scheme,
            "configuration": configuration,
            "output": str(build_result or data.get("output", ""))[:500],
            "warnings": list(data.get("warnings", [])),
            "errors": errors,
        }

    def _parse_test_result(
        self,
        raw: Any,
        scheme: str,
        test_plan: str | None,
    ) -> dict[str, Any]:
        """Parse mcpbridge test response into standard format.

        Args:
            raw: Raw tool result from mcpbridge.
            scheme: Scheme that was tested.
            test_plan: Test plan used (or None).

        Returns:
            Normalized test result dictionary.
        """
        data = extract_mcp_data(raw)
        passed = int(data.get("passed", 0))
        failed = int(data.get("failed", 0))
        return {
            "success": failed == 0,
            "scheme": scheme,
            "test_plan": test_plan,
            "output": str(data.get("output", ""))[:500],
            "passed": passed,
            "failed": failed,
            "failures": list(data.get("failures", [])),
        }

    def _parse_preview_result(self, raw: Any) -> bytes:
        """Parse mcpbridge preview response into PNG bytes.

        Args:
            raw: Raw tool result from mcpbridge.

        Returns:
            PNG image bytes.
        """
        data = extract_mcp_data(raw)
        image_data = data.get("imageData", b"")
        if isinstance(image_data, str):
            import base64
            return base64.b64decode(image_data)
        if isinstance(image_data, bytes):
            return image_data
        return str(image_data).encode()

