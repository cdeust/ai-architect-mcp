"""Tests for Finding model — validation, serialization, enum coverage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_architect_mcp._models.finding import Finding, Severity, SourceCategory

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestSourceCategory:
    """Test SourceCategory enum coverage."""

    def test_all_14_categories_present(self) -> None:
        assert len(SourceCategory) == 14

    def test_category_values(self) -> None:
        expected = {
            "amazon_aws", "anthropic", "apple", "cohere",
            "google_deepmind", "hugging_face", "meta_fair", "microsoft",
            "moonshot_01ai", "sakana_aleph_alpha", "samsung",
            "stability_midjourney", "together_fireworks", "internal",
        }
        assert {c.value for c in SourceCategory} == expected


class TestSeverity:
    """Test Severity enum."""

    def test_all_levels_present(self) -> None:
        assert len(Severity) == 4

    def test_ordering(self) -> None:
        levels = [s.value for s in Severity]
        assert levels == ["low", "medium", "high", "critical"]


class TestFinding:
    """Test Finding model validation and serialization."""

    def test_valid_finding(self) -> None:
        finding = Finding(
            finding_id="FIND-001",
            title="Test Finding",
            description="A test finding for validation",
            source_category=SourceCategory.ANTHROPIC,
            relevance_score=0.85,
            severity=Severity.HIGH,
        )
        assert finding.finding_id == "FIND-001"
        assert finding.relevance_score == 0.85

    def test_empty_title_rejected(self) -> None:
        with pytest.raises(ValueError, match="title must not be empty"):
            Finding(
                finding_id="FIND-002",
                title="   ",
                description="Valid description",
                source_category=SourceCategory.INTERNAL,
                relevance_score=0.5,
                severity=Severity.LOW,
            )

    def test_empty_description_rejected(self) -> None:
        with pytest.raises(ValueError, match="description must not be empty"):
            Finding(
                finding_id="FIND-003",
                title="Valid Title",
                description="",
                source_category=SourceCategory.INTERNAL,
                relevance_score=0.5,
                severity=Severity.LOW,
            )

    def test_score_below_zero_rejected(self) -> None:
        with pytest.raises(ValueError):
            Finding(
                finding_id="FIND-004",
                title="Valid",
                description="Valid",
                source_category=SourceCategory.INTERNAL,
                relevance_score=-0.1,
                severity=Severity.LOW,
            )

    def test_score_above_one_rejected(self) -> None:
        with pytest.raises(ValueError):
            Finding(
                finding_id="FIND-005",
                title="Valid",
                description="Valid",
                source_category=SourceCategory.INTERNAL,
                relevance_score=1.1,
                severity=Severity.LOW,
            )

    def test_serialization_round_trip(self) -> None:
        finding = Finding(
            finding_id="FIND-006",
            title="Round Trip Test",
            description="Testing serialization",
            source_category=SourceCategory.GOOGLE_DEEPMIND,
            relevance_score=0.72,
            severity=Severity.MEDIUM,
            metadata={"source_url": "https://example.com"},
        )
        dumped = finding.model_dump(mode="json")
        restored = Finding.model_validate(dumped)
        assert restored.finding_id == finding.finding_id
        assert restored.source_category == finding.source_category
        assert restored.metadata == finding.metadata

    def test_json_round_trip(self) -> None:
        finding = Finding(
            finding_id="FIND-007",
            title="JSON Test",
            description="Testing JSON",
            source_category=SourceCategory.META_FAIR,
            relevance_score=0.5,
            severity=Severity.LOW,
        )
        json_str = finding.model_dump_json()
        restored = Finding.model_validate_json(json_str)
        assert restored == finding

    def test_default_metadata_is_empty_dict(self) -> None:
        finding = Finding(
            finding_id="FIND-008",
            title="Default Metadata",
            description="Testing defaults",
            source_category=SourceCategory.INTERNAL,
            relevance_score=0.5,
            severity=Severity.LOW,
        )
        assert finding.metadata == {}

    def test_created_at_auto_populated(self) -> None:
        finding = Finding(
            finding_id="FIND-009",
            title="Timestamp Test",
            description="Testing auto timestamp",
            source_category=SourceCategory.INTERNAL,
            relevance_score=0.5,
            severity=Severity.LOW,
        )
        assert finding.created_at is not None
        assert finding.created_at.tzinfo is not None


class TestFindingFixtures:
    """Test against fixture files."""

    def test_valid_fixture(self) -> None:
        fixture_path = FIXTURES_DIR / "finding_valid.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            finding = Finding.model_validate(data)
            assert finding.finding_id is not None

    def test_invalid_score_fixture(self) -> None:
        fixture_path = FIXTURES_DIR / "finding_invalid_score.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            with pytest.raises(ValueError):
                Finding.model_validate(data)
