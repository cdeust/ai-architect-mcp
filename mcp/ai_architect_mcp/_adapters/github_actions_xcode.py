"""GitHub Actions Xcode adapter — raises NotSupportedError.

Xcode operations are not available in GitHub Actions CI environment.
All methods raise NotSupportedError with a descriptive message.
"""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._adapters.ports import XcodeOperationsPort

NOT_SUPPORTED_MSG = (
    "Xcode operations are not available in GitHub Actions — "
    "use a macOS self-hosted runner or skip Xcode-dependent stages"
)


class NotSupportedError(Exception):
    """Raised when an operation is not supported in the current environment."""


class GitHubActionsXcode(XcodeOperationsPort):
    """Xcode adapter that always raises NotSupportedError.

    GitHub Actions Linux runners do not have Xcode.
    All methods raise NotSupportedError immediately.
    """

    async def build(
        self, scheme: str, configuration: str = "Debug",
    ) -> dict[str, Any]:
        """Not supported in GitHub Actions.

        Raises:
            NotSupportedError: Always.
        """
        raise NotSupportedError(NOT_SUPPORTED_MSG)

    async def run_tests(
        self, scheme: str, test_plan: str | None = None,
    ) -> dict[str, Any]:
        """Not supported in GitHub Actions.

        Raises:
            NotSupportedError: Always.
        """
        raise NotSupportedError(NOT_SUPPORTED_MSG)

    async def preview(self, view_name: str) -> bytes:
        """Not supported in GitHub Actions.

        Raises:
            NotSupportedError: Always.
        """
        raise NotSupportedError(NOT_SUPPORTED_MSG)

    async def read(self, path: str) -> str:
        """Not supported in GitHub Actions.

        Raises:
            NotSupportedError: Always.
        """
        raise NotSupportedError(NOT_SUPPORTED_MSG)

    async def write(self, path: str, content: str) -> None:
        """Not supported in GitHub Actions.

        Raises:
            NotSupportedError: Always.
        """
        raise NotSupportedError(NOT_SUPPORTED_MSG)

    async def grep(
        self, pattern: str, path: str | None = None,
    ) -> list[dict[str, Any]]:
        """Not supported in GitHub Actions.

        Raises:
            NotSupportedError: Always.
        """
        raise NotSupportedError(NOT_SUPPORTED_MSG)
