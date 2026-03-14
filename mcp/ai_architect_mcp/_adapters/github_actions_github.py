"""GitHub Actions GitHub adapter — REST API implementation.

Provides GitHubOperationsPort using the GitHub REST API via
urllib (no external HTTP library dependency in CI).
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any
from urllib.error import HTTPError

from ai_architect_mcp._adapters.ports import GitHubOperationsPort

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
TOKEN_ENV_VAR = "GITHUB_TOKEN"
ACCEPT_HEADER = "application/vnd.github+json"
API_VERSION_HEADER = "2022-11-28"


class GitHubAPIError(Exception):
    """Raised when a GitHub API call fails."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(
            f"GitHub API error (HTTP {status}): {message}"
        )


class GitHubActionsGitHub(GitHubOperationsPort):
    """GitHub API adapter for GitHub Actions.

    Args:
        repo: Repository in owner/repo format.
        token: GitHub token. Uses GITHUB_TOKEN env if None.
    """

    def __init__(
        self,
        repo: str | None = None,
        token: str | None = None,
    ) -> None:
        """Initialize the GitHub API adapter.

        Args:
            repo: GitHub repository identifier.
            token: Authentication token.
        """
        self._repo = repo or ""
        self._token = token or os.environ.get(TOKEN_ENV_VAR, "")

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GitHub API request.

        Args:
            method: HTTP method.
            path: API path (appended to /repos/{repo}).
            body: Request body for POST/PATCH.

        Returns:
            Response JSON as dictionary.

        Raises:
            GitHubAPIError: If the API returns an error.
        """
        url = f"{API_BASE}/repos/{self._repo}{path}"
        data = json.dumps(body).encode() if body else None

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", ACCEPT_HEADER)
        req.add_header("X-GitHub-Api-Version", API_VERSION_HEADER)
        if self._token:
            req.add_header("Authorization", f"Bearer {self._token}")
        if data:
            req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as exc:
            body_text = exc.read().decode() if exc.fp else ""
            raise GitHubAPIError(exc.code, body_text) from exc

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict[str, Any]:
        """Create a pull request.

        Args:
            title: PR title.
            body: PR body (markdown).
            head: Source branch.
            base: Target branch.

        Returns:
            PR metadata with number, url, state.
        """
        result = self._request("POST", "/pulls", {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        })
        return {
            "number": result.get("number"),
            "url": result.get("html_url", ""),
            "state": result.get("state", ""),
        }

    async def fetch_tree(
        self, path: str = "", ref: str = "HEAD"
    ) -> list[dict[str, str]]:
        """Fetch repository tree structure via REST API.

        Args:
            path: Subdirectory path. Empty for root.
            ref: Git ref to fetch from.

        Returns:
            List of tree entries with path, type, and sha.
        """
        result = self._request("GET", f"/git/trees/{ref}")
        tree = result.get("tree", [])
        if path:
            tree = [e for e in tree if e.get("path", "").startswith(path)]
        return [
            {
                "path": entry.get("path", ""),
                "type": entry.get("type", ""),
                "sha": entry.get("sha", ""),
            }
            for entry in tree
        ]

    async def fetch_file(self, path: str, ref: str = "HEAD") -> str:
        """Fetch a single file's contents from the remote.

        Args:
            path: File path within the repository.
            ref: Git ref to fetch from.

        Returns:
            File contents as a string.
        """
        result = self._request(
            "GET", f"/contents/{path}?ref={ref}",
        )
        import base64
        content = result.get("content", "")
        return base64.b64decode(content).decode("utf-8")

    async def batch_fetch(
        self, paths: list[str], ref: str = "HEAD"
    ) -> dict[str, str]:
        """Batch fetch multiple files from the remote.

        Args:
            paths: List of file paths to fetch.
            ref: Git ref to fetch from.

        Returns:
            Mapping of path to file contents.
        """
        results: dict[str, str] = {}
        for file_path in paths:
            results[file_path] = await self.fetch_file(file_path, ref)
        return results
