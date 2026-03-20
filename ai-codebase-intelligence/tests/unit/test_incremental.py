"""Tests for incremental reindex pipeline."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from ai_codebase_intelligence._pipeline.incremental import incremental_reindex
from ai_codebase_intelligence._storage.in_memory_graph import InMemoryGraphStorage


def _create_temp_python_file(directory: str, name: str, content: str) -> str:
    """Create a temporary Python file in the given directory.

    Args:
        directory: Directory to create the file in.
        name: File name (with .py extension).
        content: Python source code.

    Returns:
        Absolute path to the created file.
    """
    file_path = os.path.join(directory, name)
    Path(file_path).write_text(content, encoding="utf-8")
    return file_path


class TestIncrementalReindex:
    """Tests for the incremental_reindex function."""

    @pytest.mark.asyncio
    async def test_empty_changed_files_returns_quickly(self) -> None:
        """Incremental with no changes returns zero metrics."""
        storage = InMemoryGraphStorage()
        await storage.initialize()

        result = await incremental_reindex("/tmp/fake-repo", storage, [])

        assert result.total_files == 0
        assert result.total_nodes == 0
        assert result.total_relationships == 0
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_single_changed_file_produces_nodes(self) -> None:
        """Incremental reindex with 1 changed file creates nodes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = _create_temp_python_file(
                tmp_dir,
                "example.py",
                "def hello():\n    return 'world'\n",
            )

            storage = InMemoryGraphStorage()
            await storage.initialize()

            result = await incremental_reindex(
                tmp_dir, storage, [file_path]
            )

            assert result.total_files == 1
            assert result.total_nodes > 0
            assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_unchanged_files_not_reprocessed(self) -> None:
        """Only files in the changed list are processed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            changed = _create_temp_python_file(
                tmp_dir,
                "changed.py",
                "def changed_fn():\n    pass\n",
            )
            _unchanged = _create_temp_python_file(
                tmp_dir,
                "unchanged.py",
                "def unchanged_fn():\n    pass\n",
            )

            storage = InMemoryGraphStorage()
            await storage.initialize()

            result = await incremental_reindex(
                tmp_dir, storage, [changed]
            )

            # Only the changed file should be counted
            assert result.total_files == 1

            # Check that nodes belong only to the changed file
            node_count = await storage.node_count()
            assert node_count > 0

            for node_id, node in storage._nodes.items():
                if node.file_path:
                    assert "unchanged.py" not in node.file_path

    @pytest.mark.asyncio
    async def test_multiple_changed_files(self) -> None:
        """Incremental reindex handles multiple changed files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_a = _create_temp_python_file(
                tmp_dir,
                "file_a.py",
                "class Foo:\n    pass\n",
            )
            file_b = _create_temp_python_file(
                tmp_dir,
                "file_b.py",
                "def bar():\n    return 42\n",
            )

            storage = InMemoryGraphStorage()
            await storage.initialize()

            result = await incremental_reindex(
                tmp_dir, storage, [file_a, file_b]
            )

            assert result.total_files == 2
            assert result.total_nodes > 0
