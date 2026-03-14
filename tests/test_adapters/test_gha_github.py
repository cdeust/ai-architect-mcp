"""Tests for GitHub Actions GitHub API adapter."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ai_architect_mcp._adapters.github_actions_github import (
    GitHubActionsGitHub,
    GitHubAPIError,
)


class TestGitHubActionsGitHub:
    """Tests for GitHubActionsGitHub adapter."""

    def test_init_defaults(self) -> None:
        adapter = GitHubActionsGitHub(repo="owner/repo", token="test-token")
        assert adapter._repo == "owner/repo"
        assert adapter._token == "test-token"

    def test_init_from_env(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("GITHUB_TOKEN", "env-token")
        adapter = GitHubActionsGitHub(repo="owner/repo")
        assert adapter._token == "env-token"

    @pytest.mark.asyncio
    async def test_create_pull_request(self) -> None:
        adapter = GitHubActionsGitHub(
            repo="owner/repo", token="test-token",
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "number": 42,
            "html_url": "https://github.com/owner/repo/pull/42",
            "state": "open",
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = await adapter.create_pull_request(
                title="Test PR",
                body="Test body",
                head="feature",
                base="main",
            )

        assert result["number"] == 42
        assert result["state"] == "open"

    @pytest.mark.asyncio
    async def test_fetch_tree(self) -> None:
        adapter = GitHubActionsGitHub(
            repo="owner/repo", token="test-token",
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "tree": [
                {"path": "src/main.swift", "type": "blob", "sha": "abc"},
                {"path": "README.md", "type": "blob", "sha": "def"},
            ],
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = await adapter.fetch_tree()

        assert len(result) == 2
        assert result[0]["path"] == "src/main.swift"

    @pytest.mark.asyncio
    async def test_fetch_file(self) -> None:
        import base64

        adapter = GitHubActionsGitHub(
            repo="owner/repo", token="test-token",
        )

        encoded = base64.b64encode(b"let x = 1").decode()
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "content": encoded,
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = await adapter.fetch_file("main.swift")

        assert result == "let x = 1"

    @pytest.mark.asyncio
    async def test_batch_fetch(self) -> None:
        adapter = GitHubActionsGitHub(
            repo="owner/repo", token="test-token",
        )

        async def fake_fetch(path: str, ref: str = "HEAD") -> str:
            return f"content of {path}"

        with patch.object(adapter, "fetch_file", side_effect=fake_fetch):
            result = await adapter.batch_fetch(["a.swift", "b.swift"])

        assert result["a.swift"] == "content of a.swift"
        assert result["b.swift"] == "content of b.swift"


class TestGitHubAPIError:
    """Tests for GitHubAPIError."""

    def test_error_message(self) -> None:
        err = GitHubAPIError(404, "Not Found")
        assert "404" in str(err)
        assert "Not Found" in str(err)
