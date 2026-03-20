"""Tests for pipeline modules (Epic 11)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ai_codebase_intelligence._pipeline.chunk_manager import (
    DEFAULT_BYTE_BUDGET,
    create_chunks,
)
from ai_codebase_intelligence._pipeline.filesystem_walker import discover_files


class TestChunkManager:
    """Tests for chunk creation."""

    def test_empty_list(self) -> None:
        chunks = create_chunks([])
        assert chunks == []

    def test_single_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("print('hello')", encoding="utf-8")
        chunks = create_chunks([str(f)])
        assert len(chunks) == 1
        assert len(chunks[0].files) == 1

    def test_budget_splitting(self, tmp_path: Path) -> None:
        files = []
        for i in range(5):
            f = tmp_path / f"file_{i}.py"
            f.write_text("x" * 5000, encoding="utf-8")
            files.append(str(f))

        # 10KB budget — each file is ~5KB, so 2 per chunk
        chunks = create_chunks(files, byte_budget=10_000)
        assert len(chunks) >= 2

    def test_oversized_file_skipped(self, tmp_path: Path) -> None:
        f = tmp_path / "huge.py"
        f.write_text("x" * 100, encoding="utf-8")
        chunks = create_chunks([str(f)], byte_budget=50)
        assert len(chunks) == 0


class TestFilesystemWalker:
    """Tests for file discovery."""

    def test_discover_in_repo(self) -> None:
        # Discover files in the ai-codebase-intelligence package itself
        repo = "/Users/cdeust/Developments/anthropic/ai-architect/ai-codebase-intelligence"
        files = discover_files(repo)
        assert len(files) > 0
        assert all(f.endswith(".py") for f in files)

    def test_discover_nonexistent(self) -> None:
        files = discover_files("/nonexistent/path")
        assert files == []

    def test_ignores_pycache(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("pass", encoding="utf-8")
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "main.cpython-311.pyc").write_text("bytecode", encoding="utf-8")

        files = discover_files(str(tmp_path))
        assert len(files) == 1
        assert files[0].endswith("main.py")
