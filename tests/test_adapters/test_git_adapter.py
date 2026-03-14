"""Tests for git adapter — mocked subprocess."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ai_architect_mcp._adapters.git_adapter import GitAdapter, GitOperationError


class TestGitAdapter:
    """Test GitAdapter with mocked subprocess."""

    @pytest.mark.asyncio
    async def test_create_branch(self) -> None:
        adapter = GitAdapter()
        with patch("ai_architect_mcp._adapters.git_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"", b"")
            process.returncode = 0
            mock.return_value = process

            result = await adapter.create_branch("feature/test")
            assert result == "refs/heads/feature/test"

    @pytest.mark.asyncio
    async def test_commit(self) -> None:
        adapter = GitAdapter()
        with patch("ai_architect_mcp._adapters.git_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"abc123\n", b"")
            process.returncode = 0
            mock.return_value = process

            sha = await adapter.commit("test commit", ["file.py"])
            assert sha == "abc123"

    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        adapter = GitAdapter()
        with patch("ai_architect_mcp._adapters.git_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"", b"")
            process.returncode = 0
            mock.return_value = process

            await adapter.reset("abc123")
            mock.assert_called()

    @pytest.mark.asyncio
    async def test_reset_branch(self) -> None:
        adapter = GitAdapter()
        with patch("ai_architect_mcp._adapters.git_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"", b"")
            process.returncode = 0
            mock.return_value = process

            await adapter.reset_branch("feature", "abc123")
            mock.assert_called()

    @pytest.mark.asyncio
    async def test_error_raised(self) -> None:
        adapter = GitAdapter()
        with patch("ai_architect_mcp._adapters.git_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"", b"fatal: not a repo")
            process.returncode = 128
            mock.return_value = process

            with pytest.raises(GitOperationError):
                await adapter.diff("main", "feature")
