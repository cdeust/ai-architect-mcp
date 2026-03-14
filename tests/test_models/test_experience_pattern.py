"""Tests for ExperiencePattern and PatternType models."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_architect_mcp._models.experience_pattern import (
    ExperiencePattern,
    PatternType,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_experience_pattern_creation() -> None:
    """ExperiencePattern can be created with required fields."""
    pattern = ExperiencePattern(
        pattern_id="pat-001",
        pattern_type=PatternType.SUCCESS,
        description="Test pattern",
        stage_id=6,
    )
    assert pattern.pattern_id == "pat-001"
    assert pattern.initial_relevance == 1.0
    assert pattern.half_life_days == 30.0
    assert pattern.occurrence_count == 1


def test_decay_at_half_life() -> None:
    """At exactly half_life_days, relevance should be ~50% of initial."""
    now = datetime.now(timezone.utc)
    half_life = 30.0
    created = now - timedelta(days=half_life)
    pattern = ExperiencePattern(
        pattern_id="pat-decay",
        pattern_type=PatternType.SUCCESS,
        description="Decay test",
        stage_id=1,
        initial_relevance=1.0,
        half_life_days=half_life,
        last_seen_at=created,
        created_at=created,
    )
    relevance = pattern.current_relevance(now)
    assert abs(relevance - 0.5) < 0.01, f"Expected ~0.5, got {relevance}"


def test_decay_at_zero_elapsed() -> None:
    """With zero elapsed time, relevance equals initial_relevance."""
    now = datetime.now(timezone.utc)
    pattern = ExperiencePattern(
        pattern_id="pat-zero",
        pattern_type=PatternType.OPTIMIZATION,
        description="Zero decay test",
        stage_id=4,
        initial_relevance=0.8,
        last_seen_at=now,
        created_at=now,
    )
    relevance = pattern.current_relevance(now)
    assert abs(relevance - 0.8) < 0.001


def test_decay_at_two_half_lives() -> None:
    """At two half-lives, relevance should be ~25% of initial."""
    now = datetime.now(timezone.utc)
    half_life = 20.0
    created = now - timedelta(days=half_life * 2)
    pattern = ExperiencePattern(
        pattern_id="pat-double",
        pattern_type=PatternType.FAILURE,
        description="Double half-life test",
        stage_id=7,
        initial_relevance=1.0,
        half_life_days=half_life,
        last_seen_at=created,
        created_at=created,
    )
    relevance = pattern.current_relevance(now)
    assert abs(relevance - 0.25) < 0.01


def test_reinforce_increments_count() -> None:
    """reinforce() increments occurrence_count by 1."""
    pattern = ExperiencePattern(
        pattern_id="pat-reinforce",
        pattern_type=PatternType.SUCCESS,
        description="Reinforce test",
        stage_id=3,
        occurrence_count=2,
    )
    reinforced = pattern.reinforce()
    assert reinforced.occurrence_count == 3
    assert reinforced.pattern_id == pattern.pattern_id


def test_reinforce_boosts_relevance() -> None:
    """reinforce() boosts initial_relevance."""
    pattern = ExperiencePattern(
        pattern_id="pat-boost",
        pattern_type=PatternType.SUCCESS,
        description="Boost test",
        stage_id=5,
        initial_relevance=0.5,
        occurrence_count=1,
    )
    reinforced = pattern.reinforce()
    assert reinforced.initial_relevance > pattern.initial_relevance


def test_reinforce_caps_at_one() -> None:
    """reinforce() never exceeds 1.0 relevance."""
    pattern = ExperiencePattern(
        pattern_id="pat-cap",
        pattern_type=PatternType.SUCCESS,
        description="Cap test",
        stage_id=2,
        initial_relevance=0.99,
        occurrence_count=10,
    )
    reinforced = pattern.reinforce()
    assert reinforced.initial_relevance <= 1.0


def test_fixture_round_trip() -> None:
    """Patterns from fixture file round-trip through model."""
    raw = json.loads((FIXTURES / "experience_decay_patterns.json").read_text())
    patterns = [ExperiencePattern.model_validate(item) for item in raw]
    assert len(patterns) == 3
    assert patterns[0].pattern_id == "pat-recent"


def test_pattern_type_values() -> None:
    """PatternType has all expected values."""
    expected = {"success", "failure", "optimization", "regression", "anomaly"}
    actual = {t.value for t in PatternType}
    assert actual == expected
