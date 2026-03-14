"""Tests for HOR structural rules 1-10."""

from __future__ import annotations

from ai_architect_mcp._verification.hor_rules.structural import (
    rule_001_title_exists,
    rule_002_sections_present,
    rule_003_ac_numbering,
    rule_005_no_volatile_indexes,
    rule_007_no_placeholder_tests,
)


class TestStructuralRules:
    def test_rule_001_pass(self) -> None:
        result = rule_001_title_exists({"title": "Valid PRD Title"})
        assert result.passed is True

    def test_rule_001_fail_empty(self) -> None:
        result = rule_001_title_exists({"title": ""})
        assert result.passed is False

    def test_rule_001_fail_missing(self) -> None:
        result = rule_001_title_exists({})
        assert result.passed is False

    def test_rule_001_fail_too_long(self) -> None:
        result = rule_001_title_exists({"title": "A" * 201})
        assert result.passed is False

    def test_rule_002_pass(self) -> None:
        sections = [
            {"name": s}
            for s in [
                "Overview", "Requirements", "User Stories",
                "Technical", "Acceptance", "Roadmap", "Testing",
            ]
        ]
        result = rule_002_sections_present({"sections": sections})
        assert result.passed is True

    def test_rule_002_fail(self) -> None:
        result = rule_002_sections_present({"sections": [{"name": "Overview"}]})
        assert result.passed is False

    def test_rule_003_pass(self) -> None:
        result = rule_003_ac_numbering({"content": "AC-001 first AC-002 second AC-003 third"})
        assert result.passed is True

    def test_rule_003_fail_gap(self) -> None:
        result = rule_003_ac_numbering({"content": "AC-001 first AC-003 third"})
        assert result.passed is False

    def test_rule_005_pass(self) -> None:
        result = rule_005_no_volatile_indexes({"content": "CREATE INDEX idx ON t (col)"})
        assert result.passed is True

    def test_rule_005_fail(self) -> None:
        result = rule_005_no_volatile_indexes(
            {"content": "CREATE INDEX idx ON t WHERE created_at > NOW()"}
        )
        assert result.passed is False

    def test_rule_007_pass(self) -> None:
        result = rule_007_no_placeholder_tests({"content": "def test_auth():\n    assert True"})
        assert result.passed is True

    def test_rule_007_fail(self) -> None:
        result = rule_007_no_placeholder_tests({"content": "def test_auth():\n    pass"})
        assert result.passed is False
