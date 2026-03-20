"""Tests for ignore service configuration."""

from __future__ import annotations

from ai_codebase_intelligence._config.ignore_service import (
    DEFAULT_IGNORE_DIRS,
    IGNORED_EXTENSIONS,
    IGNORED_FILES,
    MAX_FILE_SIZE_BYTES,
    should_ignore_dir,
    should_ignore_file,
)


class TestShouldIgnoreDir:
    """Tests for should_ignore_dir function."""

    def test_node_modules(self) -> None:
        assert should_ignore_dir("node_modules") is True

    def test_git(self) -> None:
        assert should_ignore_dir(".git") is True

    def test_pycache(self) -> None:
        assert should_ignore_dir("__pycache__") is True

    def test_venv(self) -> None:
        assert should_ignore_dir("venv") is True
        assert should_ignore_dir(".venv") is True

    def test_build_dirs(self) -> None:
        assert should_ignore_dir("build") is True
        assert should_ignore_dir("dist") is True
        assert should_ignore_dir("DerivedData") is True

    def test_hidden_dirs(self) -> None:
        assert should_ignore_dir(".idea") is True
        assert should_ignore_dir(".hidden") is True

    def test_source_dirs_allowed(self) -> None:
        assert should_ignore_dir("src") is False
        assert should_ignore_dir("lib") is False
        assert should_ignore_dir("tests") is False
        assert should_ignore_dir("app") is False


class TestShouldIgnoreFile:
    """Tests for should_ignore_file function."""

    def test_lock_files(self) -> None:
        assert should_ignore_file("package-lock.json") is True
        assert should_ignore_file("yarn.lock") is True
        assert should_ignore_file("poetry.lock") is True

    def test_binary_extensions(self) -> None:
        assert should_ignore_file("image.png") is True
        assert should_ignore_file("font.woff2") is True
        assert should_ignore_file("archive.zip") is True

    def test_minified(self) -> None:
        assert should_ignore_file("bundle.min.js") is True
        assert should_ignore_file("style.min.css") is True

    def test_source_files_allowed(self) -> None:
        assert should_ignore_file("main.py") is False
        assert should_ignore_file("app.ts") is False
        assert should_ignore_file("ViewController.swift") is False

    def test_ds_store(self) -> None:
        assert should_ignore_file(".DS_Store") is True


class TestConstants:
    """Tests for module constants."""

    def test_max_file_size(self) -> None:
        assert MAX_FILE_SIZE_BYTES == 1_000_000

    def test_ignore_dirs_is_frozen(self) -> None:
        assert isinstance(DEFAULT_IGNORE_DIRS, frozenset)

    def test_ignore_extensions_is_frozen(self) -> None:
        assert isinstance(IGNORED_EXTENSIONS, frozenset)

    def test_ignore_files_is_frozen(self) -> None:
        assert isinstance(IGNORED_FILES, frozenset)
