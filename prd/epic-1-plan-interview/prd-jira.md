# Epic 1: Plan Interview Stage — JIRA Tickets & Task Breakdown

## EPIC: E1-0 Plan Interview Stage (Stage 4.5)

| Field | Value |
|-------|-------|
| **Epic ID** | E1-0 |
| **Title** | Plan Interview Stage (Stage 4.5) — Mandatory PRD Quality Gate |
| **Description** | Implement a mandatory interrogation gate between Stage 4 (PRD Generation) and Stage 5 (PRD Review) that performs 10-dimensional analysis of PRDs before they advance. Gate prevents low-quality PRDs from reaching review. |
| **Status** | Backlog |
| **Priority** | P0 (Critical) |
| **Story Points** | 34 |
| **Team** | 1 Developer + 2 AI Agents |
| **Timeline** | 7-10 weeks (10 calendar weeks) |
| **Acceptance Criteria** | All 9 user stories complete with ≥85% test coverage; all 36 ACs met; full integration with Stage 4 and Stage 5 |

---

## SPRINT 1: Foundation & Scorer Architecture (Week 1) — 8 SP

### STORY: E1-1 Dimension Model Definition (3 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-1 |
| **Title** | Define domain models for interview dimensions, scores, and gate decisions |
| **Description** | Create Pydantic v2 domain models (DimensionType, DimensionScore, InterviewConfig, InterviewResult, GateDecision) to establish type-safe contract for dimension scoring. |
| **Story Points** | 3 |
| **Status** | Backlog |
| **Priority** | P0 |
| **Assignee** | [Developer] |

**Tasks**:
- [ ] E1-1-001: Create `_interview/__init__.py` package structure (0.5 SP)
- [ ] E1-1-002: Implement DimensionType enum with 10 values in `_interview/models.py` (0.5 SP)
- [ ] E1-1-003: Implement DimensionScore Pydantic model (0.5 SP)
- [ ] E1-1-004: Implement InterviewConfig Pydantic model with threshold validators (0.5 SP)
- [ ] E1-1-005: Implement GateDecision enum with 3 values (0.5 SP)
- [ ] E1-1-006: Implement InterviewResult Pydantic model (0.5 SP)
- [ ] E1-1-007: Write unit tests for all 5 models (1 SP)
- [ ] E1-1-008: Add docstrings and type hints to all models (0.5 SP)

**Acceptance Criteria**: AC-E1-001, AC-E1-002, AC-E1-003, AC-E1-004, AC-E1-005

**Depends On**: None

**Blocks**: E1-2, E1-3, E1-4

---

### STORY: E1-2a Group 1 Scorers — Base Infrastructure (5 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-2a |
| **Title** | Implement DimensionEvaluator port and base Scorer orchestrator |
| **Description** | Create abstract DimensionEvaluator port (ABC) in ports.py; implement Scorer base class that orchestrates all dimension evaluators; set up test fixtures. |
| **Story Points** | 5 |
| **Status** | Backlog |
| **Priority** | P0 |
| **Assignee** | [Developer] |

**Tasks**:
- [ ] E1-2a-001: Create `_interview/ports.py` with DimensionEvaluatorPort ABC (1 SP)
- [ ] E1-2a-002: Implement Scorer.evaluate_all() orchestrator in `_interview/scorers/base.py` (1.5 SP)
- [ ] E1-2a-003: Implement Scorer.evaluate_single() for individual dimension scoring (0.5 SP)
- [ ] E1-2a-004: Create test fixtures for sample PRD artifacts (1 SP)
- [ ] E1-2a-005: Write unit tests for Scorer orchestration (1 SP)

**Acceptance Criteria**: AC-E1-006

**Depends On**: E1-1

**Blocks**: E1-2, E1-3, E1-4, E1-6

---

## SPRINT 2: Group 1 Dimension Scorers (Weeks 2-3) — 10 SP

### STORY: E1-2 Dimension Scorer Implementation (Group 1) (5 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-2 |
| **Title** | Implement scorers for Group 1 dimensions (Structural Completeness) |
| **Description** | Implement 5 Group 1 scorers: D1-SECTIONS_PRESENT, D2-HEADER_FORMAT, D3-ID_CONSISTENCY, D4-OUTLINE_FLOW, D5-ARTIFACT_COHERENCE. |
| **Story Points** | 5 |
| **Status** | Backlog |
| **Priority** | P1 |
| **Assignee** | [Developer] |

**Tasks**:
- [ ] E1-2-001: Implement SectionsPresentScorer (D1) in `_interview/scorers/group_1.py` (0.8 SP)
- [ ] E1-2-002: Implement HeaderFormatScorer (D2) (0.8 SP)
- [ ] E1-2-003: Implement IDConsistencyScorer (D3) (0.8 SP)
- [ ] E1-2-004: Implement OutlineFlowScorer (D4) (0.8 SP)
- [ ] E1-2-005: Implement ArtifactCoherenceScorer (D5) (0.8 SP)
- [ ] E1-2-006: Write comprehensive unit tests for D1-D5 (≥3 tests each) (1 SP)

**Acceptance Criteria**: AC-E1-007, AC-E1-008, AC-E1-009, AC-E1-010, AC-E1-011

**Depends On**: E1-1, E1-2a

**Blocks**: E1-3, E1-4, E1-6, E1-9

---

## SPRINT 3: Group 2 Dimension Scorers + Gate Logic (Weeks 4-5) — 10 SP

### STORY: E1-3 Dimension Scorer Implementation (Group 2) (5 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-3 |
| **Title** | Implement scorers for Group 2 dimensions (Content Quality) |
| **Description** | Implement 5 Group 2 scorers: D6-CLARITY_LEVEL, D7-STAKEHOLDER_ALIGNMENT, D8-REQUIREMENT_PRECISION, D9-ASSUMPTION_VALIDATION, D10-SUCCESS_METRICS. |
| **Story Points** | 5 |
| **Status** | Backlog |
| **Priority** | P1 |
| **Assignee** | [Developer] |

**Tasks**:
- [ ] E1-3-001: Implement ClarityLevelScorer (D6) in `_interview/scorers/group_2.py` (0.8 SP)
- [ ] E1-3-002: Implement StakeholderAlignmentScorer (D7) (0.8 SP)
- [ ] E1-3-003: Implement RequirementPrecisionScorer (D8) (0.8 SP)
- [ ] E1-3-004: Implement AssumptionValidationScorer (D9) (0.8 SP)
- [ ] E1-3-005: Implement SuccessMetricsScorer (D10) (0.8 SP)
- [ ] E1-3-006: Write comprehensive unit tests for D6-D10 (≥3 tests each) (1 SP)

**Acceptance Criteria**: AC-E1-012, AC-E1-013, AC-E1-014, AC-E1-015, AC-E1-016

**Depends On**: E1-1, E1-2a

**Blocks**: E1-4, E1-6, E1-9

---

### STORY: E1-4 Gate Logic Implementation (5 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-4 |
| **Title** | Implement interview gate decision logic with threshold evaluation |
| **Description** | Implement InterviewGate.decide() with logic to evaluate dimension scores against critical/advisory thresholds; return APPROVED/PROVISIONAL/REJECTED verdicts; handle timeouts. |
| **Story Points** | 5 |
| **Status** | Backlog |
| **Priority** | P1 |
| **Assignee** | [Developer] |

**Tasks**:
- [ ] E1-4-001: Create `_interview/gate.py` with InterviewGate class (0.5 SP)
- [ ] E1-4-002: Implement gate decision algorithm (all critical ≥ threshold logic) (1 SP)
- [ ] E1-4-003: Implement APPROVED verdict logic (1 SP)
- [ ] E1-4-004: Implement PROVISIONAL verdict logic (1 SP)
- [ ] E1-4-005: Implement REJECTED verdict logic (1 SP)
- [ ] E1-4-006: Implement timeout handling (fail-open or skip dimension) (0.5 SP)
- [ ] E1-4-007: Write unit tests for gate logic (≥4 tests covering all verdicts) (1 SP)

**Acceptance Criteria**: AC-E1-017, AC-E1-018, AC-E1-019, AC-E1-020

**Depends On**: E1-1, E1-2, E1-3

**Blocks**: E1-6, E1-8, E1-9

---

## SPRINT 4: Integration + MCP Tools + Documentation (Weeks 6-7) — 8 SP

### STORY: E1-5 StageContext Integration (3 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-5 |
| **Title** | Integrate interview stage with StageContextPort for artifact persistence |
| **Description** | Integrate with StageContextPort to read Stage 4 PRD artifacts, write Stage 4.5 interview results, and query interview history. |
| **Story Points** | 3 |
| **Status** | Backlog |
| **Priority** | P1 |
| **Assignee** | [Developer] |

**Tasks**:
- [ ] E1-5-001: Create `_interview/context_adapter.py` wrapping StageContextPort (0.5 SP)
- [ ] E1-5-002: Implement load_prd_from_stage_4() method (0.5 SP)
- [ ] E1-5-003: Implement save_interview_result_to_stage_45() method (0.5 SP)
- [ ] E1-5-004: Implement query_interview_history() method (0.5 SP)
- [ ] E1-5-005: Write integration tests for artifact read/write/query (1 SP)

**Acceptance Criteria**: AC-E1-021, AC-E1-022, AC-E1-023

**Depends On**: E1-1, E1-2, E1-3, E1-4

**Blocks**: E1-6, E1-8

---

### STORY: E1-6 MCP Tool Integration (3 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-6 |
| **Title** | Register FastMCP tools for dimension scoring and gate execution |
| **Description** | Implement and register 3 FastMCP tools: ai_architect_score_dimension, ai_architect_run_interview_gate, ai_architect_query_interview_results. |
| **Story Points** | 3 |
| **Status** | Backlog |
| **Priority** | P1 |
| **Assignee** | [AI Agent - Orchestration] |

**Tasks**:
- [ ] E1-6-001: Create `_interview/mcp_tools.py` with FastMCP tool class (0.5 SP)
- [ ] E1-6-002: Implement ai_architect_score_dimension() tool (0.8 SP)
- [ ] E1-6-003: Implement ai_architect_run_interview_gate() tool (0.8 SP)
- [ ] E1-6-004: Implement ai_architect_query_interview_results() tool (0.8 SP)
- [ ] E1-6-005: Write unit tests for tool invocation (1 SP)

**Acceptance Criteria**: AC-E1-024, AC-E1-025, AC-E1-026

**Depends On**: E1-1, E1-2, E1-3, E1-4, E1-5

**Blocks**: E1-8, E1-9

---

### STORY: E1-7 SKILL.md v3.0 Update (2 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-7 |
| **Title** | Update SKILL.md to document Stage 4.5 orchestration and dimension specifications |
| **Description** | Document Stage 4.5 in SKILL.md v3.0: stage overview, entry/exit criteria, dimension definitions (D1-D10), MCP tool signatures, JSON schema examples. |
| **Story Points** | 2 |
| **Status** | Backlog |
| **Priority** | P1 |
| **Assignee** | [Developer] |

**Tasks**:
- [ ] E1-7-001: Create "Stage 4.5 — Plan Interview" section in SKILL.md (0.5 SP)
- [ ] E1-7-002: Document all 10 dimensions with descriptions, thresholds, scoring algorithms (0.8 SP)
- [ ] E1-7-003: Document 3 MCP tools with signatures, examples, return types (0.5 SP)
- [ ] E1-7-004: Add JSON schema examples (artifact schemas for Stage 4.5) (0.2 SP)

**Acceptance Criteria**: AC-E1-027, AC-E1-028, AC-E1-029

**Depends On**: E1-1, E1-2, E1-3, E1-4, E1-6

**Blocks**: None (can be done in parallel)

---

## SPRINT 5: Testing + Orchestrator Integration (Weeks 8-10) — 5 SP

### STORY: E1-8 Orchestrator Integration & E2E Flow (3 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-8 |
| **Title** | Integrate Stage 4.5 into the pipeline orchestrator and validate end-to-end flow |
| **Description** | Update orchestrator to insert Stage 4.5 between Stage 4 and Stage 5; implement verdict routing (APPROVED/PROVISIONAL → Stage 5, REJECTED → Stage 4 re-entry); test full pipeline flow. |
| **Story Points** | 3 |
| **Status** | Backlog |
| **Priority** | P1 |
| **Assignee** | [AI Agent - Orchestration] |

**Tasks**:
- [ ] E1-8-001: Update `_orchestrator/orchestrator.py` to insert Stage 4.5 (1 SP)
- [ ] E1-8-002: Implement APPROVED → Stage 5 routing (0.5 SP)
- [ ] E1-8-003: Implement PROVISIONAL → Stage 5 routing with flags (0.5 SP)
- [ ] E1-8-004: Implement REJECTED → Stage 4 re-entry with improvement suggestions (0.5 SP)
- [ ] E1-8-005: Write end-to-end integration tests for full pipeline (1 SP)

**Acceptance Criteria**: AC-E1-030, AC-E1-031, AC-E1-032

**Depends On**: E1-1 through E1-7

**Blocks**: E1-9

---

### STORY: E1-9 Comprehensive Test Suite (5 SP)

| Field | Value |
|-------|-------|
| **Story ID** | E1-9 |
| **Title** | Implement unit, integration, and acceptance tests for the interview stage |
| **Description** | Write comprehensive test suite covering all dimensions, gate logic, artifact persistence, MCP tools, and orchestrator integration. Achieve ≥85% code coverage. |
| **Story Points** | 5 |
| **Status** | Backlog |
| **Priority** | P0 |
| **Assignee** | [Developer + AI Agent - QA] |

**Tasks**:
- [ ] E1-9-001: Create `tests/test_interview/test_models.py` for model unit tests (0.5 SP)
- [ ] E1-9-002: Create `tests/test_interview/test_dimensions_group1.py` for D1-D5 tests (1 SP)
- [ ] E1-9-003: Create `tests/test_interview/test_dimensions_group2.py` for D6-D10 tests (1 SP)
- [ ] E1-9-004: Create `tests/test_interview/test_gate.py` for gate logic tests (0.5 SP)
- [ ] E1-9-005: Create `tests/test_interview/test_integration.py` for Stage 4→4.5→5 flow (1 SP)
- [ ] E1-9-006: Create `tests/test_interview/test_mcp_tools.py` for MCP tool tests (0.5 SP)
- [ ] E1-9-007: Run pytest-cov and verify ≥85% coverage on `_interview/` package (0.5 SP)
- [ ] E1-9-008: Document test strategy and create traceability matrix (0.5 SP)

**Acceptance Criteria**: AC-E1-033, AC-E1-034, AC-E1-035, AC-E1-036

**Depends On**: E1-1 through E1-8

**Blocks**: Epic completion

---

## CSV Export: JIRA Tickets

```csv
ID,Title,Type,Status,Priority,Story Points,Epic,Sprint,Assignee,Dependencies,Blocks
E1-0,Plan Interview Stage (Stage 4.5),Epic,Backlog,P0,34,E1-0,-,Team,None,"E1-1,E1-2,E1-3,E1-4,E1-5,E1-6,E1-7,E1-8,E1-9"
E1-1,Dimension Model Definition,Story,Backlog,P0,3,E1-0,Sprint 1,Developer,None,"E1-2,E1-3,E1-4"
E1-2a,Group 1 Scorers - Base Infrastructure,Story,Backlog,P0,5,E1-0,Sprint 1,Developer,E1-1,"E1-2,E1-3,E1-4,E1-6"
E1-2,Dimension Scorer Implementation (Group 1),Story,Backlog,P1,5,E1-0,Sprint 2,Developer,"E1-1,E1-2a","E1-3,E1-4,E1-6,E1-9"
E1-3,Dimension Scorer Implementation (Group 2),Story,Backlog,P1,5,E1-0,Sprint 3,Developer,"E1-1,E1-2a","E1-4,E1-6,E1-9"
E1-4,Gate Logic Implementation,Story,Backlog,P1,5,E1-0,Sprint 3,Developer,"E1-1,E1-2,E1-3","E1-6,E1-8,E1-9"
E1-5,StageContext Integration,Story,Backlog,P1,3,E1-0,Sprint 4,Developer,"E1-1,E1-2,E1-3,E1-4","E1-6,E1-8"
E1-6,MCP Tool Integration,Story,Backlog,P1,3,E1-0,Sprint 4,AI Agent,"E1-1,E1-2,E1-3,E1-4,E1-5","E1-8,E1-9"
E1-7,SKILL.md v3.0 Update,Story,Backlog,P1,2,E1-0,Sprint 4,Developer,"E1-1,E1-2,E1-3,E1-4,E1-6",None
E1-8,Orchestrator Integration & E2E Flow,Story,Backlog,P1,3,E1-0,Sprint 5,AI Agent,"E1-1,E1-2,E1-3,E1-4,E1-5,E1-6,E1-7",E1-9
E1-9,Comprehensive Test Suite,Story,Backlog,P0,5,E1-0,Sprint 5,Developer,"E1-1,E1-2,E1-3,E1-4,E1-5,E1-6,E1-8",Epic Complete
```

## Burndown Projection

Assuming 3.4 SP/week average across 10 weeks:

| Week | Sprint | Planned SP | Cumulative SP Completed | Remaining SP | Burndown % |
|------|--------|-----------|------------------------|--------------|-----------|
| 1 | S1 | 8 | 8 | 26 | 24% |
| 2-3 | S2 | 10 | 18 | 16 | 53% |
| 4-5 | S3 | 10 | 28 | 6 | 82% |
| 6-7 | S4 | 8 | 36 | -2 | 106% |
| 8-10 | S5 | 5 | 34 | 0 | 100% |

*Note: Sprint 4 may complete slightly ahead of schedule, allowing Sprint 5 to focus on testing and refinement.*

---

**Document**: JIRA Tickets & Task Breakdown | **Stage**: 4.5 | **Date**: 2025-03-14 | **Version**: 1.0
