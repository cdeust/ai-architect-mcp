"""Tests for Xcode adapter — mocked subprocess."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ai_architect_mcp._adapters.xcode_adapter import XcodeAdapter


class TestXcodeAdapter:
    """Test XcodeAdapter with mocked subprocess."""

    @pytest.mark.asyncio
    async def test_build_success(self) -> None:
        adapter = XcodeAdapter()
        with patch("ai_architect_mcp._adapters.xcode_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"Build Succeeded", b"")
            process.returncode = 0
            mock.return_value = process

            result = await adapter.build("MyScheme")
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_build_failure(self) -> None:
        adapter = XcodeAdapter()
        with patch("ai_architect_mcp._adapters.xcode_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"", b"Build Failed")
            process.returncode = 65
            mock.return_value = process

            result = await adapter.build("MyScheme")
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_run_tests_success(self) -> None:
        adapter = XcodeAdapter()
        with patch("ai_architect_mcp._adapters.xcode_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"Tests Passed", b"")
            process.returncode = 0
            mock.return_value = process

            result = await adapter.run_tests("MyScheme", test_plan="UnitTests")
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_read_file(self, tmp_path: Path) -> None:
        (tmp_path / "hello.swift").write_text("let x = 1")
        adapter = XcodeAdapter(project_path=str(tmp_path))
        content = await adapter.read("hello.swift")
        assert content == "let x = 1"

    @pytest.mark.asyncio
    async def test_write_file(self, tmp_path: Path) -> None:
        adapter = XcodeAdapter(project_path=str(tmp_path))
        await adapter.write("output.swift", "let y = 2")
        assert (tmp_path / "output.swift").read_text() == "let y = 2"

    @pytest.mark.asyncio
    async def test_grep_finds_matches(self, tmp_path: Path) -> None:
        (tmp_path / "a.swift").write_text("let foo = 1\nlet bar = 2")
        (tmp_path / "b.swift").write_text("let baz = 3")
        adapter = XcodeAdapter(project_path=str(tmp_path))
        with patch("ai_architect_mcp._adapters.xcode_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            output = f"{tmp_path}/a.swift:1:let foo = 1\n"
            process.communicate.return_value = (output.encode(), b"")
            process.returncode = 0
            mock.return_value = process

            results = await adapter.grep("foo")
            assert len(results) == 1
            assert results[0]["content"] == "let foo = 1"

    @pytest.mark.asyncio
    async def test_grep_no_matches(self, tmp_path: Path) -> None:
        adapter = XcodeAdapter(project_path=str(tmp_path))
        with patch("ai_architect_mcp._adapters.xcode_adapter.asyncio.create_subprocess_exec") as mock:
            process = AsyncMock()
            process.communicate.return_value = (b"", b"")
            process.returncode = 1
            mock.return_value = process

            results = await adapter.grep("nonexistent")
            assert results == []
