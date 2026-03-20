"""Git adapter — concrete implementation of GitOperationsPort.

Wraps git CLI commands via asyncio subprocess for version control
operations. Injected at the composition root. Never imported directly
by stage logic.
"""

from __future__ import annotations

import asyncio
import json

from ai_architect_mcp._adapters.ports import GitOperationsPort


class GitOperationError(Exception):
    """Raised when a git CLI command fails.

    Attributes:
        command: The git command that failed.
        stderr: Standard error output from the command.
        exit_code: Process exit code.
    """

    def __init__(self, command: str, stderr: str, exit_code: int) -> None:
        self.command = command
        self.stderr = stderr
        self.exit_code = exit_code
        super().__init__(
            f"Git command failed (exit {exit_code}): {command}\n{stderr}"
        )


class GitAdapter(GitOperationsPort):
    """Concrete git adapter wrapping the git CLI.

    All operations use asyncio.create_subprocess_exec for
    non-blocking execution.

    Args:
        repo_path: Path to the git repository root.
    """

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize the git adapter.

        Args:
            repo_path: Path to the git repository root.
        """
        self._repo_path = repo_path

    async def create_branch(
        self, branch_name: str, base: str = "main"
    ) -> str:
        """Create a new branch from the specified base.

        Args:
            branch_name: Name for the new branch.
            base: Base branch to create from.

        Returns:
            The full branch reference.
        """
        await self._run("checkout", base)
        await self._run("checkout", "-b", branch_name)
        return f"refs/heads/{branch_name}"

    async def commit(self, message: str, files: list[str]) -> str:
        """Stage specified files and create a commit.

        Args:
            message: Commit message.
            files: File paths to stage.

        Returns:
            The commit SHA.
        """
        for file_path in files:
            await self._run("add", file_path)
        await self._run("commit", "-m", message)
        result = await self._run("rev-parse", "HEAD")
        return result.strip()

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
        self, branch: str, count: int = 10
    ) -> list[dict[str, str]]:
        """Get recent commit log entries.

        Args:
            branch: Branch to read log from.
            count: Number of entries to return.

        Returns:
            List of commit entries.
        """
        format_str = (
            '{"sha": "%H", "message": "%s", '
            '"author": "%an", "date": "%aI"}'
        )
        output = await self._run(
            "log", branch, f"-{count}",
            f"--format={format_str}",
        )
        entries: list[dict[str, str]] = []
        for line in output.strip().split("\n"):
            if line.strip():
                entries.append(json.loads(line))
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
        self, branch_name: str, base: str = "main"
    ) -> str:
        """Create an isolated git worktree with a new branch.

        Uses ``git worktree add`` so each finding gets its own working
        directory and branch.  1000 concurrent findings = 1000 worktrees,
        no checkout collisions.

        Args:
            branch_name: Branch to create inside the worktree.
            base: Base ref to fork from.

        Returns:
            Absolute path to the new worktree directory.
        """
        import tempfile
        from pathlib import Path as P

        worktree_dir = P(tempfile.mkdtemp(
            prefix=f"pipeline-{branch_name.replace('/', '-')}-",
        ))
        await self._run(
            "worktree", "add",
            str(worktree_dir),
            "-b", branch_name,
            base,
        )
        return str(worktree_dir)

    async def remove_worktree(self, worktree_path: str) -> None:
        """Remove a worktree and prune its metadata.

        Args:
            worktree_path: Absolute path returned by create_worktree.
        """
        await self._run("worktree", "remove", worktree_path, "--force")
        await self._run("worktree", "prune")

    async def _run(self, *args: str) -> str:
        """Run a git command and return stdout.

        Args:
            *args: Git subcommand and arguments.

        Returns:
            Standard output from the command.

        Raises:
            GitOperationError: If the command exits with non-zero status.
        """
        process = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=self._repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise GitOperationError(
                command=f"git {' '.join(args)}",
                stderr=stderr.decode(),
                exit_code=process.returncode or 1,
            )

        return stdout.decode()
