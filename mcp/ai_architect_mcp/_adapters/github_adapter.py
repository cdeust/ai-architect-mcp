"""GitHub adapter — concrete implementation of GitHubOperationsPort.

Wraps the GitHub CLI (gh) for pull request and repository operations.
Injected at the composition root. Never imported directly by stage logic.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import re

from ai_architect_mcp._adapters.ports import GitHubOperationsPort


def _extract_pr_number(url: str) -> int:
    """Extract PR number from a GitHub PR URL.

    Args:
        url: GitHub PR URL (e.g., 'https://github.com/owner/repo/pull/42').

    Returns:
        PR number, or 0 if not parseable.
    """
    match = re.search(r"/pull/(\d+)", url)
    return int(match.group(1)) if match else 0


class GitHubOperationError(Exception):
    """Raised when a GitHub CLI command fails.

    Attributes:
        command: The gh command that failed.
        stderr: Standard error output.
        exit_code: Process exit code.
    """

    def __init__(self, command: str, stderr: str, exit_code: int) -> None:
        self.command = command
        self.stderr = stderr
        self.exit_code = exit_code
        super().__init__(
            f"GitHub CLI failed (exit {exit_code}): {command}\n{stderr}"
        )


class GitHubAdapter(GitHubOperationsPort):
    """Concrete GitHub adapter wrapping the gh CLI.

    Args:
        repo: Repository in owner/repo format. If None, uses current repo.
    """

    def __init__(self, repo: str | None = None) -> None:
        """Initialize the GitHub adapter.

        Args:
            repo: Repository in owner/repo format.
        """
        self._repo = repo

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
            body: PR description body.
            head: Source branch.
            base: Target branch.

        Returns:
            PR metadata with number, url, and state.
        """
        args = [
            "pr", "create",
            "--title", title,
            "--body", body,
            "--head", head,
            "--base", base,
        ]
        output = await self._run(*args)
        url = output.strip()
        # gh pr create outputs the PR URL on stdout
        pr_number = _extract_pr_number(url)
        return {"number": pr_number, "url": url, "state": "open"}

    async def fetch_tree(
        self, path: str = "", ref: str = "HEAD"
    ) -> list[dict[str, str]]:
        """Fetch repository tree structure via gh api.

        Args:
            path: Subdirectory path. Empty string for root.
            ref: Git ref to fetch from.

        Returns:
            List of tree entries with path, type, and sha.
        """
        api_path = f"/git/trees/{ref}"
        output = await self._run(
            "api", f"repos/{{owner}}/{{repo}}{api_path}",
        )
        data = json.loads(output)
        tree = data.get("tree", [])
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
        import base64

        output = await self._run(
            "api", f"repos/{{owner}}/{{repo}}/contents/{path}",
            "-q", ".content",
            "--header", f"ref: {ref}",
        )
        return base64.b64decode(output.strip()).decode("utf-8")

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

    async def _run(self, *args: str) -> str:
        """Run a gh CLI command and return stdout.

        Args:
            *args: gh subcommand and arguments.

        Returns:
            Standard output from the command.

        Raises:
            GitHubOperationError: If the command exits non-zero.
        """
        cmd = ["gh"]
        if self._repo:
            cmd.extend(["--repo", self._repo])
        cmd.extend(args)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise GitHubOperationError(
                command=f"gh {' '.join(args)}",
                stderr=stderr.decode(),
                exit_code=process.returncode or 1,
            )

        return stdout.decode()
