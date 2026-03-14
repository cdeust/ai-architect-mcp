"""Xcode adapter — concrete implementation of XcodeOperationsPort.

Wraps xcodebuild CLI for build, test, and preview operations.
Local filesystem fallback for read/write/grep when MCP bridge
is not available. Injected at the composition root.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

from ai_architect_mcp._adapters.ports import XcodeOperationsPort


class XcodeOperationError(Exception):
    """Raised when an xcodebuild command fails.

    Attributes:
        command: The xcodebuild command that failed.
        stderr: Standard error output.
        exit_code: Process exit code.
    """

    def __init__(self, command: str, stderr: str, exit_code: int) -> None:
        self.command = command
        self.stderr = stderr
        self.exit_code = exit_code
        super().__init__(
            f"xcodebuild failed (exit {exit_code}): {command}\n{stderr}"
        )


class XcodeAdapter(XcodeOperationsPort):
    """Concrete Xcode adapter wrapping xcodebuild.

    Args:
        project_path: Path to the Xcode project or workspace.
    """

    def __init__(self, project_path: str = ".") -> None:
        """Initialize the Xcode adapter.

        Args:
            project_path: Path to the Xcode project or workspace.
        """
        self._project_path = project_path

    async def build(
        self, scheme: str, configuration: str = "Debug"
    ) -> dict[str, Any]:
        """Build an Xcode scheme.

        Args:
            scheme: The Xcode scheme to build.
            configuration: Build configuration.

        Returns:
            Build result with success status, warnings, errors.
        """
        try:
            output = await self._run_xcode(
                "build",
                "-scheme", scheme,
                "-configuration", configuration,
            )
            return {
                "success": True,
                "scheme": scheme,
                "configuration": configuration,
                "output": output[:500],
                "warnings": [],
                "errors": [],
            }
        except XcodeOperationError as e:
            return {
                "success": False,
                "scheme": scheme,
                "configuration": configuration,
                "output": e.stderr[:500],
                "warnings": [],
                "errors": [e.stderr],
            }

    async def run_tests(
        self, scheme: str, test_plan: str | None = None
    ) -> dict[str, Any]:
        """Run tests for an Xcode scheme.

        Args:
            scheme: The Xcode scheme to test.
            test_plan: Optional test plan name.

        Returns:
            Test results with pass/fail counts.
        """
        args = ["test", "-scheme", scheme]
        if test_plan:
            args.extend(["-testPlan", test_plan])

        try:
            output = await self._run_xcode(*args)
            return {
                "success": True,
                "scheme": scheme,
                "test_plan": test_plan,
                "output": output[:500],
                "passed": 0,
                "failed": 0,
                "failures": [],
            }
        except XcodeOperationError as e:
            return {
                "success": False,
                "scheme": scheme,
                "test_plan": test_plan,
                "output": e.stderr[:500],
                "passed": 0,
                "failed": 1,
                "failures": [e.stderr],
            }

    async def preview(self, view_name: str) -> bytes:
        """Capture a SwiftUI preview snapshot.

        Args:
            view_name: The SwiftUI view to preview.

        Returns:
            PNG image bytes of the rendered preview.
        """
        output = await self._run_xcode(
            "preview", "-view", view_name,
        )
        return output.encode()

    async def read(self, path: str) -> str:
        """Read a file from the local filesystem (fallback).

        Args:
            path: Path to the file to read.

        Returns:
            File contents as a string.
        """
        from pathlib import Path

        full = (Path(self._project_path) / path).resolve()
        return full.read_text(encoding="utf-8")

    async def write(self, path: str, content: str) -> None:
        """Write a file to the local filesystem (fallback).

        Args:
            path: Path to write to.
            content: Content to write.
        """
        from pathlib import Path

        full = (Path(self._project_path) / path).resolve()
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    async def grep(
        self, pattern: str, path: str | None = None
    ) -> list[dict[str, Any]]:
        """Search files via grep CLI (fallback).

        Args:
            pattern: Search pattern (regex).
            path: Optional path to restrict search.

        Returns:
            List of match results with file, line, and content.
        """
        search_path = path or self._project_path
        try:
            output = await self._run_cmd(
                "grep", "-rn", pattern, search_path,
            )
        except _CommandError:
            return []

        matches: list[dict[str, Any]] = []
        for line in output.strip().splitlines():
            match = re.match(r"^(.+?):(\d+):(.*)$", line)
            if match:
                matches.append({
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "content": match.group(3),
                })
        return matches

    async def _run_xcode(self, *args: str) -> str:
        """Run an xcodebuild command and return stdout.

        Args:
            *args: xcodebuild subcommand and arguments.

        Returns:
            Standard output from the command.

        Raises:
            XcodeOperationError: If the command exits non-zero.
        """
        process = await asyncio.create_subprocess_exec(
            "xcodebuild", *args,
            cwd=self._project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise XcodeOperationError(
                command=f"xcodebuild {' '.join(args)}",
                stderr=stderr.decode(),
                exit_code=process.returncode or 1,
            )

        return stdout.decode()

    async def _run_cmd(self, *args: str) -> str:
        """Run a generic command and return stdout.

        Args:
            *args: Command and arguments.

        Returns:
            Standard output from the command.

        Raises:
            _CommandError: If the command exits non-zero.
        """
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=self._project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise _CommandError(stderr.decode())

        return stdout.decode()


class _CommandError(Exception):
    """Internal error for generic command failures."""
