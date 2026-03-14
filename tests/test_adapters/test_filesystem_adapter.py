"""Tests for filesystem adapter — temp dir, boundary enforcement."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ai_architect_mcp._adapters.filesystem_adapter import (
    BoundaryViolationError,
    FileSystemAdapter,
)


@pytest.fixture
def temp_root() -> Path:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def adapter(temp_root: Path) -> FileSystemAdapter:
    """Create adapter with temp root."""
    return FileSystemAdapter(project_root=temp_root)


class TestFileSystemAdapter:
    """Test FileSystemAdapter operations."""

    @pytest.mark.asyncio
    async def test_write_and_read(self, adapter: FileSystemAdapter, temp_root: Path) -> None:
        await adapter.write(Path("test.txt"), "hello world")
        content = await adapter.read(Path("test.txt"))
        assert content == "hello world"

    @pytest.mark.asyncio
    async def test_write_creates_parents(self, adapter: FileSystemAdapter) -> None:
        await adapter.write(Path("sub/dir/file.txt"), "nested")
        content = await adapter.read(Path("sub/dir/file.txt"))
        assert content == "nested"

    @pytest.mark.asyncio
    async def test_exists_true(self, adapter: FileSystemAdapter) -> None:
        await adapter.write(Path("exists.txt"), "yes")
        assert await adapter.exists(Path("exists.txt")) is True

    @pytest.mark.asyncio
    async def test_exists_false(self, adapter: FileSystemAdapter) -> None:
        assert await adapter.exists(Path("nope.txt")) is False

    @pytest.mark.asyncio
    async def test_list_directory(self, adapter: FileSystemAdapter) -> None:
        await adapter.write(Path("a.txt"), "a")
        await adapter.write(Path("b.py"), "b")
        files = await adapter.list_directory(Path("."), "*.txt")
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_boundary_violation(self, adapter: FileSystemAdapter) -> None:
        with pytest.raises(BoundaryViolationError):
            await adapter.read(Path("../../etc/passwd"))

    @pytest.mark.asyncio
    async def test_read_nonexistent_raises(self, adapter: FileSystemAdapter) -> None:
        with pytest.raises(FileNotFoundError):
            await adapter.read(Path("missing.txt"))

    @pytest.mark.asyncio
    async def test_grep_finds_matches(self, adapter: FileSystemAdapter) -> None:
        await adapter.write(Path("search.txt"), "hello world\ngoodbye world")
        await adapter.write(Path("other.txt"), "no match here")
        results = await adapter.grep("hello")
        assert len(results) == 1
        assert results[0]["line"] == 1
        assert "hello" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_grep_no_matches(self, adapter: FileSystemAdapter) -> None:
        await adapter.write(Path("empty.txt"), "nothing special")
        results = await adapter.grep("zzz_nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_grep_restricted_path(self, adapter: FileSystemAdapter) -> None:
        await adapter.write(Path("dir1/a.txt"), "target line")
        await adapter.write(Path("dir2/b.txt"), "target line")
        results = await adapter.grep("target", path=Path("dir1"))
        assert len(results) == 1
        assert "dir1" in results[0]["file"]
