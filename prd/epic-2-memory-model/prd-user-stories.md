# Epic 2: User Stories

**Status:** Draft
**Date:** 2026-03-14
**Epic ID:** EPIC-E2

---

## Story 1: PipelineState Model (3 SP)

**Title:** Implement PipelineState Pydantic model for session-scoped agent execution state

**As a** memory service architect
**I want** a strongly-typed PipelineState model
**So that** agents can persist and load execution checkpoints without type errors

**Description:**
Implement a Pydantic v2 BaseModel with fields: `session_id` (UUID), `current_stage` (int, 0-10), `active_finding` (Optional[UUID]), `agent_id` (str), `status` (PipelineStatus enum), `skill_versions` (Dict[str, str]), `created_at` (datetime), `updated_at` (datetime). Include `set_status()` method and serialization to/from JSON.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Model instantiation | Valid field values | Create PipelineState instance | Instance has all fields typed correctly | Type validation passes |
| 2 | Status transition | PipelineState in IDLE status | Call `set_status(RUNNING)` | status field updates to RUNNING, `updated_at` refreshes | ≤1ms latency |
| 3 | JSON serialization | Valid PipelineState instance | Call `.model_dump_json()` | JSON contains all fields, deserializable | Roundtrip loss = 0 bytes |

**Dependencies:** Pydantic v2 available

**Related FRs:** FR-E2-001, FR-E2-002, FR-E2-003

---

## Story 2: ExperiencePattern Model with Decay (8 SP)

**Title:** Implement ExperiencePattern with biological half-life decay calculation

**As a** synthesis engine designer
**I want** patterns to decay in relevance over time using half-life model
**So that** stale insights gradually fade without manual deletion

**Description:**
Implement ExperiencePattern Pydantic model with: `pattern_id` (UUID), `pattern_type` (PatternType enum), `description` (str), `initial_relevance` (float [0.0-1.0]), `half_life_days` (int), `created_at` (datetime), `last_reinforced_at` (datetime), `reinforcement_count` (int). Add `current_relevance()` method: `relevance = initial_relevance × 0.5^(elapsed_days / half_life_days)`. Add `reinforce()` method to boost relevance and update reinforcement metadata.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Decay accuracy | Pattern created 14 days ago, `half_life_days=14`, `initial_relevance=1.0` | Call `current_relevance()` | Returns ~0.5 (within ±1%) | Accuracy ≤1% |
| 2 | Decay calculation at t=0 | Fresh pattern | Call `current_relevance()` immediately after creation | Returns `initial_relevance` value | Variance <0.1% |
| 3 | Reinforcement boost | Pattern with `initial_relevance=0.6`, `reinforcement_count=0` | Call `reinforce()` twice | `reinforcement_count` becomes 2, `initial_relevance` becomes ~0.72 (1.1x factor) | Boost applied = (1 + 2×0.05) = 1.1 |
| 4 | Half-life edge case | Pattern at exactly half-life elapsed | Call `current_relevance()` | Returns initial_relevance × 0.5 | Exact match to formula |

**Dependencies:** Story 1 (domain models pattern)

**Related FRs:** FR-E2-004, FR-E2-005, FR-E2-006, FR-E2-007

---

## Story 3: AuditEvent Immutable Model (5 SP)

**Title:** Implement immutable AuditEvent model with append-only semantics

**As a** compliance officer
**I want** audit events to be frozen after creation
**So that** the audit trail cannot be tampered with or modified retroactively

**Description:**
Implement AuditEvent Pydantic model (frozen=True) with: `event_id` (UUID), `timestamp` (datetime, UTC), `agent_id` (str), `action` (str), `outcome` (AuditOutcome enum), `context_snapshot` (JSON), `duration_ms` (int), `metadata` (Dict[str, Any]). Define AuditOutcome enum: SUCCESS, FAILURE, PARTIAL, HANDOFF, VALIDATION_ERROR. No update/delete methods on AuditPort.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Immutability enforcement | AuditEvent instance created | Attempt to modify `timestamp` field | Raises FrozenInstanceError | Error raised in ≤1ms |
| 2 | Creation idempotence | Valid AuditEvent data | Create event twice with same data | Both instances have same `event_id` (deterministic) | SHA256(data) = deterministic |
| 3 | AuditPort restrictions | AuditPort interface defined | Check method signatures | Only `append_event()` and `query_events()` present; NO update/delete | Reflection confirms ≤2 methods |

**Dependencies:** Story 1

**Related FRs:** FR-E2-008, FR-E2-009, FR-E2-010, FR-E2-011, FR-E2-014

---

## Story 4: Memory Adapter Ports (3 SP)

**Title:** Define three async adapter ports for memory services

**As a** dependency injection architect
**I want** three abstract port interfaces (PipelineStatePort, ExperiencePort, AuditPort)
**So that** implementations can be swapped (local, CloudKit, etc.) without coupling

**Description:**
Define PipelineStatePort ABC with async methods: `load(session_id: str)`, `save(state: PipelineState)`, `delete(session_id: str)`. Define ExperiencePort ABC: `list_patterns(min_relevance: float = 0.0)`, `save_pattern(pattern: ExperiencePattern)`, `get_pattern(pattern_id: UUID)`, `query_by_type(pattern_type: PatternType)`. Define AuditPort ABC: `append_event(event: AuditEvent)`, `query_events(query: AuditQuery)`. All methods marked @abstractmethod, async.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Port abstraction | Ports module imported | Inspect PipelineStatePort, ExperiencePort, AuditPort | All are ABCs with @abstractmethod decorators | isinstance(port_class, ABCMeta) = True |
| 2 | Async signatures | Port methods examined | Check method definitions | All async; use @abstractmethod | Re.match(r'async def', method_src) for all |
| 3 | Method argument types | ExperiencePort.list_patterns() signature | Type hint inspection | Parameter `min_relevance` has default 0.0 | inspect.signature confirms default |

**Dependencies:** Story 1, Story 2, Story 3

**Related FRs:** FR-E2-012, FR-E2-013, FR-E2-014

---

## Story 5: CloudKit Adapter for PipelineState (8 SP)

**Title:** Implement CloudKit adapter wrapping PipelineState sync

**As a** cross-device architect
**I want** PipelineState to sync to CloudKit with last-writer-wins conflict resolution
**So that** users see consistent execution state across iOS, macOS, web

**Description:**
Implement PipelineStatePort adapter using SwiftData + CloudKit integration. Serialize PipelineState to CloudKit record type "PipelineState" with custom fields for conflict detection: `last_modified_by` (agent_id), `last_modified_at` (ISO timestamp). On load, fetch from CloudKit if available, else local store. On save, write to local store first, then async push to CloudKit. Implement last-writer-wins logic in the adapter.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Local write succeeds | CloudKit offline | Call `save(state)` | Returns immediately; local PipelineState updated | Latency ≤100ms |
| 2 | CloudKit async push | Local state saved | Wait 2s for background sync | CloudKit record created/updated with same data | Record appears in CloudKit zone |
| 3 | Load fallback to local | CloudKit unavailable | Call `load(session_id)` | Reads from local store, returns valid PipelineState | No exception raised |
| 4 | Conflict detection metadata | Two writes to same session on different devices | Compare records in CloudKit | Both have `last_modified_at` and `last_modified_by` set | Timestamps differ if edits concurrent |

**Dependencies:** Story 1, Story 4

**Related FRs:** FR-E2-015, FR-E2-018, FR-E2-020

---

## Story 6: CloudKit Adapter for Experience Patterns (8 SP)

**Title:** Implement CloudKit adapter for ExperiencePattern persistence and sync

**As a** learning system designer
**I want** patterns to persist to CloudKit and sync across devices
**So that** architectural insights accumulate and propagate system-wide

**Description:**
Implement ExperiencePort adapter with CloudKit integration. Support `list_patterns(min_relevance)` as bulk fetch with client-side filtering. Implement `save_pattern()` to write to local + async CloudKit. Implement `get_pattern()` and `query_by_type()` with CloudKit-first-then-local fallback. All pattern metadata syncs including `reinforcement_count` and `last_reinforced_at`.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Bulk list with filtering | 100 patterns in CloudKit, min_relevance=0.7 | Call `list_patterns(0.7)` | Returns only patterns with current_relevance ≥0.7 | Filtering accurate, count ≤100 |
| 2 | Reinforcement sync | Pattern reinforced on Device A | Wait for CloudKit sync, check on Device B | Device B sees updated `reinforcement_count` and `last_reinforced_at` | Sync latency <2s |
| 3 | Query by type | 50 ARCHITECTURAL patterns, 30 NAMING patterns | Call `query_by_type(ARCHITECTURAL)` | Returns exactly 50 patterns | Count verified by CloudKit query |
| 4 | Pattern save idempotence | Save same pattern twice with 10s delay | Both writes succeed | Second write updates `updated_at` only; `pattern_id` unchanged | Same record in CloudKit |

**Dependencies:** Story 2, Story 4

**Related FRs:** FR-E2-016, FR-E2-020

---

## Story 7: CloudKit Adapter for AuditEvent (5 SP)

**Title:** Implement CloudKit adapter for immutable append-only audit trail

**As a** compliance architect
**I want** audit events to persist to CloudKit as append-only records
**So that** the audit trail is durable, synced, and tamper-evident

**Description:**
Implement AuditPort adapter that enforces append-only semantics: `append_event()` writes to local store + async CloudKit. `query_events()` uses AuditQuery to filter by agent_id, action, outcome, timestamp range. NO update/delete operations at adapter or CloudKit level (delete operations are not exposed).

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Append-only enforcement | AuditPort adapter instantiated | Inspect method signatures | Only `append_event()` and `query_events()` present | Method count = 2 |
| 2 | Event persistence | Valid AuditEvent created | Call `append_event(event)` | Event written to local store + queued for CloudKit | Local query returns event immediately |
| 3 | Query filtering | 100 events in trail (various agents/outcomes) | Call `query_events(AuditQuery(agent_id='agent1', outcome=SUCCESS))` | Returns only events matching both filters | Filtering accuracy = 100% |
| 4 | Timestamp ordering | Query with timestamp range [T1, T2] | Results returned | Events ordered by ascending timestamp | Ordering verified by assertion |

**Dependencies:** Story 3, Story 4

**Related FRs:** FR-E2-017, FR-E2-020

---

## Story 8: Conflict Resolution (5 SP)

**Title:** Implement last-writer-wins conflict resolution for CloudKit syncs

**As a** sync architect
**I want** concurrent edits to same session/pattern to resolve deterministically
**So that** users don't lose edits due to sync conflicts

**Description:**
Implement conflict resolution strategy in CloudKit adapters: compare `last_modified_at` timestamps; record with most recent timestamp wins. When timestamps equal, use `last_modified_by` (agent_id) lexicographic order as tiebreaker. Log all conflicts to AuditEvent with outcome=PARTIAL. Ensure deterministic ordering: same inputs always produce same winner.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Timestamp-based winner selection | Device A edits at T1=10:00:00Z, Device B at T2=10:00:01Z | Conflict detected in CloudKit | Device B's record becomes canonical | `last_modified_at` comparison correct |
| 2 | Tiebreaker determinism | Both devices edit at exact same timestamp (T=10:00:00Z) | Conflict resolution runs | Lexicographically later agent_id wins (e.g., 'agent2' > 'agent1') | Tiebreaker applied; results match string comparison |
| 3 | Conflict logging | Conflict resolved between two records | Check audit trail | AuditEvent created with outcome=PARTIAL, metadata showing both versions | Audit trail has complete conflict info |

**Dependencies:** Story 5, Story 6, Story 7

**Related FRs:** FR-E2-018, FR-E2-019

---

## Story 9: Progressive Disclosure Engine (8 SP)

**Title:** Implement 3-level progressive disclosure for context budget optimization

**As a** context window optimizer
**I want** to render findings at 3 disclosure levels (L1: 500t, L2: 300t, L3: 3Kt)
**So that** context fits within agent's budget while preserving semantic meaning

**Description:**
Implement ProgressiveDisclosure class with `render(findings: List[Finding], level: DisclosureLevel) → str` method. L1: entity keys + pattern types only (~500 tokens). L2: keys + 1-sentence summaries (~300 tokens, more concise). L3: full JSON representation (~3000 tokens). Implement `calculate_token_count(rendered: str) → int` using tokenizer model (e.g., tiktoken for GPT-4). Define DisclosureLevel enum.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | L1 rendering | 10 findings, each with key + type | Call `render(findings, L1)` | Output contains only keys and PatternType enums; no descriptions | Token count ≤500 |
| 2 | L2 rendering | Same 10 findings | Call `render(findings, L2)` | Output contains keys, types, and 1-sentence summaries | Token count ≤300 (more concise) |
| 3 | L3 rendering | Same 10 findings | Call `render(findings, L3)` | Output is full JSON with all fields | Token count ≤3000 |
| 4 | Token counting accuracy | Rendered output at each level | Verify token count with actual tokenizer | Reported count matches tiktoken.encoding_for_model('gpt-4').encode() | Accuracy ±2% |

**Dependencies:** Story 1, Story 2

**Related FRs:** FR-E2-021, FR-E2-023, FR-E2-024

---

## Story 10: Context Budget Monitor (5 SP)

**Title:** Implement context budget monitor with 70%/93% thresholds

**As a** memory manager
**I want** the system to warn at 70% context usage and escalate at 93%
**So that** agents can gracefully degrade context before exhaustion

**Description:**
Implement ContextBudgetMonitor class with `check_and_downgrade(context: List[Finding], max_tokens: int) → Tuple[DisclosureLevel, bool, Optional[str]]` method. At ≥70% usage, recommend downgrading to L2 (summaries) and emit warning. At ≥93% usage, emit CRITICAL alert and return auto_handoff=True. Return recommended DisclosureLevel, alert severity, and optional handoff recommendation.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | 70% threshold trigger | Context utilization = 70% | Call `check_and_downgrade()` | Returns (L2, False, None); warning logged | Threshold exact at 70% |
| 2 | 93% threshold trigger | Context utilization = 93% | Call `check_and_downgrade()` | Returns (L3, True, "handoff_required"); CRITICAL alert logged | Threshold exact at 93% |
| 3 | Sub-70% no action | Context utilization = 69% | Call `check_and_downgrade()` | Returns (L3, False, None); no warning | No alert emitted |
| 4 | Budget recalculation speed | 1000-item finding set, max_tokens=5000 | Call `check_and_downgrade()` multiple times | Each call returns in ≤2s | Latency <2s |

**Dependencies:** Story 9

**Related FRs:** FR-E2-022, FR-E2-025, FR-E2-026, FR-E2-027

---

## Story 11: Auto-Handoff Generation (3 SP)

**Title:** Automatically generate HandoffDocument when 93% context threshold hit

**As a** synthesis automation engine
**I want** to automatically create a structured handoff document at 93% context usage
**So that** the next agent has all necessary context without manual prep

**Description:**
Implement auto-handoff trigger in ContextBudgetMonitor or agent loop: when `check_and_downgrade()` returns auto_handoff=True, call `generate_handoff_document(session: PipelineState, findings: List[Finding], budget: ContextBudget) → HandoffDocument`. HandoffDocument includes: current stage summary, active finding with status, key patterns reused in this session, next-step recommendations, and snapshot of remaining context.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Handoff trigger | 93% context threshold hit | Monitor detects trigger | `generate_handoff_document()` called automatically | No manual intervention |
| 2 | Document completeness | Handoff generation in progress | Check HandoffDocument fields | Contains: current_stage, active_finding, patterns, recommendations, context_snapshot | All fields populated |
| 3 | Markdown format | HandoffDocument generated | Call `.to_markdown()` | Output is valid Markdown with headers, lists, code blocks | Markdown validates with schema |

**Dependencies:** Story 10

**Related FRs:** FR-E2-028

---

## Story 12: CompositionRoot Memory Service Injection (2 SP)

**Title:** Update CompositionRoot factory to inject memory services

**As a** dependency container architect
**I want** CompositionRoot to create and inject PipelineStatePort, ExperiencePort, AuditPort instances
**So that** services are cleanly decoupled from concrete implementations

**Description:**
Update CompositionRoot.build() to include async setup hook for memory services. Based on environment config (local/CloudKit), instantiate appropriate port implementations. Return factory with lazy-loaded memory service accessors: `get_pipeline_state_port()`, `get_experience_port()`, `get_audit_port()`. Ensure async initialization completes before serving requests.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Port injection | CompositionRoot.build() called | Access `get_pipeline_state_port()` | Returns PipelineStatePort instance (CloudKit or local based on env) | isinstance() check passes |
| 2 | Async initialization | CompositionRoot instantiated | Call `await root.initialize_async()` | Memory service adapters fully initialized | No exceptions raised |
| 3 | Lazy loading | Root built but async not called | Try to access memory ports | Raises error or returns uninitialized adapter | Error message clear |

**Dependencies:** Story 4, Story 5, Story 6, Story 7

**Related FRs:** FR-E2-029, FR-E2-030

---

## Story 13: Cross-Device Integration Tests (8 SP)

**Title:** Implement integration tests for multi-device CloudKit sync scenarios

**As a** QA architect
**I want** end-to-end tests covering simultaneous edits on different devices
**So that** we verify sync correctness before production

**Description:**
Write pytest tests with mock CloudKit backend simulating two devices. Tests cover: (1) Save on A, verify appears on B after sync delay; (2) Concurrent edits on A and B, verify conflict resolution winner is deterministic; (3) Pattern reinforcement on A syncs to B; (4) Audit event on A queries correctly on B; (5) Offline mode on A, reconnect, verify queued writes flush. Use deterministic time mocking to control sync delays.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Cross-device persistence | Device A saves PipelineState | Device B fetches same session_id after 1s delay | Retrieves A's data | Test passes deterministically |
| 2 | Concurrent conflict resolution | Devices A and B both edit same pattern at T=10:00:00Z | Conflict resolved | Deterministic winner (lexicographic agent_id) | 100 concurrent runs, same result |
| 3 | Pattern reinforcement propagation | Pattern reinforced on A | Device B queries and calculates relevance | Sees updated `last_reinforced_at` | Sync latency <2s in test |
| 4 | Audit trail consistency | 50 events logged across A and B | Query all events from B | Returns all 50 in timestamp order | No duplicates, correct ordering |
| 5 | Offline queue flush | Device A writes 10 events offline, then reconnects | Events push to CloudKit | All 10 appear in CloudKit with correct metadata | CloudKit count = 10 |

**Dependencies:** Story 5, Story 6, Story 7, Story 8

**Related FRs:** FR-E2-015, FR-E2-016, FR-E2-017, FR-E2-018

---

## Story 14: Full Test Suite and Documentation (5 SP)

**Title:** Complete test suite for all models, adapters, and engines with docstrings

**As a** maintainability champion
**I want** ≥85% code coverage and comprehensive docstrings
**So that** future developers understand design and can modify safely

**Description:**
Write complete test files for: models (pipeline_state, experience_pattern, audit_event), ports, adapters, progressive disclosure, budget monitor. All tests use pytest, fixture-based setup, deterministic time mocking. Add Google-style docstrings to all public methods. Generate coverage report. Ensure no framework imports in domain models.

**Acceptance Criteria:**

| # | Criterion | GIVEN | WHEN | THEN | KPI |
|---|-----------|-------|------|------|-----|
| 1 | Coverage threshold | Test suite executed | Run `pytest --cov` | Coverage ≥85% for all non-test files | Report shows 85%+ |
| 2 | Docstring completeness | Public methods inspected | Use `pydoc` or IDE | All public methods have Google-style docstrings | 100% coverage |
| 3 | Framework isolation | Domain models inspected | grep for imports | No framework imports (Django, FastAPI, etc.) in `_models/` | Import scan shows 0 hits |

**Dependencies:** All prior stories

**Related FRs:** All FRs

---

## Story Point Summary

| Story | Title | SP | Sprint |
|-------|-------|----|----|
| 1 | PipelineState Model | 3 | 1 |
| 2 | ExperiencePattern + Decay | 8 | 1 |
| 3 | AuditEvent Immutable | 5 | 1 |
| 4 | Memory Adapter Ports | 3 | 2 |
| 5 | CloudKit Adapter (PipelineState) | 8 | 3 |
| 6 | CloudKit Adapter (Experience) | 8 | 3 |
| 7 | CloudKit Adapter (AuditEvent) | 5 | 3 |
| 8 | Conflict Resolution | 5 | 3 |
| 9 | Progressive Disclosure Engine | 8 | 4 |
| 10 | Context Budget Monitor | 5 | 4 |
| 11 | Auto-Handoff Generation | 3 | 4 |
| 12 | CompositionRoot Memory Injection | 2 | 2 |
| 13 | Cross-Device Integration Tests | 8 | 5 |
| 14 | Full Test Suite + Docs | 5 | 5 |
| **Total** | | **76 SP** | |

---

## Release Planning

- **Sprint 1** (Weeks 1-2): Stories 1, 2, 3 → Domain models (16 SP after S12 moved to S2)
- **Sprint 2** (Weeks 2-4): Stories 4, 12 → Ports + Injection (6 SP, add 10 SP padding for detailed adapter design)
- **Sprint 3** (Weeks 4-6): Stories 5, 6, 7, 8 → CloudKit Adapters + Conflict Resolution (26 SP)
- **Sprint 4** (Weeks 6-8): Stories 9, 10, 11 → Progressive Disclosure + Budget (16 SP)
- **Sprint 5** (Weeks 8-12): Stories 13, 14 → Integration Tests + Docs (13 SP)

**Total: 76 SP across 12 weeks (9 weeks minimum), 1 engineer + AI**

