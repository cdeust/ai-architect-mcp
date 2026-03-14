"""Tests for GitHub adapter — mocked subprocess."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ai_architect_mcp._adapters.github_adapter import GitHubAdapter, GitHubOperationError


class TestGitHubAdapter:
    """Test GitHubAdapter with mocked subprocess."""

    @pytest.mark.asyncio
    async def test_create_pr(self) -> None:
        adapter = GitHubAdapter()
        pr_data = {"number": 42, "url": "https://github.com/test/pr/42", "state": "open"}
        with patch("ai_architect_mcp._adapters.github_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (json.dumps(pr_data).encode(), b"")
            process.returncode = 0
            mock.return_value = process

            result = await adapter.create_pull_request("Test PR", "Body", "feature")
            assert result["number"] == 42

    @pytest.mark.asyncio
    async def test_fetch_tree(self) -> None:
        adapter = GitHubAdapter()
        tree_data = {
            "tree": [
                {"path": "src/main.swift", "type": "blob", "sha": "abc123"},
                {"path": "README.md", "type": "blob", "sha": "def456"},
            ],
        }
        with patch("ai_architect_mcp._adapters.github_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (json.dumps(tree_data).encode(), b"")
            process.returncode = 0
            mock.return_value = process

            result = await adapter.fetch_tree()
            assert len(result) == 2
            assert result[0]["path"] == "src/main.swift"

    @pytest.mark.asyncio
    async def test_fetch_file(self) -> None:
        adapter = GitHubAdapter()
        import base64
        content = base64.b64encode(b"let x = 1").decode()
        with patch("ai_architect_mcp._adapters.github_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (content.encode() + b"\n", b"")
            process.returncode = 0
            mock.return_value = process

            result = await adapter.fetch_file("main.swift")
            assert result == "let x = 1"

    @pytest.mark.asyncio
    async def test_batch_fetch(self) -> None:
        adapter = GitHubAdapter()
        import base64

        async def fake_fetch(path: str, ref: str = "HEAD") -> str:
            return f"content of {path}"

        with patch.object(adapter, "fetch_file", side_effect=fake_fetch):
            result = await adapter.batch_fetch(["a.swift", "b.swift"])
            assert result["a.swift"] == "content of a.swift"
            assert result["b.swift"] == "content of b.swift"

    @pytest.mark.asyncio
    async def test_error_raised(self) -> None:
        adapter = GitHubAdapter()
        with patch("ai_architect_mcp._adapters.github_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"", b"not authenticated")
            process.returncode = 1
            mock.return_value = process

            with pytest.raises(GitHubOperationError):
                await adapter.fetch_tree()
