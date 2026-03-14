"""Tests for composition root — correct port types returned."""

from __future__ import annotations

from pathlib import Path

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp._adapters.ports import (
    FileSystemPort,
    GitHubOperationsPort,
    GitOperationsPort,
    XcodeOperationsPort,
)


class TestCompositionRoot:
    """Test CompositionRoot creates correct port implementations."""

    def test_create_git(self) -> None:
        root = CompositionRoot()
        adapter = root.create_git()
        assert isinstance(adapter, GitOperationsPort)

    def test_create_github(self) -> None:
        root = CompositionRoot()
        adapter = root.create_github()
        assert isinstance(adapter, GitHubOperationsPort)

    def test_create_xcode(self) -> None:
        root = CompositionRoot()
        adapter = root.create_xcode()
        assert isinstance(adapter, XcodeOperationsPort)

    def test_create_filesystem(self) -> None:
        root = CompositionRoot(project_root=Path("/tmp"))
        adapter = root.create_filesystem()
        assert isinstance(adapter, FileSystemPort)

    def test_create_context(self) -> None:
        root = CompositionRoot()
        context = root.create_context()
        assert context is not None

    def test_no_diagnostics_method(self) -> None:
        root = CompositionRoot()
        assert not hasattr(root, "create_xcode_diagnostics")
