"""Tests for GitHub Actions Xcode adapter."""

from __future__ import annotations

import pytest

from ai_architect_mcp._adapters.github_actions_xcode import (
    GitHubActionsXcode,
    NotSupportedError,
)


class TestGitHubActionsXcode:
    """Tests for GitHubActionsXcode — all methods raise NotSupportedError."""

    @pytest.mark.asyncio
    async def test_build_raises(self) -> None:
        adapter = GitHubActionsXcode()
        with pytest.raises(NotSupportedError, match="not available"):
            await adapter.build("MyScheme")

    @pytest.mark.asyncio
    async def test_run_tests_raises(self) -> None:
        adapter = GitHubActionsXcode()
        with pytest.raises(NotSupportedError, match="not available"):
            await adapter.run_tests("MyScheme")

    @pytest.mark.asyncio
    async def test_preview_raises(self) -> None:
        adapter = GitHubActionsXcode()
        with pytest.raises(NotSupportedError, match="not available"):
            await adapter.preview("MyView")

    @pytest.mark.asyncio
    async def test_read_raises(self) -> None:
        adapter = GitHubActionsXcode()
        with pytest.raises(NotSupportedError, match="not available"):
            await adapter.read("file.swift")

    @pytest.mark.asyncio
    async def test_write_raises(self) -> None:
        adapter = GitHubActionsXcode()
        with pytest.raises(NotSupportedError, match="not available"):
            await adapter.write("file.swift", "content")

    @pytest.mark.asyncio
    async def test_grep_raises(self) -> None:
        adapter = GitHubActionsXcode()
        with pytest.raises(NotSupportedError, match="not available"):
            await adapter.grep("pattern")
