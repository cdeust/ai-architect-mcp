# Epic 2: Requirements Specification

**Status:** Draft
**Date:** 2026-03-14
**Epic ID:** EPIC-E2

---

## Functional Requirements

| ID | Title | Description | Source | Status |
|---|---|---|---|---|
| **FR-E2-001** | PipelineState Model Definition | Define Pydantic v2 BaseModel for session-scoped agent execution state: `current_stage` (int, 0-10), `active_finding` (Finding UUID or None), `agent_id` (str), `skill_versions` (Dict[str, str]), `created_at` (datetime), `updated_at` (datetime) | ADR-004, Epic 1 | Draft |
| **FR-E2-002** | PipelineStatus Enum | Define enum: IDLE, RUNNING, PAUSED, HANDOFF_PENDING, COMPLETED, FAILED | ADR-004 | Draft |
| **FR-E2-003** | PipelineState Status Field | Add `status` field to PipelineState; allow transitions via `set_status(PipelineStatus)` method | FR-E2-002 | Draft |
| **FR-E2-004** | ExperiencePattern Model Definition | Define model: `pattern_id` (UUID), `pattern_type` (PatternType enum), `description` (str), `initial_relevance` (float [0.0-1.0]), `half_life_days` (int), `created_at` (datetime), `last_reinforced_at` (datetime), `reinforcement_count` (int) | ADR-007 | Draft |
| **FR-E2-005** | PatternType Enum | Define enum: ARCHITECTURAL, DOMAIN_MODELING, NAMING, INTERFACE_DESIGN, REFINEMENT_HEURISTIC | ADR-007 | Draft |
| **FR-E2-006** | ExperiencePattern Decay Calculation | Implement `current_relevance()` method: `relevance = initial_relevance × 0.5^(elapsed_days / half_life_days)` with accuracy ±1% at half-life | ADR-007 | Draft |
| **FR-E2-007** | ExperiencePattern Reinforcement | Implement `reinforce()` method: increment `reinforcement_count`, update `last_reinforced_at`, boost `initial_relevance` by (1 + reinforcement_count × 0.05) factor | ADR-007 | Draft |
| **FR-E2-008** | AuditEvent Model Definition | Define immutable model: `event_id` (UUID), `timestamp` (datetime, UTC), `agent_id` (str), `action` (str), `outcome` (AuditOutcome), `context_snapshot` (JSON), `duration_ms` (int), `metadata` (Dict[str, Any]) | ADR-004 | Draft |
| **FR-E2-009** | AuditOutcome Enum | Define enum: SUCCESS, FAILURE, PARTIAL, HANDOFF, VALIDATION_ERROR | ADR-004 | Draft |
| **FR-E2-010** | AuditEvent Immutability | AuditEvent instances must be frozen (Pydantic `frozen=True`); no update/delete semantics on AuditPort | ADR-004 | Draft |
| **FR-E2-011** | AuditQuery Model | Define model for querying audits: `agent_id_filter` (Optional[str]), `action_filter` (Optional[str]), `outcome_filter` (Optional[AuditOutcome]), `timestamp_range` (Optional[Tuple[datetime, datetime]]), `limit` (int, default 1000) | ADR-004 | Draft |
| **FR-E2-012** | PipelineStatePort (ABC) | Define async port: `load(session_id: str)`, `save(state: PipelineState)`, `delete(session_id: str)` with @abstractmethod decorator | ADR-004 | Draft |
| **FR-E2-013** | ExperiencePort (ABC) | Define async port: `list_patterns(min_relevance: float = 0.0)`, `save_pattern(pattern: ExperiencePattern)`, `get_pattern(pattern_id: UUID)`, `query_by_type(pattern_type: PatternType)` | ADR-004 | Draft |
| **FR-E2-014** | AuditPort (ABC) | Define async port: `append_event(event: AuditEvent)`, `query_events(query: AuditQuery)` with NO update/delete methods | ADR-004 | Draft |
| **FR-E2-015** | CloudKit Adapter for PipelineState | Implement PipelineStatePort adapter wrapping SwiftData + CloudKit; serialize to/from CloudKit record with `last_modified_by` and `last_modified_at` for conflict detection | ADR-004, CloudKit | Draft |
| **FR-E2-016** | CloudKit Adapter for Experience | Implement ExperiencePort adapter; persist ExperiencePattern collection to CloudKit zone; support bulk `list_patterns()` with relevance filtering | ADR-004, CloudKit | Draft |
| **FR-E2-017** | CloudKit Adapter for AuditEvent | Implement AuditPort adapter; append-only semantics enforced at adapter level (no update/delete CloudKit operations) | ADR-004, CloudKit | Draft |
| **FR-E2-018** | Conflict Resolution Strategy | Implement last-writer-wins for CloudKit syncs: compare `last_modified_at` timestamps; most recent record wins; log conflicts to AuditEvent | ADR-004, CloudKit | Draft |
| **FR-E2-019** | Conflict Resolution Ordering | Ensure deterministic ordering when timestamps equal: use `last_modified_by` (agent_id) lexicographic order as tiebreaker | FR-E2-018 | Draft |
| **FR-E2-020** | Offline-First Writes | All writes target local PipelineState/Experience/Audit stores first; async CloudKit push occurs without blocking caller | CloudKit | Draft |
| **FR-E2-021** | DisclosureLevel Enum | Define enum: L1 (~500 tokens), L2 (~300 tokens), L3 (~3000 tokens) | ADR-004 | Draft |
| **FR-E2-022** | ContextBudget Model | Define model: `total_tokens` (int), `used_tokens` (int), `disclosure_level` (DisclosureLevel), `timestamp` (datetime) | ADR-004 | Draft |
| **FR-E2-023** | Progressive Disclosure Engine | Implement algorithm to render findings/patterns at disclosure level: L1 = entity keys + pattern types; L2 = L1 + 1-sentence summaries; L3 = full JSON | ADR-004 | Draft |
| **FR-E2-024** | Token Budget Calculation | For any Finding/Pattern set and target disclosure level, calculate exact token count (actual or estimated) | FR-E2-023 | Draft |
| **FR-E2-025** | ContextBudgetMonitor Class | Implement monitor: `check_and_downgrade(context: List[Finding])` → returns next DisclosureLevel if exceeded 70% of budget; triggers alert at 93% | ADR-004 | Draft |
| **FR-E2-026** | 70% Threshold Trigger | At ≥70% context utilization, ContextBudgetMonitor should recommend downgrading to L2 (summaries) and emit warning | FR-E2-025 | Draft |
| **FR-E2-027** | 93% Threshold Trigger | At ≥93% context utilization, ContextBudgetMonitor should emit CRITICAL alert and prepare for auto-handoff | FR-E2-025 | Draft |
| **FR-E2-028** | Auto-Handoff Generation | When 93% threshold triggered, automatically generate HandoffDocument summarizing session state, active findings, and next-step recommendations | FR-E2-027 | Draft |
| **FR-E2-029** | CompositionRoot Memory Services | Update CompositionRoot factory to inject PipelineStatePort, ExperiencePort, AuditPort implementations based on environment (local/CloudKit) | ADR-004 | Draft |
| **FR-E2-030** | Async Port Initialization | CompositionRoot async setup hook must initialize CloudKit adapters before serving requests | FR-E2-029 | Draft |

---

## Non-Functional Requirements

| ID | Category | Requirement | Target | Rationale |
|---|---|---|---|---|
| **NFR-E2-001** | Performance | Experience decay calculation for 10K patterns | <100ms | Prevent blocking during context budget checks |
| **NFR-E2-002** | Performance | Progressive disclosure rendering (any level) | <200ms | User-facing context window optimization |
| **NFR-E2-003** | Performance | CloudKit sync latency (offline to cloud) | <2s | Enable near-real-time cross-device coherence |
| **NFR-E2-004** | Performance | AuditEvent write throughput | ≥100 events/sec | Support high-frequency agent logging |
| **NFR-E2-005** | Reliability | AuditEvent immutability enforcement | 100% | No mutations after creation |
| **NFR-E2-006** | Reliability | Conflict resolution determinism | 100% | Same inputs always produce same winner |
| **NFR-E2-007** | Scalability | Experience pattern storage | Support 50K+ patterns per user/project | Heuristic decay prevents unbounded growth |
| **NFR-E2-008** | Testability | Domain model isolation | Zero framework imports in domain layer | Enable rapid testing without CloudKit setup |
| **NFR-E2-009** | Compliance | Audit trail retention | ≥30 days | Meet basic compliance hold period |
| **NFR-E2-010** | Usability | Decay calculation accuracy | ±1% at half-life | Predictable pattern relevance over time |

---

## Domain Assumptions

1. **Half-life decay is sufficient** for pattern relevance; no ML-based decay curves
2. **Last-writer-wins** is acceptable conflict resolution (no merging strategies)
3. **CloudKit is available** in deployment environments
4. **Token counting** uses a fixed model (e.g., GPT-4, 4 chars ≈ 1 token)
5. **Progressive disclosure** is opt-in; L3 is default if no budget constraint
6. **Audit events are immutable** by design; historical correction via new audit entries only

---

## Acceptance Criteria Mapping

| FR ID | Primary AC | Secondary ACs |
|---|---|---|
| FR-E2-001 | AC-E2-001 | AC-E2-002 |
| FR-E2-004 | AC-E2-005 | AC-E2-006, AC-E2-007 |
| FR-E2-006 | AC-E2-008 | AC-E2-009 |
| FR-E2-010 | AC-E2-010 | AC-E2-011 |
| FR-E2-012 | AC-E2-012 | AC-E2-013 |
| FR-E2-015 | AC-E2-020 | AC-E2-021 |
| FR-E2-018 | AC-E2-025 | AC-E2-026 |
| FR-E2-023 | AC-E2-030 | AC-E2-031, AC-E2-032 |
| FR-E2-025 | AC-E2-035 | AC-E2-036, AC-E2-037 |
| FR-E2-028 | AC-E2-040 | AC-E2-041 |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-03-14 | AI Architect PRD | Initial 30 FRs + 10 NFRs |

