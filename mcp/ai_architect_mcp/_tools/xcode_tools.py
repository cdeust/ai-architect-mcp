"""Xcode tools — build and test via port interfaces.

Exposes 2 MCP tools: ai_architect_run_build, ai_architect_run_tests.
Supports both Xcode projects (via mcpbridge or xcodebuild) and
Swift Package Manager packages (via swift build/test).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp._app import mcp
from ai_architect_mcp._observability.instrumentation import observe_tool_call

_root: CompositionRoot | None = None


def _get_root() -> CompositionRoot:
    """Get or create the composition root."""
    global _root
    if _root is None:
        _root = CompositionRoot()
    return _root


def _is_spm_package(project_path: str) -> bool:
    """Check if the path is a Swift Package Manager package."""
    return (Path(project_path) / "Package.swift").exists()


async def _swift_build(
    project_path: str,
    scheme: str,
    configuration: str,
) -> dict[str, Any]:
    """Build an SPM package using swift build."""
    args = ["swift", "build", "--package-path", project_path]
    if scheme != "all":
        args.extend(["--target", scheme])
    if configuration.lower() == "release":
        args.extend(["-c", "release"])

    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    output = (stdout.decode() + stderr.decode()).strip()
    success = process.returncode == 0

    return {
        "success": success,
        "scheme": scheme,
        "configuration": configuration,
        "output": output[:500],
        "warnings": [],
        "errors": [] if success else [output[:500]],
    }


async def _swift_test(
    project_path: str,
    scheme: str,
    test_plan: str | None,
) -> dict[str, Any]:
    """Run tests for an SPM package using swift test."""
    args = ["swift", "test", "--package-path", project_path]
    if test_plan:
        args.extend(["--filter", test_plan])

    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    output = (stdout.decode() + stderr.decode()).strip()
    success = process.returncode == 0

    passed = output.count("passed")
    failed_count = output.count("failed")

    return {
        "success": success,
        "scheme": scheme,
        "test_plan": test_plan,
        "output": output[:500],
        "passed": passed,
        "failed": failed_count if not success else 0,
        "failures": [] if success else [output[:500]],
    }


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_run_build(
    scheme: str,
    configuration: str = "Debug",
    project_path: str = "",
) -> dict[str, Any]:
    """Build a Swift package or Xcode scheme.

    For SPM packages (directory with Package.swift), uses swift build.
    For Xcode projects, uses mcpbridge or xcodebuild CLI.

    Args:
        scheme: Target or scheme name. Use 'all' for full SPM build.
        configuration: Build configuration (Debug/Release).
        project_path: Path to the project. Defaults to app/ in repo.

    Returns:
        Build result dict with success, output, errors.
    """
    if not project_path:
        project_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "app")
    project_path = str(Path(project_path).resolve())

    if _is_spm_package(project_path):
        return await _swift_build(project_path, scheme, configuration)

    xcode = _get_root().create_xcode()
    return await xcode.build(scheme, configuration)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_run_tests(
    scheme: str,
    test_plan: str | None = None,
    project_path: str = "",
) -> dict[str, Any]:
    """Run tests for a Swift package or Xcode scheme.

    For SPM packages (directory with Package.swift), uses swift test.
    For Xcode projects, uses mcpbridge or xcodebuild CLI.

    Args:
        scheme: Test target or scheme name.
        test_plan: Optional test plan or filter.
        project_path: Path to the project. Defaults to app/ in repo.

    Returns:
        Test result dict with success, passed, failed counts.
    """
    if not project_path:
        project_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "app")
    project_path = str(Path(project_path).resolve())

    if _is_spm_package(project_path):
        return await _swift_test(project_path, scheme, test_plan)

    xcode = _get_root().create_xcode()
    return await xcode.run_tests(scheme, test_plan)
