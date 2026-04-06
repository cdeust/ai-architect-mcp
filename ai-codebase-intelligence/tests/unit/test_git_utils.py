"""Tests for git utility functions."""

from __future__ import annotations

from ai_codebase_intelligence.storage.git import (
    get_current_commit,
    get_git_root,
    is_git_repo,
)


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_current_repo(self) -> None:
        # The ai-architect repo is a git repo
        assert is_git_repo("/Users/cdeust/Developments/anthropic/ai-architect") is True

    def test_non_repo(self, tmp_path: str) -> None:
        assert is_git_repo(str(tmp_path)) is False

    def test_nonexistent_path(self) -> None:
        assert is_git_repo("/nonexistent/path/foo/bar") is False


class TestGetGitRoot:
    """Tests for get_git_root function."""

    def test_from_subdir(self) -> None:
        root = get_git_root(
            "/Users/cdeust/Developments/anthropic/ai-architect/mcp"
        )
        assert root is not None
        assert root.endswith("ai-architect")

    def test_nonexistent(self) -> None:
        assert get_git_root("/nonexistent/path") is None


class TestGetCurrentCommit:
    """Tests for get_current_commit function."""

    def test_returns_full_hash(self) -> None:
        commit = get_current_commit(
            "/Users/cdeust/Developments/anthropic/ai-architect"
        )
        assert len(commit) == 40
        # Should be hex characters
        assert all(c in "0123456789abcdef" for c in commit)

    def test_nonexistent_returns_empty(self) -> None:
        assert get_current_commit("/nonexistent") == ""
