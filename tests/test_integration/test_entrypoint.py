"""Tests for the CI entrypoint script."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ci.entrypoint import (
    EXIT_CONFIG_ERROR,
    EXIT_SUCCESS,
    load_github_context,
    main,
    parse_args,
    validate_context,
    write_output,
)


class TestParseArgs:
    """Tests for argument parsing."""

    def test_issue_trigger(self) -> None:
        args = parse_args(["--trigger", "issue"])
        assert args.trigger == "issue"
        assert not args.dry_run

    def test_nightly_trigger(self) -> None:
        args = parse_args(["--trigger", "nightly"])
        assert args.trigger == "nightly"

    def test_dry_run(self) -> None:
        args = parse_args(["--trigger", "issue", "--dry-run"])
        assert args.dry_run is True

    def test_stages(self) -> None:
        args = parse_args(["--trigger", "issue", "--stages", "0,1,2"])
        assert args.stages == "0,1,2"


class TestValidateContext:
    """Tests for context validation."""

    def test_valid_issue_context(self) -> None:
        context = {
            "repo": "owner/repo",
            "issue_number": "42",
            "pr_number": "",
            "comment": "",
            "github_token": "token",
            "workspace": "/tmp",
            "event_name": "issues",
            "run_id": "123",
        }
        errors = validate_context("issue", context)
        assert len(errors) == 0

    def test_missing_repo(self) -> None:
        context = {
            "repo": "",
            "issue_number": "42",
            "pr_number": "",
            "comment": "",
            "github_token": "",
            "workspace": "",
            "event_name": "",
            "run_id": "",
        }
        errors = validate_context("issue", context)
        assert any("AI_ARCHITECT_REPO" in e for e in errors)

    def test_pr_comment_missing_fields(self) -> None:
        context = {
            "repo": "owner/repo",
            "issue_number": "",
            "pr_number": "",
            "comment": "",
            "github_token": "",
            "workspace": "",
            "event_name": "",
            "run_id": "",
        }
        errors = validate_context("pr-comment", context)
        assert len(errors) == 2


class TestWriteOutput:
    """Tests for write_output function."""

    def test_writes_json(self, tmp_path: Path) -> None:
        result = {"status": "ok"}
        path = write_output(tmp_path / "output", "issue", result)
        assert path.exists()
        assert "ok" in path.read_text()


class TestMain:
    """Tests for main function."""

    def test_dry_run_success(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("AI_ARCHITECT_REPO", "owner/repo")
        monkeypatch.setenv("AI_ARCHITECT_ISSUE_NUMBER", "1")
        code = main(["--trigger", "issue", "--dry-run"])
        assert code == EXIT_SUCCESS

    def test_missing_config_returns_error(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("AI_ARCHITECT_REPO", raising=False)
        monkeypatch.delenv("AI_ARCHITECT_ISSUE_NUMBER", raising=False)
        code = main(["--trigger", "issue"])
        assert code == EXIT_CONFIG_ERROR
