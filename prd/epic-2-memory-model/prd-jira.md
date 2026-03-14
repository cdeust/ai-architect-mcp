# Epic 2: JIRA Tickets & Project Plan

**Status:** Draft
**Date:** 2026-03-14
**Epic ID:** EPIC-E2
**Total Tickets:** 20+ (stories + tasks)

---

## Epic Summary

| Field | Value |
|-------|-------|
| **Epic Key** | EPIC-E2 |
| **Title** | Four-Layer Memory Model with CloudKit Sync |
| **Description** | Implement Session, Project, Experience, Analytics memory layers; CloudKit sync; progressive disclosure; context budget monitoring |
| **Status** | To Do |
| **Story Points** | 76 |
| **Priority** | High |
| **Component** | ai-architect / memory |
| **Labels** | epic, memory, cloudkit, storage |
| **Sprint** | Epic (spans S0-S5) |

---

## JIRA Ticket Breakdown

### Sprint 0: CloudKit Prototype

**E2-01: CloudKit Zone Setup & CRUD Prototype**
- **Type:** Task
- **Story Points:** 5
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S0
- **Assignee:** Tech Lead
- **Priority:** High
- **Description:**
  - Create CloudKit zone configuration for PipelineState record type
  - Implement basic CRUD (create, read, update in zone)
  - Write 1000 mock records and measure sync latency
  - Test conflict scenario: simultaneous edits from two "devices"
- **Acceptance Criteria:**
  - Zone created and accessible via CloudKit SDK
  - 1000 records sync in <2s on 95th percentile
  - Conflict resolution winner determined by timestamp + agent_id tiebreaker
- **Dependencies:** None
- **Blockers:** None
- **Testing Strategy:** Manual testing on iOS Simulator + real device (if available)
- **Documentation:** Store findings in ADR-008 (CloudKit Integration)

**Subtasks:**
- [ ] Setup CloudKit container + zone in Xcode project
- [ ] Write mock PipelineState record type
- [ ] Implement async CRUD methods
- [ ] Load test: 1000 records, measure latency
- [ ] Conflict test: timestamp-based resolution
- [ ] Document results in ADR

---

### Sprint 1: Domain Models

**E2-02: Implement PipelineState Model (Story S1)**
- **Type:** Story
- **Story Points:** 3
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S1
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement Pydantic v2 BaseModel for session-scoped agent execution state
- **Acceptance Criteria:** AC-E2-001, AC-E2-002
- **Dependencies:** Pydantic v2
- **Related FRs:** FR-E2-001, FR-E2-002, FR-E2-003

**Subtasks:**
- [ ] Define PipelineState model with all fields (session_id, current_stage, active_finding, agent_id, status, skill_versions, timestamps)
- [ ] Define PipelineStatus enum (IDLE, RUNNING, PAUSED, HANDOFF_PENDING, COMPLETED, FAILED)
- [ ] Implement set_status() and advance_stage() methods
- [ ] Implement model_dump_json() / model_validate_json()
- [ ] Write unit tests (model creation, status transitions, serialization)
- [ ] Docstring all public methods

---

**E2-03: Implement ExperiencePattern Model with Decay (Story S2)**
- **Type:** Story
- **Story Points:** 8
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S1
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement pattern model with half-life decay and reinforcement
- **Acceptance Criteria:** AC-E2-005, AC-E2-006, AC-E2-007
- **Dependencies:** Story S1 (pattern, PipelineState for tests)
- **Related FRs:** FR-E2-004, FR-E2-005, FR-E2-006, FR-E2-007

**Subtasks:**
- [ ] Define PatternType enum (5 variants: ARCHITECTURAL, DOMAIN_MODELING, NAMING, INTERFACE_DESIGN, REFINEMENT_HEURISTIC)
- [ ] Define ExperiencePattern model (pattern_id, pattern_type, description, initial_relevance, half_life_days, reinforcement_count, timestamps)
- [ ] Implement current_relevance() method: `relevance = initial_relevance × 0.5^(elapsed_days / half_life_days)`
- [ ] Implement reinforce() method: boost initial_relevance by (1 + reinforcement_count × 0.05)
- [ ] Unit tests: decay accuracy ±1% at half-life, reinforcement boost, edge cases (future dates, long decay)
- [ ] Benchmark: decay calc for 10K patterns <100ms
- [ ] Docstrings + comments on decay formula

---

**E2-04: Implement AuditEvent Immutable Model (Story S3)**
- **Type:** Story
- **Story Points:** 5
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S1
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement immutable audit event model (frozen=True) with append-only semantics
- **Acceptance Criteria:** AC-E2-008, AC-E2-010, AC-E2-011
- **Dependencies:** Story S1
- **Related FRs:** FR-E2-008, FR-E2-009, FR-E2-010, FR-E2-011

**Subtasks:**
- [ ] Define AuditOutcome enum (SUCCESS, FAILURE, PARTIAL, HANDOFF, VALIDATION_ERROR)
- [ ] Define AuditEvent model (event_id, timestamp, agent_id, action, outcome, context_snapshot, duration_ms, metadata) with frozen=True
- [ ] Define AuditQuery model (filters: agent_id, action, outcome, timestamp_range, limit)
- [ ] Unit tests: immutability enforcement (try to modify field, expect FrozenInstanceError)
- [ ] Unit tests: event creation, auto-generated event_id and timestamp
- [ ] Unit tests: AuditQuery structure
- [ ] Docstrings

---

### Sprint 2: Ports & Local Adapters

**E2-05: Define Memory Adapter Ports (Story S4)**
- **Type:** Story
- **Story Points:** 3
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S2
- **Assignee:** Tech Lead
- **Priority:** High
- **Description:** Define three async ABC ports for memory services
- **Acceptance Criteria:** AC-E2-012, AC-E2-013
- **Dependencies:** Stories S1, S2, S3
- **Related FRs:** FR-E2-012, FR-E2-013, FR-E2-014

**Subtasks:**
- [ ] Define PipelineStatePort ABC with async methods: load(session_id), save(state), delete(session_id)
- [ ] Define ExperiencePort ABC with async methods: list_patterns(min_relevance), save_pattern(pattern), get_pattern(pattern_id), query_by_type(pattern_type)
- [ ] Define AuditPort ABC with async methods: append_event(event), query_events(query) [NO update/delete]
- [ ] Add all ports to _adapters/ports.py
- [ ] Unit tests: verify ABCs cannot instantiate directly; verify @abstractmethod decorators
- [ ] Docstrings on all port methods

---

**E2-06: Implement Local Memory Adapters (Task)**
- **Type:** Task
- **Story Points:** 6 (unplanned, added to S2)
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S2
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement in-memory reference adapters for local development
- **Dependencies:** Story E2-05
- **Related FRs:** FR-E2-012, FR-E2-013, FR-E2-014

**Subtasks:**
- [ ] LocalPipelineStateAdapter: in-memory dict + optional SQLite
- [ ] LocalExperienceAdapter: in-memory list with filtering
- [ ] LocalAuditAdapter: append-only list
- [ ] Unit tests: all port methods work correctly
- [ ] Integration tests: with CompositionRoot injection

---

**E2-07: Update CompositionRoot for Memory Services (Story S12)**
- **Type:** Story
- **Story Points:** 2
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S2
- **Assignee:** Tech Lead
- **Priority:** High
- **Description:** Add memory service port injection to CompositionRoot
- **Acceptance Criteria:** AC-E2-012 (port injection), and additional ACs for root initialization
- **Dependencies:** Story E2-05
- **Related FRs:** FR-E2-029, FR-E2-030

**Subtasks:**
- [ ] Add async initialize_async() hook to CompositionRoot
- [ ] Add get_pipeline_state_port(), get_experience_port(), get_audit_port() accessors
- [ ] Implement environment-based port selection (local vs cloudkit)
- [ ] Unit tests: port injection works, lazy loading, error on uninitialized
- [ ] Integration tests: with local adapters

---

### Sprint 3: CloudKit Adapters & Conflict Resolution

**E2-08: CloudKit Adapter for PipelineState (Story S5)**
- **Type:** Story
- **Story Points:** 8
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S3
- **Assignee:** Tech Lead
- **Priority:** High
- **Description:** Implement CloudKit adapter for PipelineState (offline-first)
- **Acceptance Criteria:** AC-E2-020, AC-E2-021
- **Dependencies:** Story E2-05, Task E2-06, Sprint S0 prototype
- **Related FRs:** FR-E2-015, FR-E2-018, FR-E2-020

**Subtasks:**
- [ ] Create CloudKitPipelineStateAdapter class implementing PipelineStatePort
- [ ] Add CloudKit record type "PipelineState" with fields + metadata (last_modified_by, last_modified_at)
- [ ] Implement save(): write to local store first (<100ms), queue async CloudKit push
- [ ] Implement load(): fetch from CloudKit if available, else fallback to local
- [ ] Implement delete(): remove from local + queue CloudKit delete
- [ ] Unit tests: offline write latency, local fallback
- [ ] Integration tests: sync queue processing, CloudKit roundtrip
- [ ] Docstrings

---

**E2-09: CloudKit Adapter for Experience Patterns (Story S6)**
- **Type:** Story
- **Story Points:** 8
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S3
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement CloudKit adapter for ExperiencePattern persistence
- **Acceptance Criteria:** AC-E2-020, AC-E2-021 (adapted for patterns)
- **Dependencies:** Story E2-05, Task E2-06, E2-08
- **Related FRs:** FR-E2-016, FR-E2-020

**Subtasks:**
- [ ] Create CloudKitExperienceAdapter class implementing ExperiencePort
- [ ] Implement list_patterns(): bulk fetch from CloudKit + client-side filtering
- [ ] Implement save_pattern(): write to local + async CloudKit
- [ ] Implement get_pattern(): CloudKit-first, fallback to local
- [ ] Implement query_by_type(): CloudKit predicate query or client-side filtering
- [ ] Unit tests: filtering accuracy, sync metadata (last_reinforced_at, reinforcement_count)
- [ ] Integration tests: pattern reinforcement syncs to another device
- [ ] Docstrings

---

**E2-10: CloudKit Adapter for AuditEvent (Story S7)**
- **Type:** Story
- **Story Points:** 5
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S3
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement CloudKit adapter for audit trail (append-only)
- **Acceptance Criteria:** AC-E2-020, AC-E2-021 (adapted for audit)
- **Dependencies:** Story E2-05, Task E2-06, E2-08
- **Related FRs:** FR-E2-017, FR-E2-020

**Subtasks:**
- [ ] Create CloudKitAuditAdapter class implementing AuditPort
- [ ] Implement append_event(): write to local + async CloudKit (enforce append-only)
- [ ] Implement query_events(): filter by agent_id, action, outcome, timestamp range
- [ ] Unit tests: append correctness, no update/delete allowed
- [ ] Integration tests: audit events propagate to other devices
- [ ] Docstrings

---

**E2-11: Implement Conflict Resolution (Story S8)**
- **Type:** Story
- **Story Points:** 5
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S3
- **Assignee:** Tech Lead
- **Priority:** High
- **Description:** Implement last-writer-wins conflict resolution for CloudKit syncs
- **Acceptance Criteria:** AC-E2-025, AC-E2-026
- **Dependencies:** Stories E2-08, E2-09, E2-10
- **Related FRs:** FR-E2-018, FR-E2-019

**Subtasks:**
- [ ] Implement resolve_conflict() function: compare last_modified_at timestamps
- [ ] Implement tiebreaker: lexicographic comparison of last_modified_by (agent_id)
- [ ] Integrate resolver into all three CloudKit adapters (PipelineState, Experience, Audit)
- [ ] Log all conflicts to AuditEvent with outcome=PARTIAL + metadata showing both versions
- [ ] Unit tests: timestamp-based winner selection
- [ ] Determinism tests: 100 concurrent conflict scenarios, identical winner each time
- [ ] Docstrings + comments on algorithm

---

### Sprint 4: Progressive Disclosure & Budget Monitoring

**E2-12: Progressive Disclosure Engine (Story S9)**
- **Type:** Story
- **Story Points:** 8
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S4
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement 3-level progressive disclosure for context budget optimization
- **Acceptance Criteria:** AC-E2-030, AC-E2-031, AC-E2-032
- **Dependencies:** Stories S1, S2
- **Related FRs:** FR-E2-021, FR-E2-023, FR-E2-024

**Subtasks:**
- [ ] Define DisclosureLevel enum (L1, L2, L3)
- [ ] Create ProgressiveDisclosure class with render() method
- [ ] Implement _render_l1(): keys + pattern types only (~500 tokens)
- [ ] Implement _render_l2(): keys + types + truncated summaries (~300 tokens, more concise)
- [ ] Implement _render_l3(): full JSON (~3000 tokens)
- [ ] Implement calculate_token_count(): heuristic (4 chars/token) or tiktoken integration
- [ ] Unit tests: token count accuracy (±2%), rendering correctness
- [ ] Performance: rendering <200ms
- [ ] Docstrings

---

**E2-13: Context Budget Monitor (Story S10)**
- **Type:** Story
- **Story Points:** 5
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S4
- **Assignee:** Backend Engineer
- **Priority:** High
- **Description:** Implement context budget monitor with 70%/93% thresholds
- **Acceptance Criteria:** AC-E2-035, AC-E2-036, AC-E2-037
- **Dependencies:** Story E2-12
- **Related FRs:** FR-E2-022, FR-E2-025, FR-E2-026, FR-E2-027

**Subtasks:**
- [ ] Create ContextBudget class (total_tokens, used_tokens, utilization_percent(), remaining_tokens())
- [ ] Create ContextBudgetMonitor class with check_and_downgrade() method
- [ ] Implement 70% threshold logic: return (L2, False, warning_msg)
- [ ] Implement 93% threshold logic: return (L3, True, critical_msg)
- [ ] Unit tests: threshold accuracy ±1%, sub-70% no warning, 70% warning, 93% critical
- [ ] Performance: check_and_downgrade() <2s for 10K items
- [ ] Docstrings

---

**E2-14: Auto-Handoff Generation (Story S11)**
- **Type:** Story
- **Story Points:** 3
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S4
- **Assignee:** Backend Engineer
- **Priority:** Medium
- **Description:** Auto-generate HandoffDocument when 93% budget threshold hit
- **Acceptance Criteria:** AC-E2-040, AC-E2-041
- **Dependencies:** Story E2-13
- **Related FRs:** FR-E2-028

**Subtasks:**
- [ ] Implement generate_handoff_document(session: PipelineState, findings: List[Finding], budget: ContextBudget) → HandoffDocument
- [ ] Capture: current_stage, active_finding + status, patterns reused, recommendations, context_snapshot
- [ ] Hook into ContextBudgetMonitor: when 93% threshold triggered, auto-call generate_handoff_document()
- [ ] Unit tests: handoff document completeness, Markdown output validation
- [ ] Integration tests: handoff triggers at exact 93% (not before)
- [ ] Docstrings

---

### Sprint 5: Integration Tests & Documentation

**E2-15: Cross-Device Integration Tests (Story S13)**
- **Type:** Story
- **Story Points:** 8
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S5
- **Assignee:** Backend Engineer + AI (test generation)
- **Priority:** High
- **Description:** End-to-end integration tests for multi-device CloudKit sync
- **Acceptance Criteria:** AC-E2-020, AC-E2-021 (integration level), AC-E2-025, AC-E2-026
- **Dependencies:** All CloudKit adapter stories (E2-08 through E2-11)
- **Related FRs:** All FRs

**Subtasks:**
- [ ] Setup pytest with mock CloudKit backend (or real CloudKit test zone)
- [ ] Test 1: Save on Device A, load on Device B after sync → data matches
- [ ] Test 2: Concurrent edits on A and B, conflict resolved → deterministic winner
- [ ] Test 3: Pattern reinforced on A, queried on B → updated metadata visible
- [ ] Test 4: Audit events logged on A, queried from B → all events present and ordered
- [ ] Test 5: Offline on A, write 10 events, reconnect → queue flushed, all events in CloudKit
- [ ] Determinism: Run all concurrent tests 100×, verify zero flakiness
- [ ] Docstrings + test comments

---

**E2-16: Full Test Suite & API Documentation (Story S14)**
- **Type:** Story
- **Story Points:** 5
- **Status:** To Do
- **Epic Link:** EPIC-E2
- **Sprint:** S5
- **Assignee:** Backend Engineer + AI (test generation + coverage analysis)
- **Priority:** High
- **Description:** Complete test suite with ≥85% coverage + comprehensive API docs
- **Acceptance Criteria:** AC-E2-001 through AC-E2-041 all verified
- **Dependencies:** All previous stories

**Subtasks:**
- [ ] Test file: test_pipeline_state.py (instantiation, status, serialization)
- [ ] Test file: test_experience_pattern.py (decay, reinforcement, edge cases, 10K pattern benchmark)
- [ ] Test file: test_audit_event.py (immutability, creation, query)
- [ ] Test file: test_progressive_disclosure.py (L1/L2/L3, token counts, rendering <200ms)
- [ ] Test file: test_budget_monitor.py (70%/93% thresholds, <2s performance)
- [ ] Test file: test_cloudkit_sync.py (adapters, offline, conflict resolution)
- [ ] Run pytest --cov and verify ≥85% coverage for all non-test modules
- [ ] Add Google-style docstrings to ALL public methods
- [ ] Create ARCHITECTURE.md: explain four-layer model, CloudKit sync flow, decay formula, progressive disclosure algorithm
- [ ] Create TESTING.md: guide for running tests, CloudKit setup, determinism verification

---

## JIRA CSV Export

```csv
Key,Type,Status,Story Points,Epic Link,Sprint,Summary,Assignee,Priority
E2-01,Task,To Do,5,EPIC-E2,S0,CloudKit Zone Setup & CRUD Prototype,Tech Lead,High
E2-02,Story,To Do,3,EPIC-E2,S1,Implement PipelineState Model,Backend Engineer,High
E2-03,Story,To Do,8,EPIC-E2,S1,Implement ExperiencePattern with Decay,Backend Engineer,High
E2-04,Story,To Do,5,EPIC-E2,S1,Implement AuditEvent Immutable Model,Backend Engineer,High
E2-05,Story,To Do,3,EPIC-E2,S2,Define Memory Adapter Ports,Tech Lead,High
E2-06,Task,To Do,6,EPIC-E2,S2,Implement Local Memory Adapters,Backend Engineer,High
E2-07,Story,To Do,2,EPIC-E2,S2,Update CompositionRoot for Memory Services,Tech Lead,High
E2-08,Story,To Do,8,EPIC-E2,S3,CloudKit Adapter for PipelineState,Tech Lead,High
E2-09,Story,To Do,8,EPIC-E2,S3,CloudKit Adapter for Experience Patterns,Backend Engineer,High
E2-10,Story,To Do,5,EPIC-E2,S3,CloudKit Adapter for AuditEvent,Backend Engineer,High
E2-11,Story,To Do,5,EPIC-E2,S3,Implement Conflict Resolution,Tech Lead,High
E2-12,Story,To Do,8,EPIC-E2,S4,Progressive Disclosure Engine,Backend Engineer,High
E2-13,Story,To Do,5,EPIC-E2,S4,Context Budget Monitor,Backend Engineer,High
E2-14,Story,To Do,3,EPIC-E2,S4,Auto-Handoff Generation,Backend Engineer,Medium
E2-15,Story,To Do,8,EPIC-E2,S5,Cross-Device Integration Tests,Backend Engineer,High
E2-16,Story,To Do,5,EPIC-E2,S5,Full Test Suite & API Documentation,Backend Engineer,High
```

---

## Dependency Graph

```
E2-01 (CloudKit Prototype, S0)
    ↓ (validated)
E2-02 (PipelineState, S1) ← also feeds E2-03, E2-04
    ↓
E2-03 (ExperiencePattern, S1)
    ↓
E2-04 (AuditEvent, S1)
    ↓
E2-05 (Ports, S2)
    ↓
E2-06 (Local Adapters, S2)
    ↓
E2-07 (CompositionRoot, S2)
    ↓
E2-08 (PipelineState CloudKit, S3)
    ↓
E2-09 (Experience CloudKit, S3) ← parallel with E2-08
    ↓
E2-10 (Audit CloudKit, S3) ← parallel with E2-09
    ↓
E2-11 (Conflict Resolution, S3) ← uses all above adapters
    ↓
E2-12 (Disclosure, S4) ← can start parallel with E2-11 end
    ↓
E2-13 (Budget Monitor, S4) ← depends on E2-12
    ↓
E2-14 (Auto-Handoff, S4) ← depends on E2-13
    ↓
E2-15 (Integration Tests, S5) ← depends on all CloudKit adapters
    ↓
E2-16 (Full Test Suite, S5) ← depends on all stories
```

---

## Velocity & Release Planning

| Sprint | Total SP | Delivered | Velocity |
|--------|----------|-----------|----------|
| S0 | 5 | 5 | 5 |
| S1 | 16 | 16 | 16 |
| S2 | 11 | 11 | 11 |
| S3 | 16 | 16 | 16 |
| S4 | 13 | 13 | 13 |
| S5 | 8 | 8 | 8 |
| **Total** | **76** | **76** | **avg 13 SP/sprint** |

