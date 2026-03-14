"""Tests for xcode_tools — verify renamed tools are importable."""

from __future__ import annotations

import pytest


class TestXcodeToolsImport:
    """Verify Xcode tools are importable with spec names."""

    def test_run_build_importable(self) -> None:
        from ai_architect_mcp._tools.xcode_tools import ai_architect_run_build
        assert callable(ai_architect_run_build)

    def test_run_tests_importable(self) -> None:
        from ai_architect_mcp._tools.xcode_tools import ai_architect_run_tests
        assert callable(ai_architect_run_tests)

    def test_old_names_removed(self) -> None:
        import ai_architect_mcp._tools.xcode_tools as xt
        assert not hasattr(xt, "ai_architect_xcode_build")
        assert not hasattr(xt, "ai_architect_xcode_test")
        assert not hasattr(xt, "ai_architect_xcode_preview")
        assert not hasattr(xt, "ai_architect_xcode_build_log")
        assert not hasattr(xt, "ai_architect_xcode_doc_search")
        assert not hasattr(xt, "ai_architect_xcode_issues")

    def test_old_adapter_tools_no_xcode(self) -> None:
        """Xcode tools should NOT be in adapter_tools anymore."""
        import ai_architect_mcp._tools.adapter_tools as at
        assert not hasattr(at, "ai_architect_xcode_build")
        assert not hasattr(at, "ai_architect_xcode_test")
