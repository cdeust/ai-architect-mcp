"""Tests for research evidence database."""

from __future__ import annotations

from ai_architect_mcp._prompting.strategies.research_evidence import ResearchEvidenceDatabase


class TestResearchEvidence:
    def test_all_16_registered(self) -> None:
        db = ResearchEvidenceDatabase()
        assert len(db.get_all()) == 16

    def test_all_have_papers(self) -> None:
        db = ResearchEvidenceDatabase()
        for s in db.get_all():
            assert s.research_paper != ""
            assert s.research_institution != ""

    def test_tiers_valid(self) -> None:
        db = ResearchEvidenceDatabase()
        for s in db.get_all():
            assert 1 <= s.tier <= 4

    def test_tier_counts(self) -> None:
        db = ResearchEvidenceDatabase()
        assert len(db.get_by_tier(1)) == 6
        assert len(db.get_by_tier(2)) == 4
        assert len(db.get_by_tier(3)) == 3
        assert len(db.get_by_tier(4)) == 3

    def test_get_by_characteristic(self) -> None:
        db = ResearchEvidenceDatabase()
        math = db.get_by_characteristic("mathematical_reasoning")
        assert len(math) > 0

    def test_get_strategy_by_id(self) -> None:
        db = ResearchEvidenceDatabase()
        s = db.get_strategy("recursive_refinement")
        assert s.tier == 1
        assert s.weight == 1.0
