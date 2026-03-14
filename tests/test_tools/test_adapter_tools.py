"""Tests for adapter tools."""

from __future__ import annotations

import pytest


class TestAdapterTools:
    @pytest.mark.asyncio
    async def test_fs_read(self) -> None:
        from ai_architect_mcp._tools.adapter_tools import ai_architect_fs_read

        result = await ai_architect_fs_read(path="README.md")
        assert "path" in result
        assert result["path"] == "README.md"

    @pytest.mark.asyncio
    async def test_fs_list(self) -> None:
        from ai_architect_mcp._tools.adapter_tools import ai_architect_fs_list

        result = await ai_architect_fs_list(path=".", pattern="*.py")
        assert "files" in result
        assert result["pattern"] == "*.py"

    @pytest.mark.asyncio
    async def test_git_diff(self) -> None:
        from ai_architect_mcp._tools.adapter_tools import ai_architect_git_diff

        result = await ai_architect_git_diff(base="main", head="HEAD")
        assert "diff" in result
