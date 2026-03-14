"""Tests for GitHub Actions git adapter."""

from __future__ import annotations

import pytest

from ai_architect_mcp._adapters.github_actions_git import (
    GitCommandError,
    GitHubActionsGit,
)


class TestGitHubActionsGit:
    """Tests for GitHubActionsGit adapter."""

    def test_init_default_repo_path(self) -> None:
        adapter = GitHubActionsGit()
        assert adapter._repo_path == "."

    def test_init_custom_repo_path(self) -> None:
        adapter = GitHubActionsGit(repo_path="/tmp/repo")
        assert adapter._repo_path == "/tmp/repo"

    @pytest.mark.asyncio
    async def test_create_branch_builds_ref(
        self, tmp_path: "Path",
    ) -> None:
        """Test branch creation in a real git repo."""
        from pathlib import Path
        import subprocess

        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo), check=True, capture_output=True,
        )
        (repo / "file.txt").write_text("init")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo),
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=str(repo), check=True, capture_output=True,
        )

        adapter = GitHubActionsGit(repo_path=str(repo))
        ref = await adapter.create_branch("test-branch", "main")
        assert ref == "refs/heads/test-branch"

    @pytest.mark.asyncio
    async def test_commit_returns_sha(self, tmp_path: "Path") -> None:
        """Test commit returns a valid SHA."""
        from pathlib import Path
        import subprocess

        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo), check=True, capture_output=True,
        )
        (repo / "file.txt").write_text("init")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo),
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=str(repo), check=True, capture_output=True,
        )

        (repo / "new.txt").write_text("content")
        adapter = GitHubActionsGit(repo_path=str(repo))
        sha = await adapter.commit("test commit", ["new.txt"])
        assert len(sha) == 40

    @pytest.mark.asyncio
    async def test_log_parses_entries(self, tmp_path: "Path") -> None:
        """Test log parsing returns structured entries."""
        from pathlib import Path
        import subprocess

        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo), check=True, capture_output=True,
        )
        (repo / "file.txt").write_text("init")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo),
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial commit"],
            cwd=str(repo), check=True, capture_output=True,
        )

        adapter = GitHubActionsGit(repo_path=str(repo))
        entries = await adapter.log("main", count=5)
        assert len(entries) == 1
        assert entries[0]["message"] == "initial commit"
        assert "sha" in entries[0]

    @pytest.mark.asyncio
    async def test_reset(self, tmp_path: "Path") -> None:
        """Test reset to a ref."""
        from pathlib import Path
        import subprocess

        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo), check=True, capture_output=True,
        )
        (repo / "file.txt").write_text("init")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo),
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=str(repo), check=True, capture_output=True,
        )
        initial_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo), check=True, capture_output=True,
        ).stdout.decode().strip()

        (repo / "file.txt").write_text("changed")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo),
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "second"],
            cwd=str(repo), check=True, capture_output=True,
        )

        adapter = GitHubActionsGit(repo_path=str(repo))
        await adapter.reset(initial_sha)

        current = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo), check=True, capture_output=True,
        ).stdout.decode().strip()
        assert current == initial_sha

    @pytest.mark.asyncio
    async def test_reset_branch(self, tmp_path: "Path") -> None:
        """Test reset_branch to a ref."""
        from pathlib import Path
        import subprocess

        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(repo), check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo), check=True, capture_output=True,
        )
        (repo / "file.txt").write_text("init")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo),
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=str(repo), check=True, capture_output=True,
        )
        initial_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo), check=True, capture_output=True,
        ).stdout.decode().strip()

        subprocess.run(
            ["git", "checkout", "-b", "feature"],
            cwd=str(repo), check=True, capture_output=True,
        )
        (repo / "file.txt").write_text("changed")
        subprocess.run(
            ["git", "add", "."], cwd=str(repo),
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "feature work"],
            cwd=str(repo), check=True, capture_output=True,
        )
        # Switch back to main so we can force-update feature
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=str(repo), check=True, capture_output=True,
        )

        adapter = GitHubActionsGit(repo_path=str(repo))
        await adapter.reset_branch("feature", initial_sha)

        feature_sha = subprocess.run(
            ["git", "rev-parse", "feature"],
            cwd=str(repo), check=True, capture_output=True,
        ).stdout.decode().strip()
        assert feature_sha == initial_sha


class TestGitCommandError:
    """Tests for GitCommandError."""

    def test_error_message(self) -> None:
        err = GitCommandError(["git", "push"], "rejected")
        assert "git push" in str(err)
        assert "rejected" in str(err)
