"""Tests for git utility functions."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_codebase_intelligence.storage.git import (
    get_current_commit,
    get_git_root,
    is_git_repo,
)


@pytest.fixture
def real_repo(tmp_path: Path) -> Path:
    """Create an isolated git repo with a single commit."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, check=True,
    )
    (tmp_path / "README.md").write_text("test\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=tmp_path, check=True,
    )
    return tmp_path


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_current_repo(self, real_repo: Path) -> None:
        assert is_git_repo(str(real_repo)) is True

    def test_non_repo(self, tmp_path: Path) -> None:
        assert is_git_repo(str(tmp_path)) is False

    def test_nonexistent_path(self) -> None:
        assert is_git_repo("/nonexistent/path/foo/bar") is False


class TestGetGitRoot:
    """Tests for get_git_root function."""

    def test_from_subdir(self, real_repo: Path) -> None:
        sub = real_repo / "sub"
        sub.mkdir()
        root = get_git_root(str(sub))
        assert root is not None
        assert Path(root).resolve() == real_repo.resolve()

    def test_nonexistent(self) -> None:
        assert get_git_root("/nonexistent/path") is None


class TestGetCurrentCommit:
    """Tests for get_current_commit function."""

    def test_returns_full_hash(self, real_repo: Path) -> None:
        commit = get_current_commit(str(real_repo))
        assert len(commit) == 40
        assert all(c in "0123456789abcdef" for c in commit)

    def test_nonexistent_returns_empty(self) -> None:
        assert get_current_commit("/nonexistent") == ""
