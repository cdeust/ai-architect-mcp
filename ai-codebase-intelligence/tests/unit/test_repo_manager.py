"""Tests for repository manager."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from ai_codebase_intelligence._models.pipeline_types import RepoMetadata
from ai_codebase_intelligence._storage.repo_manager import (
    load_registry,
    register_repo,
    save_registry,
    unregister_repo,
)


class TestRepoManager:
    """Tests for repository registry operations."""

    def test_load_empty_registry(self, tmp_path: Path) -> None:
        with patch(
            "ai_codebase_intelligence._storage.repo_manager.REGISTRY_FILE",
            tmp_path / "registry.json",
        ):
            registry = load_registry()
            assert registry == {}

    def test_save_and_load(self, tmp_path: Path) -> None:
        reg_file = tmp_path / "registry.json"
        reg_dir = tmp_path
        with (
            patch(
                "ai_codebase_intelligence._storage.repo_manager.REGISTRY_FILE",
                reg_file,
            ),
            patch(
                "ai_codebase_intelligence._storage.repo_manager.REGISTRY_DIR",
                reg_dir,
            ),
        ):
            meta = RepoMetadata(
                repo_path="/tmp/repo",
                repo_name="repo",
                total_nodes=100,
            )
            save_registry({"/tmp/repo": meta})

            loaded = load_registry()
            assert "/tmp/repo" in loaded
            assert loaded["/tmp/repo"].total_nodes == 100

    def test_register_and_unregister(self, tmp_path: Path) -> None:
        reg_file = tmp_path / "registry.json"
        reg_dir = tmp_path
        db_dir = tmp_path / "databases"
        with (
            patch(
                "ai_codebase_intelligence._storage.repo_manager.REGISTRY_FILE",
                reg_file,
            ),
            patch(
                "ai_codebase_intelligence._storage.repo_manager.REGISTRY_DIR",
                reg_dir,
            ),
            patch(
                "ai_codebase_intelligence._storage.repo_manager.DB_BASE_DIR",
                db_dir,
            ),
        ):
            meta = register_repo("/tmp/repo", "repo", "abc1234")
            assert meta.repo_name == "repo"
            assert meta.last_commit == "abc1234"

            removed = unregister_repo("/tmp/repo")
            assert removed is True

            removed_again = unregister_repo("/tmp/repo")
            assert removed_again is False

    def test_load_corrupted_registry(self, tmp_path: Path) -> None:
        reg_file = tmp_path / "registry.json"
        reg_file.write_text("not valid json", encoding="utf-8")
        with patch(
            "ai_codebase_intelligence._storage.repo_manager.REGISTRY_FILE",
            reg_file,
        ):
            registry = load_registry()
            assert registry == {}
