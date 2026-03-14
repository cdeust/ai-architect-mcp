"""Tests for GitHub Actions filesystem adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect_mcp._adapters.filesystem_adapter import (
    BoundaryViolationError,
)
from ai_architect_mcp._adapters.github_actions_filesystem import (
    GitHubActionsFilesystem,
)


class TestGitHubActionsFilesystem:
    """Tests for GitHubActionsFilesystem adapter."""

    def test_init_with_explicit_workspace(self, tmp_path: Path) -> None:
        adapter = GitHubActionsFilesystem(workspace=tmp_path)
        assert adapter._root == tmp_path.resolve()

    def test_init_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
        adapter = GitHubActionsFilesystem()
        assert adapter._root == tmp_path.resolve()

    def test_init_no_workspace_raises(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("GITHUB_WORKSPACE", raising=False)
        with pytest.raises(ValueError, match="GITHUB_WORKSPACE"):
            GitHubActionsFilesystem()

    @pytest.mark.asyncio
    async def test_read_write_roundtrip(self, tmp_path: Path) -> None:
        adapter = GitHubActionsFilesystem(workspace=tmp_path)
        await adapter.write(Path("test.txt"), "hello")
        content = await adapter.read(Path("test.txt"))
        assert content == "hello"

    @pytest.mark.asyncio
    async def test_exists(self, tmp_path: Path) -> None:
        adapter = GitHubActionsFilesystem(workspace=tmp_path)
        assert not await adapter.exists(Path("missing.txt"))
        await adapter.write(Path("exists.txt"), "yes")
        assert await adapter.exists(Path("exists.txt"))

    @pytest.mark.asyncio
    async def test_list_directory(self, tmp_path: Path) -> None:
        adapter = GitHubActionsFilesystem(workspace=tmp_path)
        await adapter.write(Path("a.txt"), "a")
        await adapter.write(Path("b.py"), "b")
        files = await adapter.list_directory(Path("."), "*.txt")
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_boundary_violation(self, tmp_path: Path) -> None:
        adapter = GitHubActionsFilesystem(workspace=tmp_path)
        with pytest.raises(BoundaryViolationError):
            await adapter.read(Path("../../etc/passwd"))

    @pytest.mark.asyncio
    async def test_grep(self, tmp_path: Path) -> None:
        adapter = GitHubActionsFilesystem(workspace=tmp_path)
        await adapter.write(Path("search.txt"), "hello world\ngoodbye")
        results = await adapter.grep("hello")
        assert len(results) == 1
        assert results[0]["line"] == 1
