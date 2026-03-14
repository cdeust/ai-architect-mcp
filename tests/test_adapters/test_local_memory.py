"""Tests for local memory adapters — pipeline state, experience, audit."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ai_architect_mcp._adapters.local_audit import LocalAudit
from ai_architect_mcp._adapters.local_experience import LocalExperience
from ai_architect_mcp._adapters.local_pipeline_state import LocalPipelineState
from ai_architect_mcp._models.audit_event import AuditEvent, AuditOutcome, AuditQuery
from ai_architect_mcp._models.experience_pattern import ExperiencePattern, PatternType
from ai_architect_mcp._models.session_state import PipelineStatus, SessionState

FIXTURES = Path(__file__).parent.parent / "fixtures"


# --- Pipeline State ---


@pytest.mark.asyncio
async def test_pipeline_state_save_and_load(tmp_path: Path) -> None:
    """SessionState round-trips through JSON file."""
    adapter = LocalPipelineState(data_dir=tmp_path)
    state = SessionState(
        session_id="sess-rt",
        finding_id="FIND-001",
        current_stage=2,
        status=PipelineStatus.RUNNING,
        completed_stages=[0, 1],
    )
    await adapter.save(state)
    loaded = await adapter.load("sess-rt")
    assert loaded is not None
    assert loaded.session_id == "sess-rt"
    assert loaded.completed_stages == [0, 1]


@pytest.mark.asyncio
async def test_pipeline_state_load_missing(tmp_path: Path) -> None:
    """Loading a non-existent session returns None."""
    adapter = LocalPipelineState(data_dir=tmp_path)
    result = await adapter.load("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_pipeline_state_list_sessions(tmp_path: Path) -> None:
    """list_sessions returns saved session IDs."""
    adapter = LocalPipelineState(data_dir=tmp_path)
    for i in range(3):
        state = SessionState(
            session_id=f"sess-{i}",
            finding_id="FIND-001",
            current_stage=0,
            status=PipelineStatus.IDLE,
        )
        await adapter.save(state)
    sessions = await adapter.list_sessions(limit=10)
    assert len(sessions) == 3


@pytest.mark.asyncio
async def test_pipeline_state_overwrite(tmp_path: Path) -> None:
    """Saving the same session_id overwrites previous data."""
    adapter = LocalPipelineState(data_dir=tmp_path)
    state1 = SessionState(
        session_id="sess-ow",
        finding_id="FIND-001",
        current_stage=1,
        status=PipelineStatus.RUNNING,
    )
    await adapter.save(state1)
    state2 = SessionState(
        session_id="sess-ow",
        finding_id="FIND-001",
        current_stage=5,
        status=PipelineStatus.PAUSED,
    )
    await adapter.save(state2)
    loaded = await adapter.load("sess-ow")
    assert loaded is not None
    assert loaded.current_stage == 5
    assert loaded.status == PipelineStatus.PAUSED


# --- Experience Patterns ---


@pytest.mark.asyncio
async def test_experience_save_and_list(tmp_path: Path) -> None:
    """Patterns round-trip through JSON file."""
    adapter = LocalExperience(data_dir=tmp_path)
    pattern = ExperiencePattern(
        pattern_id="pat-001",
        pattern_type=PatternType.SUCCESS,
        description="Test pattern",
        stage_id=6,
    )
    await adapter.save(pattern)
    patterns = await adapter.list_patterns()
    assert len(patterns) == 1
    assert patterns[0].pattern_id == "pat-001"


@pytest.mark.asyncio
async def test_experience_decay_filtering(tmp_path: Path) -> None:
    """list_patterns filters by current relevance."""
    adapter = LocalExperience(data_dir=tmp_path)
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=365)

    fresh = ExperiencePattern(
        pattern_id="pat-fresh",
        pattern_type=PatternType.SUCCESS,
        description="Fresh",
        stage_id=1,
        last_seen_at=now,
        created_at=now,
    )
    stale = ExperiencePattern(
        pattern_id="pat-stale",
        pattern_type=PatternType.FAILURE,
        description="Stale",
        stage_id=2,
        last_seen_at=old,
        created_at=old,
        half_life_days=30.0,
    )
    await adapter.save(fresh)
    await adapter.save(stale)

    all_patterns = await adapter.list_patterns(min_relevance=0.0)
    assert len(all_patterns) == 2

    fresh_only = await adapter.list_patterns(min_relevance=0.5)
    assert len(fresh_only) == 1
    assert fresh_only[0].pattern_id == "pat-fresh"


@pytest.mark.asyncio
async def test_experience_stage_filter(tmp_path: Path) -> None:
    """list_patterns filters by stage_id."""
    adapter = LocalExperience(data_dir=tmp_path)
    for stage in [3, 5, 7]:
        await adapter.save(
            ExperiencePattern(
                pattern_id=f"pat-s{stage}",
                pattern_type=PatternType.SUCCESS,
                description=f"Stage {stage}",
                stage_id=stage,
            )
        )
    result = await adapter.list_patterns(stage_id=5)
    assert len(result) == 1
    assert result[0].stage_id == 5


@pytest.mark.asyncio
async def test_experience_reinforce(tmp_path: Path) -> None:
    """reinforce() increments count and boosts relevance."""
    adapter = LocalExperience(data_dir=tmp_path)
    pattern = ExperiencePattern(
        pattern_id="pat-reinf",
        pattern_type=PatternType.SUCCESS,
        description="Reinforce me",
        stage_id=4,
        initial_relevance=0.5,
        occurrence_count=1,
    )
    await adapter.save(pattern)
    reinforced = await adapter.reinforce("pat-reinf")
    assert reinforced.occurrence_count == 2
    assert reinforced.initial_relevance > 0.5


@pytest.mark.asyncio
async def test_experience_reinforce_missing(tmp_path: Path) -> None:
    """reinforce() raises KeyError for missing pattern."""
    adapter = LocalExperience(data_dir=tmp_path)
    with pytest.raises(KeyError):
        await adapter.reinforce("nonexistent")


# --- Audit Events ---


@pytest.mark.asyncio
async def test_audit_append_and_query(tmp_path: Path) -> None:
    """Events round-trip through JSONL file."""
    adapter = LocalAudit(data_dir=tmp_path)
    event = AuditEvent(
        event_id="evt-001",
        session_id="sess-001",
        stage_id=0,
        tool_name="test",
        outcome=AuditOutcome.PASS,
        message="Test event",
    )
    await adapter.append(event)
    results = await adapter.query(AuditQuery())
    assert len(results) == 1
    assert results[0].event_id == "evt-001"


@pytest.mark.asyncio
async def test_audit_append_only(tmp_path: Path) -> None:
    """Multiple appends add distinct events."""
    adapter = LocalAudit(data_dir=tmp_path)
    for i in range(3):
        await adapter.append(
            AuditEvent(
                event_id=f"evt-{i}",
                session_id="sess-001",
                stage_id=i,
                tool_name="test",
                outcome=AuditOutcome.PASS,
                message=f"Event {i}",
            )
        )
    results = await adapter.query(AuditQuery())
    assert len(results) == 3


@pytest.mark.asyncio
async def test_audit_query_filters(tmp_path: Path) -> None:
    """Query filters by session_id and outcome."""
    adapter = LocalAudit(data_dir=tmp_path)
    events_data = json.loads((FIXTURES / "audit_events_sample.json").read_text())
    for data in events_data:
        await adapter.append(AuditEvent.model_validate(data))

    sess1 = await adapter.query(AuditQuery(session_id="sess-001"))
    assert all(e.session_id == "sess-001" for e in sess1)
    assert len(sess1) == 4

    fails = await adapter.query(AuditQuery(outcome=AuditOutcome.FAIL))
    assert len(fails) == 1
    assert fails[0].event_id == "evt-003"


@pytest.mark.asyncio
async def test_audit_query_empty(tmp_path: Path) -> None:
    """Query on empty store returns empty list."""
    adapter = LocalAudit(data_dir=tmp_path)
    results = await adapter.query(AuditQuery())
    assert results == []
