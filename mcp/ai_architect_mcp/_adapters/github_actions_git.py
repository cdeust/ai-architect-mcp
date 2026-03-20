"""GitHub Actions Git adapter — subprocess-based GitOperationsPort.

Wraps git CLI commands for use in GitHub Actions environment.
Assumes git is available on PATH and the workspace is a valid repo.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ai_architect_mcp._adapters.ports import GitOperationsPort

logger = logging.getLogger(__name__)

GIT_CMD = "git"
LOG_FORMAT = "--format=%H|%s|%an|%ai"
FIELD_SEPARATOR = "|"
FIELD_COUNT = 4


class GitCommandError(Exception):
    """Raised when a git command fails."""

    def __init__(self, command: list[str], stderr: str) -> None:
        self.command = command
        self.stderr = stderr
        super().__init__(
            f"Git command failed: {' '.join(command)} — {stderr}"
        )


class GitHubActionsGit(GitOperationsPort):
    """Git adapter for GitHub Actions via subprocess.

    Args:
        repo_path: Path to the git repository.
    """

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize the GitHub Actions git adapter.

        Args:
            repo_path: Working directory for git commands.
        """
        self._repo_path = repo_path

    async def _run(self, *args: str) -> str:
        """Run a git command and return stdout.

        Args:
            *args: Git subcommand and arguments.

        Returns:
            Command stdout as a string.

        Raises:
            GitCommandError: If the command exits with non-zero status.
        """
        cmd = [GIT_CMD, *args]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._repo_path,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise GitCommandError(cmd, stderr.decode().strip())

        return stdout.decode().strip()

    async def create_branch(
        self, branch_name: str, base: str = "main",
    ) -> str:
        """Create a new branch from the specified base.

        Args:
            branch_name: Name for the new branch.
            base: Base branch to create from.

        Returns:
            The full branch reference.
        """
        await self._run("checkout", "-b", branch_name, base)
        return f"refs/heads/{branch_name}"

    async def commit(self, message: str, files: list[str]) -> str:
        """Stage specified files and create a commit.

        Args:
            message: Commit message.
            files: List of file paths to stage.

        Returns:
            The commit SHA.
        """
        await self._run("add", *files)
        await self._run("commit", "-m", message)
        return await self._run("rev-parse", "HEAD")

    async def push(self, branch: str, force: bool = False) -> None:
        """Push a branch to the remote.

        Args:
            branch: Branch name to push.
            force: Whether to force-push.
        """
        args = ["push", "origin", branch]
        if force:
            args.insert(1, "--force")
        await self._run(*args)

    async def diff(self, base: str, head: str) -> str:
        """Get the diff between two refs.

        Args:
            base: Base ref for comparison.
            head: Head ref for comparison.

        Returns:
            Unified diff as a string.
        """
        return await self._run("diff", f"{base}...{head}")

    async def log(
        self, branch: str, count: int = 10,
    ) -> list[dict[str, str]]:
        """Get recent commit log entries.

        Args:
            branch: Branch to read log from.
            count: Number of entries to return.

        Returns:
            List of commit entries.
        """
        output = await self._run(
            "log", branch, f"-{count}", LOG_FORMAT,
        )
        entries: list[dict[str, str]] = []
        for line in output.splitlines():
            parts = line.split(FIELD_SEPARATOR, FIELD_COUNT - 1)
            if len(parts) == FIELD_COUNT:
                entries.append({
                    "sha": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })
        return entries

    async def reset(self, ref: str) -> None:
        """Reset current branch to ref.

        Args:
            ref: The git ref to reset to.
        """
        await self._run("reset", "--hard", ref)

    async def reset_branch(self, branch: str, to_ref: str) -> None:
        """Reset a specific branch to a ref.

        Args:
            branch: The branch to reset.
            to_ref: The ref to reset the branch to.
        """
        await self._run("branch", "-f", branch, to_ref)

    async def create_worktree(
        self, branch_name: str, base: str = "main",
    ) -> str:
        """Create an isolated git worktree with a new branch.

        Args:
            branch_name: Branch to create in the worktree.
            base: Base branch to fork from.

        Returns:
            Absolute path to the worktree directory.
        """
        import tempfile

        safe_name = branch_name.replace("/", "-")
        worktree_dir = tempfile.mkdtemp(
            prefix=f"pipeline-{safe_name}-",
        )
        await self._run(
            "worktree", "add", worktree_dir,
            "-b", branch_name, base,
        )
        return worktree_dir

    async def remove_worktree(self, worktree_path: str) -> None:
        """Remove a previously created worktree.

        Args:
            worktree_path: Path returned by create_worktree.
        """
        await self._run("worktree", "remove", worktree_path, "--force")
        await self._run("worktree", "prune")
