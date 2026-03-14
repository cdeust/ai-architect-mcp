# Epic 2: Acceptance Criteria

**Status:** Draft
**Date:** 2026-03-14
**Epic ID:** EPIC-E2

---

## AC-E2-001: PipelineState Model Creation

**Story:** S1 (PipelineState Model)
**Related FR:** FR-E2-001, FR-E2-002, FR-E2-003

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Model instantiation** | Valid field values (session_id, agent_id, current_stage) | Create `PipelineState(...)` instance | Instance has all typed fields, no validation errors | Type validation passes |
| **Default status** | No status field provided | Construct PipelineState | status defaults to IDLE | Enum value = PipelineStatus.IDLE |
| **Status transition** | PipelineState with status=IDLE | Call `set_status(PipelineStatus.RUNNING)` | status field changes to RUNNING, `updated_at` refreshes | ≤1ms latency, updated_at is fresh |
| **JSON serialization** | Valid PipelineState instance | Call `.model_dump_json()` | Returns valid JSON string with all public fields | JSON parseable, roundtrip loss = 0 |
| **JSON deserialization** | JSON string from previous serialization | Call `PipelineState.model_validate_json(json_str)` | Reconstructs equivalent PipelineState | Instance fields match original |

---

## AC-E2-002: PipelineState Skill Versions

**Story:** S1
**Related FR:** FR-E2-001

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Skill version tracking** | PipelineState with empty skill_versions | Set skill_versions={'skill_a': '1.0', 'skill_b': '2.1'} | skill_versions dict populated | Dict keys match inputs |
| **Version lookup** | skill_versions = {'analyze_domain': '1.5'} | Access instance.skill_versions['analyze_domain'] | Returns '1.5' | String value correct |
| **Empty case** | No skill_versions provided on construction | Check default value | skill_versions is empty dict {} | Type = dict, len = 0 |

---

## AC-E2-005: ExperiencePattern Model Creation

**Story:** S2 (ExperiencePattern + Decay)
**Related FR:** FR-E2-004, FR-E2-005

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Pattern instantiation** | Valid fields (pattern_type, description, initial_relevance, half_life_days) | Create `ExperiencePattern(...)` | Instance created with all typed fields | No validation errors |
| **PatternType enum** | ExperiencePattern constructor | Create with pattern_type=PatternType.ARCHITECTURAL | Enum value accepted | Value in enum member list |
| **Relevance bounds** | Setting initial_relevance | Try values 0.0, 0.5, 1.0 | All accepted; values outside [0.0-1.0] rejected | Validation enforces range |
| **Half-life positive** | Setting half_life_days | Try values 1, 30, 365 | All accepted; ≤0 values rejected | Validation enforces ge=1 |
| **Defaults on creation** | No reinforcement_count or timestamps provided | Construct ExperiencePattern | created_at and last_reinforced_at set to now(), reinforcement_count=0 | Timestamps UTC, count=0 |

---

## AC-E2-006: ExperiencePattern Decay Calculation

**Story:** S2
**Related FR:** FR-E2-006

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Decay at half-life** | Pattern created 14 days ago, half_life_days=14, initial_relevance=1.0 | Call `current_relevance()` (as_of now) | Returns 0.5 ± 1% (i.e., [0.495, 0.505]) | Accuracy within tolerance |
| **Fresh pattern** | Pattern created <1 hour ago | Call `current_relevance()` | Returns ≥0.99 × initial_relevance | Variance minimal for recent |
| **Double half-life decay** | Pattern created 28 days ago, half_life_days=14, initial_relevance=1.0 | Call `current_relevance()` | Returns ~0.25 (0.5^2) | Decay squared as expected |
| **Negative elapsed (future reference)** | Pattern created tomorrow, reference date=today | Call `current_relevance(as_of=today)` | Returns initial_relevance (not future-decayed) | Clamps to no decay |
| **Long decay (t >> half-life)** | Pattern created 365 days ago, half_life_days=30, initial_relevance=1.0 | Call `current_relevance()` | Returns ≈0.00001 (highly decayed) | Near-zero but not NaN |

---

## AC-E2-007: ExperiencePattern Reinforcement

**Story:** S2
**Related FR:** FR-E2-007

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Reinforcement count increment** | Pattern with reinforcement_count=0 | Call `reinforce()` | reinforcement_count becomes 1 | Count incremented by 1 |
| **Multiple reinforcements** | Pattern reinforced 3 times total | Call `reinforce()` 3 times | reinforcement_count = 3 | All increments applied |
| **Relevance boost factor** | Pattern with initial_relevance=0.6, reinforcement_count=0 | Call `reinforce()` | initial_relevance becomes 0.6 × (1 + 0×0.05) = 0.6 on 1st call, then ≈0.63 on 2nd | Boost = (1 + count×0.05) |
| **Double reinforcement boost** | Start with initial_relevance=1.0, reinforce_count=0 | Call `reinforce()` twice | After 1st: 1.0×1.05=1.05 clamped to 1.0; After 2nd: still 1.0 (capped) | Boost clamped at 1.0 |
| **Reinforcement timestamp update** | last_reinforced_at = T0 | Call `reinforce()` at T1 (T1 > T0) | last_reinforced_at updated to T1 | Timestamp differs |

---

## AC-E2-008: AuditEvent Creation

**Story:** S3 (AuditEvent Immutable)
**Related FR:** FR-E2-008, FR-E2-009

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Event creation** | Valid fields (agent_id, action, outcome, duration_ms) | Create `AuditEvent(...)` | Instance created with all fields | No validation errors |
| **AuditOutcome enum** | AuditEvent constructor | Create with outcome=AuditOutcome.SUCCESS | Enum value accepted | Value in enum |
| **Default timestamp** | No timestamp provided | Create AuditEvent | timestamp set to current UTC time | time.utcnow() applied |
| **Event ID generation** | No event_id provided | Create AuditEvent | event_id auto-generated (UUID4) | UUID is valid |
| **Context snapshot empty case** | No context_snapshot provided | Create AuditEvent | context_snapshot defaults to {} | Dict is empty |

---

## AC-E2-010: AuditEvent Immutability

**Story:** S3
**Related FR:** FR-E2-010

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Frozen model configuration** | AuditEvent instance created | Try to modify any field (e.g., event.timestamp = new_time) | Raises FrozenInstanceError or ValidationError | Exception raised immediately |
| **No attribute deletion** | AuditEvent instance created | Try to delete field via del event.outcome | Raises AttributeError or FrozenInstanceError | Exception raised |
| **No __setattr__ bypass** | AuditEvent instance created | Try object.__setattr__(event, 'outcome', ...) | Still raises or prevents mutation | Immutability enforced |

---

## AC-E2-011: AuditQuery Filtering

**Story:** S3
**Related FR:** FR-E2-011

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Query creation** | Various filters | Create `AuditQuery(agent_id_filter='agent1', outcome_filter=AuditOutcome.FAILURE)` | Query instance created | No validation errors |
| **Optional filters** | No filters provided | Create AuditQuery() | All filter fields None, limit=1000 | Defaults applied |
| **Timestamp range** | Range from T1 to T2 | Create with timestamp_range=(T1, T2) | Range stored as tuple | tuple(datetime, datetime) |

---

## AC-E2-012: PipelineStatePort Interface

**Story:** S4 (Memory Adapter Ports)
**Related FR:** FR-E2-012

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Port is ABC** | PipelineStatePort imported | Check `isinstance(PipelineStatePort, ABCMeta)` | True | Type check passes |
| **Three abstract methods** | PipelineStatePort source | Inspect methods | load, save, delete all marked @abstractmethod | Method count = 3 |
| **Async signatures** | Method definitions | Check each method signature | All are async def | Keyword 'async' in source |
| **Cannot instantiate** | PipelineStatePort ABC | Try to instantiate directly: `PipelineStatePort()` | Raises TypeError (abstract) | Exception raised |
| **Subclass enforcement** | Create dummy subclass without implementing all methods | Try to instantiate | Raises TypeError | Unimplemented methods block creation |

---

## AC-E2-013: ExperiencePort and AuditPort Interfaces

**Story:** S4
**Related FR:** FR-E2-013, FR-E2-014

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **ExperiencePort methods** | ExperiencePort source | Inspect method list | list_patterns, save_pattern, get_pattern, query_by_type all present | Method count = 4 |
| **AuditPort methods** | AuditPort source | Inspect method list | append_event, query_events only (NO update/delete) | Method count = 2 |
| **Method argument types** | ExperiencePort.list_patterns signature | Use inspect.signature() | Parameter min_relevance has default=0.0 and type hint float | Signature correct |

---

## AC-E2-020: CloudKit Adapter Local Write

**Story:** S5 (CloudKit Adapter for PipelineState)
**Related FR:** FR-E2-015, FR-E2-020

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Offline write succeeds** | CloudKit unavailable/offline | Call `adapter.save(state)` | Returns immediately without error | Latency ≤100ms |
| **Local storage updated** | Call save() when offline | Then call `adapter.load(session_id)` | Returns saved state | Data persisted locally |
| **Async CloudKit push queued** | Save called | Wait 1s, inspect adapter's sync queue | Event enqueued for CloudKit push | Sync scheduled |

---

## AC-E2-021: CloudKit Adapter Fallback to Local

**Story:** S5
**Related FR:** FR-E2-015, FR-E2-020

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Load when CloudKit unavailable** | CloudKit offline, state in local store | Call `adapter.load(session_id)` | Returns local copy | Data retrieved |
| **CloudKit-first, then fallback** | State exists in both CloudKit and local | Call `adapter.load(session_id)` | Attempts CloudKit first, falls back to local on error | Preference order correct |

---

## AC-E2-025: Conflict Resolution Winner Selection

**Story:** S8 (Conflict Resolution)
**Related FR:** FR-E2-018, FR-E2-019

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Timestamp comparison** | Device A edit at 10:00:00Z, Device B at 10:00:01Z | Conflict detected | Device B record (later timestamp) becomes canonical | Last-writer-wins applied |
| **Same timestamp tiebreaker** | Both devices edit at exact 10:00:00Z, agent_ids='agent1' and 'agent2' | Conflict detected | 'agent2' > 'agent1' lexicographically, agent2 record wins | Deterministic tiebreaker |
| **Conflict determinism** | Same two records with same metadata, run resolution 100 times | Compare results | All 100 runs produce same winner | No randomness |

---

## AC-E2-026: Conflict Logging

**Story:** S8
**Related FR:** FR-E2-018

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Audit event on conflict** | Conflict detected and resolved | Inspect audit trail | AuditEvent with outcome=PARTIAL and metadata showing both record versions | Conflict fully logged |
| **Conflict metadata completeness** | Audit entry for conflict | Check metadata field | Includes losing record's values and why it lost | Audit enables debugging |

---

## AC-E2-030: Progressive Disclosure L1 Rendering

**Story:** S9 (Progressive Disclosure Engine)
**Related FR:** FR-E2-023

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **L1 minimal content** | 10 findings with keys and pattern types | Call `disclosure.render(findings, L1)` | Output contains only "- key (type)" lines | No descriptions included |
| **L1 token count** | L1 rendered output | Check token estimate | ≤500 tokens | Constraint met |
| **L1 parsing** | L1 output | Parse as structured list | Each line is "- key (type)" format | Format consistent |

---

## AC-E2-031: Progressive Disclosure L2 Rendering

**Story:** S9
**Related FR:** FR-E2-023

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **L2 with summaries** | 10 findings with summaries | Call `disclosure.render(findings, L2)` | Output is "- key (type): summary" format | Summaries included |
| **L2 summary truncation** | Finding with 500-char summary | Render at L2 | Summary truncated to ~100 chars + "..." | Prevents unbounded growth |
| **L2 token count** | L2 rendered output | Check token estimate | ~300 tokens (more concise than L3) | Token budget met |

---

## AC-E2-032: Progressive Disclosure L3 Rendering

**Story:** S9
**Related FR:** FR-E2-023

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **L3 full JSON** | 10 findings | Call `disclosure.render(findings, L3)` | Output is valid JSON with all fields | JSON parseable, complete |
| **L3 token count** | L3 rendered output | Check token estimate | ≤3000 tokens | Full context constraint |
| **L3 default behavior** | Call render without level param | Default to L3 | Full JSON returned | L3 is default |

---

## AC-E2-035: Budget Monitor 70% Threshold

**Story:** S10 (Context Budget Monitor)
**Related FR:** FR-E2-025, FR-E2-026

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **70% warning trigger** | Context utilization = 70% | Call `monitor.check_and_downgrade(context, max_tokens)` | Returns (L2, False, warning_msg) | Threshold exact at 70% |
| **Below 70% no warning** | Context utilization = 69% | Call `check_and_downgrade()` | Returns (L3, False, None) | No warning <70% |
| **Warning message** | Utilization 70%+ | Check returned alert_message | Message contains "WARNING" and percentage | Message informative |

---

## AC-E2-036: Budget Monitor 93% Threshold

**Story:** S10
**Related FR:** FR-E2-025, FR-E2-027

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **93% critical trigger** | Context utilization = 93% | Call `monitor.check_and_downgrade()` | Returns (L3, True, critical_msg) | Threshold exact at 93% |
| **Auto-handoff flag** | 93% threshold hit | Check return value's trigger_handoff | Boolean is True | Handoff triggered |
| **Critical alert message** | Utilization 93%+ | Check alert_message | Message contains "CRITICAL" and "handoff" | Message clear |

---

## AC-E2-037: Budget Monitor Recalculation Speed

**Story:** S10
**Related FR:** FR-E2-025

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Large context set performance** | 1000 findings, max_tokens=5000 | Call `check_and_downgrade()` multiple times | Each call returns in ≤2s | Latency <2s |
| **Scaling to 10K patterns** | 10,000 items | Call check_and_downgrade() | Completes in <2s | Scales linearly |

---

## AC-E2-040: Auto-Handoff Document Generation

**Story:** S11 (Auto-Handoff Generation)
**Related FR:** FR-E2-028

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Handoff trigger at 93%** | Context utilization = 93% | Monitor detects threshold | `generate_handoff_document()` called automatically | Automation works |
| **Handoff document fields** | Auto-handoff generation | Inspect HandoffDocument | Contains: current_stage, active_finding, patterns reused, recommendations, context_snapshot | All fields present |
| **Markdown format** | HandoffDocument generated | Call `.to_markdown()` | Valid Markdown with headers and lists | Format correct |

---

## AC-E2-041: Handoff Completeness

**Story:** S11
**Related FR:** FR-E2-028

| Criterion | GIVEN | WHEN | THEN | KPI |
|-----------|-------|------|------|-----|
| **Next-step recommendations** | Handoff generation in progress | Check recommendations field | Contains actionable next steps | Content meaningful |
| **Current stage capture** | Session at stage 5 | Generate handoff | Handoff captures stage=5 | State preserved |
| **Active finding context** | Session with active_finding = UUID-X | Generate handoff | Handoff includes active finding + its status | Context complete |

---

## Summary by Story

| Story | Total ACs | AC Range |
|-------|-----------|----------|
| S1 | 5 | AC-E2-001 to AC-E2-002 |
| S2 | 4 | AC-E2-005 to AC-E2-007 |
| S3 | 5 | AC-E2-008 to AC-E2-011 |
| S4 | 3 | AC-E2-012 to AC-E2-013 |
| S5 | 2 | AC-E2-020 to AC-E2-021 |
| S8 | 3 | AC-E2-025 to AC-E2-026 |
| S9 | 3 | AC-E2-030 to AC-E2-032 |
| S10 | 3 | AC-E2-035 to AC-E2-037 |
| S11 | 2 | AC-E2-040 to AC-E2-041 |
| **Total** | **30+ ACs** | **AC-E2-001 through AC-E2-041** |

