# Epic 2: Sprint Roadmap

**Status:** Draft
**Date:** 2026-03-14
**Epic ID:** EPIC-E2
**Duration:** 9-12 weeks
**Total Capacity:** ~76 SP (1 engineer + AI automation)

---

## Sprint 0: CloudKit Assumption Validation (1 week, 5 SP)

**Goal:** De-risk CloudKit integration by building a small prototype and validating key assumptions before committing full architecture.

**Stories:**
- Prototype CloudKit zone setup + basic CRUD operations for mock PipelineState
- Validate sync latency assumptions (<2s)
- Test conflict resolution (last-writer-wins + timestamp ordering)

**Deliverables:**
- Working prototype of CloudKit adapter (PipelineState only)
- Sync latency measurements (actual hardware or simulator)
- Conflict test results demonstrating deterministic behavior

**Risks Addressed:**
- CloudKit quota limits
- Sync latency bottlenecks
- Conflict resolution edge cases

**Success Criteria:**
- Sync latency confirmed <2s on 95th percentile
- Conflict resolution test: 100 concurrent ops, deterministic winner
- No CloudKit quota errors on 1000-record volume

---

## Sprint 1: Domain Models (2 weeks, 16 SP)

**Goal:** Implement core domain models with full type safety and decay calculation.

**Stories:**
- S1: PipelineState Model (3 SP)
- S2: ExperiencePattern + Decay (8 SP)
- S3: AuditEvent Immutable (5 SP)

**Tasks:**

### S1: PipelineState
- [ ] Define PipelineState Pydantic v2 model
- [ ] Define PipelineStatus enum
- [ ] Implement `set_status()` and `advance_stage()` methods
- [ ] Add JSON serialization/deserialization
- [ ] Unit tests: model instantiation, status transitions, serialization

### S2: ExperiencePattern
- [ ] Define PatternType enum (5 variants)
- [ ] Implement ExperiencePattern model with decay formula
- [ ] Implement `current_relevance()` method with formula verification
- [ ] Implement `reinforce()` method with boost logic
- [ ] Unit tests: decay accuracy (±1%), reinforcement boost, edge cases (future dates, double half-life)

### S3: AuditEvent
- [ ] Define AuditOutcome enum
- [ ] Implement AuditEvent model (frozen=True)
- [ ] Define AuditQuery model
- [ ] Unit tests: immutability enforcement, event creation, query structure

**Acceptance Criteria:**
- All models compile without errors
- Type hints complete and correct
- Unit test coverage ≥90% for all models
- Decay calculation verified ±1% accuracy at half-life

**Risks:**
- Decay formula precision (mitigated by deterministic test cases with fixed timestamps)
- Pydantic v2 validator complexity (start simple, add custom validators only if needed)

---

## Sprint 2: Ports & Local Adapters (2 weeks, 11 SP + 10 SP design buffer)

**Goal:** Define adapter ports and implement local (non-CloudKit) reference implementations.

**Stories:**
- S4: Memory Adapter Ports (3 SP)
- S12: CompositionRoot Memory Injection (2 SP)
- Local adapter implementations (6 SP, unplanned but necessary)

**Tasks:**

### S4: Ports Definition
- [ ] Define PipelineStatePort ABC (load, save, delete)
- [ ] Define ExperiencePort ABC (list_patterns, save_pattern, get_pattern, query_by_type)
- [ ] Define AuditPort ABC (append_event, query_events)
- [ ] Add to `_adapters/ports.py`
- [ ] Unit tests: port interfaces are ABCs, cannot instantiate directly

### S12: CompositionRoot Update
- [ ] Add async `initialize_async()` hook
- [ ] Add `get_pipeline_state_port()`, `get_experience_port()`, `get_audit_port()` accessors
- [ ] Implement environment-based port selection (local vs CloudKit)
- [ ] Unit tests: port injection, lazy loading, error on uninitialized access

### Local Adapters (unplanned, but essential)
- [ ] LocalPipelineStateAdapter (in-memory + optional SQLite)
- [ ] LocalExperienceAdapter (in-memory store with filtering)
- [ ] LocalAuditAdapter (append-only list)

**Acceptance Criteria:**
- All ports defined and documented
- CompositionRoot can inject local adapters without error
- Local adapters implement all port methods correctly
- Unit tests passing for all adapters

**Risks:**
- Storage backend complexity (use in-memory for now, SQLite only if needed)

---

## Sprint 3: CloudKit Adapters & Conflict Resolution (2 weeks, 16 SP)

**Goal:** Implement CloudKit adapters for all three ports and implement last-writer-wins conflict resolution.

**Stories:**
- S5: CloudKit Adapter for PipelineState (8 SP)
- S6: CloudKit Adapter for Experience (8 SP)
- S7: CloudKit Adapter for AuditEvent (5 SP)
- S8: Conflict Resolution (5 SP)

**Tasks:**

### S5: CloudKit PipelineState Adapter
- [ ] Implement PipelineStatePort using SwiftData + CloudKit SDK
- [ ] Add `last_modified_by`, `last_modified_at` metadata fields
- [ ] Implement offline-first write (local → async CloudKit)
- [ ] Implement load with CloudKit-first fallback to local
- [ ] Integration tests: offline write, sync queue, fallback behavior

### S6: CloudKit Experience Adapter
- [ ] Implement ExperiencePort for pattern persistence
- [ ] Implement bulk `list_patterns()` with client-side filtering
- [ ] Implement `save_pattern()` with sync
- [ ] Implement `query_by_type()` with CloudKit predicate
- [ ] Integration tests: reinforcement sync, bulk list accuracy, query correctness

### S7: CloudKit AuditEvent Adapter
- [ ] Implement AuditPort append-only semantics
- [ ] Implement `append_event()` with local + async CloudKit
- [ ] Implement `query_events()` with AuditQuery filtering
- [ ] Integration tests: append correctness, query filtering, no update/delete

### S8: Conflict Resolution
- [ ] Implement conflict detection logic (compare timestamps)
- [ ] Implement tiebreaker (lexicographic agent_id)
- [ ] Log conflicts to AuditEvent with outcome=PARTIAL
- [ ] Determinism tests: 100 concurrent conflict scenarios, same winner

**Acceptance Criteria:**
- CloudKit adapters implement all port methods
- Offline-first write latency ≤100ms
- Sync latency <2s (95th percentile)
- Conflict resolution deterministic across 100 runs
- All conflicts logged to audit trail

**Risks:**
- CloudKit zone configuration complexity (use defaults where possible)
- SwiftData version compatibility (pin to known-good version)

---

## Sprint 4: Progressive Disclosure & Budget Monitor (2 weeks, 13 SP)

**Goal:** Implement context budget optimization with automatic disclosure level switching and auto-handoff trigger.

**Stories:**
- S9: Progressive Disclosure Engine (8 SP)
- S10: Context Budget Monitor (5 SP)
- S11: Auto-Handoff Generation (3 SP)

**Tasks:**

### S9: Progressive Disclosure
- [ ] Define DisclosureLevel enum (L1, L2, L3)
- [ ] Implement ProgressiveDisclosure.render() for L1/L2/L3
- [ ] Implement `calculate_token_count()` heuristic (4 chars/token, or tiktoken)
- [ ] L1: keys + types only
- [ ] L2: keys + types + 1-sentence summaries (truncated to ~100 chars)
- [ ] L3: full JSON
- [ ] Unit tests: token count accuracy (±2%), level rendering correctness

### S10: Context Budget Monitor
- [ ] Implement ContextBudget class (total, used, timestamp)
- [ ] Implement ContextBudgetMonitor with 70%/93% thresholds
- [ ] Implement `check_and_downgrade()` returning (level, trigger_handoff, alert_msg)
- [ ] Integration tests: threshold accuracy, alert messages, performance <2s

### S11: Auto-Handoff Generation
- [ ] Implement auto-handoff trigger when 93% threshold hit
- [ ] Implement `generate_handoff_document()` (uses existing HandoffDocument model)
- [ ] Capture current_stage, active_finding, patterns reused, recommendations
- [ ] Unit tests: handoff generation on trigger, document completeness

**Acceptance Criteria:**
- Progressive disclosure tokens within budget targets (L1 ≤500t, L2 ≤300t, L3 ≤3000t)
- Budget monitor thresholds accurate to ±1%
- Handoff document generated within 500ms of 93% trigger
- All token counting verified against expected heuristic

**Risks:**
- Token counting heuristic inaccuracy (validate with actual tiktoken before release)
- 93% threshold too aggressive (monitor production usage, adjust to 90% if needed)

---

## Sprint 5: Integration Tests & Documentation (2 weeks, 8 SP + 5 SP unplanned tests)

**Goal:** Verify cross-device sync scenarios, ensure ≥85% test coverage, and document all public APIs.

**Stories:**
- S13: Cross-Device Integration Tests (8 SP)
- S14: Full Test Suite + Docs (5 SP)

**Tasks:**

### S13: Cross-Device Integration Tests
- [ ] Setup mock CloudKit backend (or real CloudKit with test zones)
- [ ] Test 1: Save on Device A, load on Device B after sync
- [ ] Test 2: Concurrent edits on A and B, verify deterministic conflict winner
- [ ] Test 3: Pattern reinforced on A, queried on B with updated metadata
- [ ] Test 4: Audit events logged on A, queried from B
- [ ] Test 5: Offline on A, write 10 events, reconnect, verify queue flush
- [ ] Determinism: Run concurrent tests 100×, verify no flaky results

### S14: Full Test Suite + Documentation
- [ ] Test suite: test_pipeline_state.py (model, status, serialization)
- [ ] Test suite: test_experience_pattern.py (decay, reinforcement, edge cases)
- [ ] Test suite: test_audit_event.py (immutability, creation, queries)
- [ ] Test suite: test_progressive_disclosure.py (L1/L2/L3, token counts)
- [ ] Test suite: test_budget_monitor.py (70%/93% thresholds, performance)
- [ ] Test suite: test_cloudkit_sync.py (offline, sync, conflict resolution)
- [ ] Coverage report: target ≥85% for all non-test code
- [ ] API documentation: Google-style docstrings for all public methods
- [ ] Architecture guide: README explaining four-layer model, CloudKit sync, decay formula

**Acceptance Criteria:**
- ≥85% code coverage (verified by pytest --cov)
- All integration tests pass
- No flaky tests (100 determinism runs)
- All public methods have docstrings
- Architecture guide covers design decisions and trade-offs

**Risks:**
- Coverage tools may not handle CloudKit mocks correctly (use fixtures liberally)
- Integration test setup complexity (create helper functions early)

---

## Timeline

```
Week 1       Sprint 0 (CloudKit Prototype, 5 SP)
             Sprint 1 starts

Weeks 2-3    Sprint 1 (Domain Models, 16 SP)
             Sprint 2 starts (parallel design)

Weeks 4-5    Sprint 2 (Ports + Local Adapters, 11 SP)
             Sprint 3 starts (parallel design)

Weeks 6-7    Sprint 3 (CloudKit + Conflict, 16 SP)
             Sprint 4 starts (parallel design)

Weeks 8-9    Sprint 4 (Disclosure + Budget, 13 SP)
             Sprint 5 starts (parallel testing)

Weeks 10-12  Sprint 5 (Integration Tests + Docs, 8 SP)

Total: 9-12 weeks, 76 SP
```

---

## Staffing & Capacity

| Role | Allocation | Notes |
|------|-----------|-------|
| Tech Lead | 1.0 FTE | Architecture, ports, CloudKit adapter design |
| Backend Engineer | 1.0 FTE (or AI automation equivalent) | Implementation, local adapters, tests |
| QA / Automation | 0.5 FTE (AI) | Test suite generation, coverage analysis |
| **Total** | **1 + AI** | Uneven sprint load due to CloudKit unknowns |

---

## Sprint Load & Burndown

| Sprint | SP | Owner | Rationale |
|--------|----|----|-----------|
| S0 | 5 | Lead | De-risk CloudKit (prototype only, unplanned) |
| S1 | 16 | Backend + AI | Domain models, straightforward implementation |
| S2 | 11 | Lead + Backend | Port definitions, local adapters (less risky) |
| S3 | 16 | Lead | CloudKit adapters, conflict resolution (high complexity) |
| S4 | 13 | Backend + AI | Disclosure, budget, auto-handoff (well-defined) |
| S5 | 8 | Backend + AI | Integration tests, documentation (execution) |
| **Total** | **76** | | |

---

## Key Milestones & Gates

| Milestone | Sprint | Criteria | Risk Mitigation |
|-----------|--------|----------|-----------------|
| **CloudKit Viability** | S0 | <2s sync latency, deterministic conflict resolution | Proceed to S1 only if validated |
| **Model Completeness** | S1 | All models compile, ≥90% test coverage, decay ±1% accurate | Code review + peer testing |
| **Port Isolation** | S2 | No framework imports in domain models, ports are true ABCs | Linting + import audit |
| **Adapter Correctness** | S3 | Offline writes <100ms, sync <2s, conflicts deterministic | Integration tests on real hardware |
| **Budget Correctness** | S4 | Thresholds ±1%, disclosure levels within token budgets | Automated threshold tests |
| **Production Ready** | S5 | ≥85% coverage, all AC-E2-* verified, no flaky tests | CI/CD validation before release |

---

## Dependencies Between Sprints

```
S0 (Prototype)
    ↓ (CloudKit viability confirmed)
S1 (Domain Models)
    ↓
S2 (Ports) ← (can start during S1)
    ↓
S3 (CloudKit Adapters) ← (uses ports from S2, models from S1)
    ↓
S4 (Disclosure + Budget) ← (can start parallel with S3)
    ↓
S5 (Integration Tests) ← (uses all components from S1-S4)
```

No critical path bottlenecks; S4 can start in parallel with S3 end-of-sprint.

---

## Success Definition

At end of Sprint 5:
- ✓ All 9 PRD files complete with consistent AC IDs, SP estimates
- ✓ 76 SP delivered (±5%)
- ✓ ≥85% test coverage across all modules
- ✓ CloudKit sync <2s latency (95th percentile)
- ✓ Conflict resolution deterministic
- ✓ Progressive disclosure within token budgets
- ✓ Budget monitor thresholds ±1% accurate
- ✓ All AC-E2-001 through AC-E2-041 verified
- ✓ Zero framework imports in domain models
- ✓ Comprehensive API documentation

