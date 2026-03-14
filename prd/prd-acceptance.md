# PRD Acceptance Criteria — AI Architect Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**PRD Type:** Full Scope Overview

---

## Acceptance Criteria with KPI Linkage

### AC-001: Plan Interview — Full Dimension Evaluation

**GIVEN** a completed Stage 4 output in StageContextPort
**WHEN** Stage 4.5 (Plan Interview) executes
**THEN** all 10 dimensions are evaluated and each produces a DimensionScore

| Metric | Value |
|--------|-------|
| Baseline | N/A — new capability |
| Target | 10/10 dimensions evaluated per run |
| Measurement | Unit test: `test_all_dimensions_evaluated()` |
| Business Impact | BG-005: Reduce PRD defect rate from 8% to < 5% |

---

### AC-002: Plan Interview — Gate Blocking

**GIVEN** any dimension scores below its configured pass threshold
**WHEN** the pipeline attempts to advance to Stage 5
**THEN** progression is blocked and a detailed report of failing dimensions is returned

| Metric | Value |
|--------|-------|
| Baseline | N/A — no gate exists today |
| Target | 100% of sub-threshold dimensions block progression |
| Measurement | Integration test: `test_gate_blocks_on_failure()` |
| Business Impact | BG-005: Prevent incomplete PRDs from reaching review |

---

### AC-003: Plan Interview — Context Pass-Through

**GIVEN** all 10 dimensions pass their thresholds
**WHEN** Stage 4.5 completes
**THEN** enriched context (dimension scores + findings) is written to StageContextPort for Stage 5

| Metric | Value |
|--------|-------|
| Baseline | Stage 4 output passes directly to Stage 5 (no enrichment) |
| Target | Enriched context includes all 10 dimension scores and findings |
| Measurement | Integration test: `test_enriched_context_written()` |
| Business Impact | BG-005: Higher quality input to PRD Review |

---

### AC-004: Dimension Scoring Output

**GIVEN** a Stage 4.5 run completes
**WHEN** results are returned to the caller
**THEN** each dimension has a numeric score (0.0–1.0) and pass/fail indicator

| Metric | Value |
|--------|-------|
| Baseline | N/A — new capability |
| Target | All scores in [0.0, 1.0] range, pass/fail computed against threshold |
| Measurement | Unit test: `test_dimension_score_range()` |
| Business Impact | BG-005 |

---

### AC-005: Failing Dimension Report

**GIVEN** a dimension scores below its threshold
**WHEN** the dimension report is generated
**THEN** it includes specific findings and suggested improvements

| Metric | Value |
|--------|-------|
| Baseline | N/A — no feedback exists |
| Target | ≥ 1 specific finding + ≥ 1 actionable suggestion per failing dimension |
| Measurement | Unit test: `test_failing_dimension_has_findings()` |
| Business Impact | BG-005 |

---

### AC-006: CloudKit Cross-Device Sync

**GIVEN** a PipelineState update on Mac
**WHEN** iCloud sync completes
**THEN** the same state is readable on a second Apple device

| Metric | Value |
|--------|-------|
| Baseline | N/A — local-only persistence today |
| Target | Sync visible within 5 seconds (CloudKit typical latency) |
| Measurement | Manual test: 2-device sync verification |
| Business Impact | BG-002: Cross-device persistence |

**HUMAN REVIEW REQUIRED:** CloudKit latency depends on network conditions. 5-second target is based on industry benchmarks, not measured baseline.

---

### AC-007: CloudKit Conflict Resolution

**GIVEN** concurrent PipelineState updates from 2 devices
**WHEN** CloudKit detects a sync conflict
**THEN** the most recent timestamp wins and both devices converge

| Metric | Value |
|--------|-------|
| Baseline | N/A — no sync exists |
| Target | 100% conflict detection, 95% auto-resolution via last-writer-wins |
| Measurement | Integration test: simulated concurrent writes |
| Business Impact | BG-002, NFR-010 |

---

### AC-008: Experience Pattern Half-Life Decay

**GIVEN** an ExperiencePattern with half_life_days = 30
**WHEN** 30 days have elapsed since creation
**THEN** current_relevance() returns ~50% of initial_relevance (±1% floating point)

| Metric | Value |
|--------|-------|
| Baseline | N/A — no experience patterns exist |
| Target | Decay follows formula: `initial × 0.5^(elapsed / half_life)` |
| Measurement | Unit test: `test_half_life_decay()` with deterministic timestamps |
| Business Impact | BG-005: Recommendations evolve with codebase |

---

### AC-009: Experience Pattern Reinforcement

**GIVEN** an ExperiencePattern that was accessed by the pipeline
**WHEN** the pattern is used in a decision
**THEN** its last_accessed_at is updated, effectively resetting decay

| Metric | Value |
|--------|-------|
| Baseline | N/A |
| Target | last_accessed_at updated to current time on access |
| Measurement | Unit test: `test_pattern_reinforcement()` |
| Business Impact | BG-005 |

---

### AC-010: Progressive Disclosure — 70% Threshold

**GIVEN** context token usage reaches 70%
**WHEN** the budget monitor triggers
**THEN** the system switches non-active stages from L3 full to L2 summaries

| Metric | Value |
|--------|-------|
| Baseline | All context loaded at L3 (no budget management) |
| Target | Token usage drops by ≥ 40% after L3→L2 switch |
| Measurement | Unit test: `test_progressive_disclosure_70_percent()` |
| Business Impact | NFR-008 |

---

### AC-011: Progressive Disclosure — 93% Auto-Handoff

**GIVEN** context token usage reaches 93%
**WHEN** the budget monitor triggers
**THEN** a HandoffDocument is auto-generated with full session state

| Metric | Value |
|--------|-------|
| Baseline | No auto-handoff (context overflow causes degradation) |
| Target | HandoffDocument generated with all active context within 5 seconds |
| Measurement | Unit test: `test_auto_handoff_at_93_percent()` |
| Business Impact | NFR-008 |

---

### AC-012: Immutable Audit Event Logging

**GIVEN** any stage completes (success or failure)
**WHEN** the pipeline advances
**THEN** an AuditEvent is appended with who, what, when, where, and outcome

| Metric | Value |
|--------|-------|
| Baseline | No audit trail exists |
| Target | 100% of stage completions produce an AuditEvent |
| Measurement | Integration test: `test_audit_event_per_stage()` |
| Business Impact | BG-006 |

---

### AC-013: Audit Event Immutability

**GIVEN** an AuditEvent in the log
**WHEN** any operation attempts to modify or delete it
**THEN** the operation is rejected with an error

| Metric | Value |
|--------|-------|
| Baseline | N/A |
| Target | 0 successful mutations on audit events |
| Measurement | Unit test: `test_audit_event_immutability()` |
| Business Impact | BG-006 |

---

### AC-014 through AC-035

*Acceptance criteria AC-014 through AC-035 follow the same pattern as above, covering Epics 3–6. Each AC includes GIVEN-WHEN-THEN format with Baseline, Target, Measurement, and Business Impact. Full detail is provided in the user stories file (prd-user-stories.md). Per Full Scope Overview mode, detailed KPI tables for these ACs will be generated in the per-epic implementation PRDs.*

---

## AC Coverage Summary

| Epic | AC Count | Happy Path | Error/Edge | Total |
|------|----------|------------|------------|-------|
| Epic 1: Plan Interview | AC-001 to AC-005 | 3 | 2 | 5 |
| Epic 2: Memory Model | AC-006 to AC-013 | 5 | 3 | 8 |
| Epic 3: Consensus | AC-014 to AC-017 | 2 | 2 | 4 |
| Epic 4: Hooks | AC-018 to AC-023 | 3 | 3 | 6 |
| Epic 5: GitHub Actions | AC-024 to AC-029 | 4 | 2 | 6 |
| Epic 6: Python Migration | AC-030 to AC-035 | 4 | 2 | 6 |
| **Total** | | **21** | **14** | **35** |
