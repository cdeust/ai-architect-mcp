# Epic 1: Plan Interview Stage — Roadmap & Sprint Plan

## Timeline Overview

**Total Duration**: 7-10 weeks (8 calendar weeks, accounting for reviews/iterations)
**Team**: 1 developer + 2 AI agents (dimension evaluation + orchestration)
**Total Story Points**: 34 SP (Fibonacci-distributed)
**Delivery Cadence**: 5 sprints of uneven duration

```
Week 1   Week 2-3     Week 4-5       Week 6-7           Week 8-10
|--------|-----------|-------------|--------------------|------------|
Sprint 1  Sprint 2    Sprint 3      Sprint 4            Sprint 5
8 SP      10 SP       10 SP         8 SP                5 SP
```

## Sprint Breakdown

### Sprint 1: Foundation & Scorer Architecture (Week 1) — 8 SP

**Goal**: Establish domain models, scorer port, and base infrastructure

**Stories Included**:
- Story 1: Dimension Model Definition (3 SP)
- Story 2 (Partial): Group 1 Scorer Setup + Base Scorer Class (5 SP)

| Story | Title | SP | Tasks |
|-------|-------|-----|-------|
| 1 | Dimension Model Definition | 3 | Create DimensionType enum, DimensionScore, InterviewConfig, GateDecision, InterviewResult Pydantic models; validate all models with unit tests |
| 2a | Group 1 Scorers — Base Infrastructure | 5 | Create DimensionEvaluatorPort abstract class; implement base Scorer orchestrator; create test fixtures; set up _interview/ package structure |

**Key Deliverables**:
- `_interview/models.py` with all 5 domain models (Pydantic v2)
- `_interview/ports.py` with DimensionEvaluatorPort ABC
- `_interview/scorers/base.py` with Scorer orchestrator
- Package `__init__.py` exports
- Unit tests for all models (fixtures-driven)

**Acceptance Criteria**:
- AC-E1-001 (DimensionType enum) ✓
- AC-E1-002 (DimensionScore model) ✓
- AC-E1-003 (InterviewConfig model) ✓
- AC-E1-004 (InterviewResult model) ✓
- AC-E1-005 (GateDecision enum) ✓
- AC-E1-006 (DimensionEvaluator port) ✓

**Dependencies**: None (greenfield sprint)

**Risks**: None significant

---

### Sprint 2: Group 1 Dimension Scorers (Weeks 2-3) — 10 SP

**Goal**: Implement all 5 Group 1 (Structural Completeness) dimension scorers

**Stories Included**:
- Story 2 (Continued): Group 1 Dimension Scorers (5 SP)

| Story | Title | SP | Tasks |
|-------|-------|-----|-------|
| 2 | Dimension Scorer Implementation (Group 1) | 5 | Implement D1-D5 scorers (SectionsPresentScorer, HeaderFormatScorer, IDConsistencyScorer, OutlineFlowScorer, ArtifactCoherenceScorer); write comprehensive unit tests for all 5 dimensions |

**Key Deliverables**:
- `_interview/scorers/group_1.py` with 5 scorer implementations
- Unit tests: ≥3 tests per dimension (15+ tests total)
- Test fixtures: sample PRDs with various section counts, header formats, ID patterns
- Documentation: dimension scoring algorithms in docstrings

**Acceptance Criteria**:
- AC-E1-007 (D1 SECTIONS_PRESENT) ✓
- AC-E1-008 (D2 HEADER_FORMAT) ✓
- AC-E1-009 (D3 ID_CONSISTENCY) ✓
- AC-E1-010 (D4 OUTLINE_FLOW) ✓
- AC-E1-011 (D5 ARTIFACT_COHERENCE) ✓

**Dependencies**: Sprint 1 completion (models, port, base scorer)

**Risks**:
- Coherence scorer keyword extraction may need tuning (mitigation: start with simple heuristic, refine in Stage 5 feedback)
- Test fixture creation time (mitigation: use parametrized tests, reuse fixtures)

---

### Sprint 3: Group 2 Dimension Scorers + Gate Logic (Weeks 4-5) — 10 SP

**Goal**: Implement Group 2 (Content Quality) scorers and gate decision logic

**Stories Included**:
- Story 3: Dimension Scorer Implementation (Group 2) (5 SP)
- Story 4: Gate Logic Implementation (5 SP)

| Story | Title | SP | Tasks |
|-------|-------|-----|-------|
| 3 | Dimension Scorer Implementation (Group 2) | 5 | Implement D6-D10 scorers (ClarityLevelScorer, StakeholderAlignmentScorer, RequirementPrecisionScorer, AssumptionValidationScorer, SuccessMetricsScorer); write unit tests |
| 4 | Gate Logic Implementation | 5 | Implement InterviewGate.decide() with threshold logic; test all three verdicts (APPROVED/PROVISIONAL/REJECTED); implement timeout handling |

**Key Deliverables**:
- `_interview/scorers/group_2.py` with 5 scorer implementations
- `_interview/gate.py` with gate decision logic
- Unit tests: ≥3 tests per dimension (15+ tests), ≥4 gate logic tests
- Test fixtures: prose samples with various clarity levels, user stories, requirements
- Timeout handling implementation

**Acceptance Criteria**:
- AC-E1-012 (D6 CLARITY_LEVEL) ✓
- AC-E1-013 (D7 STAKEHOLDER_ALIGNMENT) ✓
- AC-E1-014 (D8 REQUIREMENT_PRECISION) ✓
- AC-E1-015 (D9 ASSUMPTION_VALIDATION) ✓
- AC-E1-016 (D10 SUCCESS_METRICS) ✓
- AC-E1-017 (APPROVED verdict) ✓
- AC-E1-018 (PROVISIONAL verdict) ✓
- AC-E1-019 (REJECTED verdict) ✓
- AC-E1-020 (Timeout handling) ✓

**Dependencies**: Sprint 1 & 2 completion

**Risks**:
- Clarity level and precision scoring may require NLP heuristics (mitigation: start simple, iterate)
- Success metrics detection requires robust table parsing (mitigation: use regex, add error handling)

---

### Sprint 4: Integration + MCP Tools + Documentation (Weeks 6-7) — 8 SP

**Goal**: Integrate with StageContext, register MCP tools, update SKILL.md, integrate with orchestrator

**Stories Included**:
- Story 5: StageContext Integration (3 SP)
- Story 6: MCP Tools Integration (3 SP)
- Story 7: SKILL.md v3.0 Update (2 SP)

| Story | Title | SP | Tasks |
|-------|-------|-----|-------|
| 5 | StageContext Integration | 3 | Implement artifact read from Stage 4, write to Stage 4.5; integrate with StageContextPort; test load/save/query flow |
| 6 | MCP Tools Integration | 3 | Register 3 FastMCP tools (score_dimension, run_interview_gate, query_interview_results); test tool signatures and return types |
| 7 | SKILL.md v3.0 Update | 2 | Document Stage 4.5 section; define all 10 dimensions; document MCP tool signatures; add JSON schema examples |

**Key Deliverables**:
- `_interview/mcp_tools.py` with 3 FastMCP tools registered
- Integration tests: Stage 4 → 4.5 → 5 flow
- SKILL.md v3.0 with comprehensive Stage 4.5 documentation
- `_composition.py` updates for Stage 4.5 setup
- Orchestrator integration (Stage 4.5 insertion between 4 and 5)

**Acceptance Criteria**:
- AC-E1-021 (Stage 4 artifact loading) ✓
- AC-E1-022 (Stage 4.5 artifact persistence) ✓
- AC-E1-023 (Interview result querying) ✓
- AC-E1-024 (score_dimension MCP tool) ✓
- AC-E1-025 (run_interview_gate MCP tool) ✓
- AC-E1-026 (query_interview_results MCP tool) ✓
- AC-E1-027 (Stage 4.5 section in SKILL.md) ✓
- AC-E1-028 (Dimension definitions in SKILL.md) ✓
- AC-E1-029 (MCP tool signatures in SKILL.md) ✓

**Dependencies**: Sprint 1, 2, 3 completion; existing StageContext and orchestrator code

**Risks**:
- Orchestrator integration may require coordination with Stage 4 & 5 (mitigation: write integration tests early)
- MCP tool registration may conflict with existing tools (mitigation: use unique ai_architect_ prefix)

---

### Sprint 5: Comprehensive Testing + Final Documentation (Weeks 8-10) — 5 SP

**Goal**: Complete test suite with ≥85% coverage, finalize documentation, prepare for release

**Stories Included**:
- Story 8: Orchestrator Integration & E2E Flow (3 SP)
- Story 9: Comprehensive Test Suite (5 SP)

| Story | Title | SP | Tasks |
|-------|-------|-----|-------|
| 8 | Orchestrator Integration & E2E Flow | 3 | Update orchestrator to insert Stage 4.5; implement verdict routing (APPROVED → Stage 5, REJECTED → Stage 4 re-entry); test full pipeline flow |
| 9 | Comprehensive Test Suite | 5 | Unit tests for all dimensions + gate logic; integration tests for Stage 4.5 flow; achieve ≥85% coverage; test error handling and edge cases |

**Key Deliverables**:
- `tests/test_interview/test_models.py` (dimension model unit tests)
- `tests/test_interview/test_dimensions_group1.py` (D1-D5 unit tests)
- `tests/test_interview/test_dimensions_group2.py` (D6-D10 unit tests)
- `tests/test_interview/test_gate.py` (gate logic unit tests)
- `tests/test_interview/test_integration.py` (Stage 4 → 4.5 → 5 flow)
- `tests/test_interview/test_mcp_tools.py` (MCP tool invocation tests)
- pytest-cov coverage report (≥85% on _interview/ package)
- Final PRD documentation (all 9 files complete)

**Acceptance Criteria**:
- AC-E1-030 (Orchestrator stage insertion) ✓
- AC-E1-031 (Gate verdict routing) ✓
- AC-E1-032 (End-to-end flow) ✓
- AC-E1-033 (Unit tests for dimensions) ✓
- AC-E1-034 (Gate logic tests) ✓
- AC-E1-035 (Integration tests) ✓
- AC-E1-036 (≥85% test coverage) ✓

**Dependencies**: Sprint 1-4 completion

**Risks**:
- Coverage gaps may require additional test writing (mitigation: use pytest-cov to identify hotspots)
- E2E tests may surface integration issues (mitigation: write integration tests in Sprint 4 for early detection)

---

## Story Point Summary by Sprint

| Sprint | Focus | Duration | Stories | Total SP | Velocity |
|--------|-------|----------|---------|----------|----------|
| 1 | Foundation | Week 1 | 1, 2a | 8 | 8 SP/week |
| 2 | Group 1 Dimensions | Weeks 2-3 | 2 | 10 | 5 SP/week |
| 3 | Group 2 Dimensions + Gate | Weeks 4-5 | 3, 4 | 10 | 5 SP/week |
| 4 | Integration + Tools + Docs | Weeks 6-7 | 5, 6, 7 | 8 | 4 SP/week |
| 5 | Testing + Final Docs | Weeks 8-10 | 8, 9 | 5 | 1.67 SP/week |
| **TOTAL** | - | 10 weeks | 9 stories | **34 SP** | **3.4 SP/week avg** |

**Notes on Uneven Distribution**:
- Sprint 1: Higher velocity (foundation work, focused scope)
- Sprint 2-3: Steady velocity (dimension implementation, repetitive patterns enable efficiency)
- Sprint 4: Lower velocity (integration requires coordination, documentation time-intensive)
- Sprint 5: Much lower velocity (testing is thorough, covers many edge cases)
- Average: 3.4 SP/week across 10 weeks; some weeks 4-5 SP, others 1-2 SP

## Key Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **Domain Models Ready** | End Week 1 | All 5 Pydantic models + port definition complete, unit tests passing |
| **Group 1 Scorers Done** | End Week 3 | All 5 Group 1 scorers implemented, unit tests ≥85% coverage for D1-D5 |
| **Group 2 Scorers + Gate Done** | End Week 5 | All 5 Group 2 scorers + gate logic implemented, all unit tests passing |
| **Integration Complete** | End Week 7 | MCP tools registered, SKILL.md updated, orchestrator integration done |
| **E2E Tests Passing** | End Week 9 | Stage 4 → 4.5 → 5 flow verified, verdict routing working |
| **≥85% Coverage Achieved** | End Week 10 | pytest-cov reports ≥85% coverage on _interview/ package |
| **Epic Complete** | End Week 10 | All 9 user stories done, all 36 ACs met, ready for Stage 5 review |

## Critical Path

```
Sprint 1 (Week 1)
  ↓ (Models + Port ready)
Sprint 2 (Weeks 2-3)
  ↓ (Group 1 scorers ready)
Sprint 3 (Weeks 4-5)
  ↓ (Group 2 scorers + gate ready)
Sprint 4 (Weeks 6-7)
  ├─ Parallel: Integration (3 SP)
  ├─ Parallel: MCP Tools (3 SP)
  └─ Parallel: SKILL.md (2 SP)
Sprint 5 (Weeks 8-10)
  ├─ Parallel: E2E Testing (3 SP from Story 8)
  └─ Parallel: Unit + Integration Testing (5 SP from Story 9)
```

The critical path is: **Sprint 1 → 2 → 3 → (4 + 5 in parallel) → Complete**.

Stories in Sprint 4-5 can be partially parallelized:
- Integration story (Story 8) and MCP tools (Story 6) can run in parallel in Sprint 4
- Testing story (Story 9) depends on all scorers (Sprints 2-3) but can run in parallel with MCP tools

## Dependencies Between Sprints

```
Sprint 1 OUTPUTS → Sprint 2 INPUT:
  - DimensionEvaluatorPort → Group 1 scorer implementations
  - DimensionScore model → Return type for all scorers
  - Scorer base class → Orchestration logic in all scorers

Sprint 2 OUTPUTS → Sprint 3 INPUT:
  - Group 1 scorers → Part of interview gate test fixtures
  - All 10 dimension implementations → Complete scorer orchestration

Sprint 3 OUTPUTS → Sprint 4 INPUT:
  - All 10 scorers + gate logic → MCP tool implementations
  - Gate logic → Orchestrator verdict routing

Sprint 4 OUTPUTS → Sprint 5 INPUT:
  - MCP tools + StageContext integration → Integration test fixtures
  - SKILL.md documentation → Test data for documentation validation
  - Orchestrator changes → E2E test scenarios
```

## Risk Mitigation Timeline

| Risk | Sprint | Mitigation |
|------|--------|-----------|
| **Coherence scorer tuning** | 2-3 | Start with simple heuristic; refine in feedback loop |
| **Clarity/precision NLP heuristics** | 3 | Use conservative rule-based scoring; flag for LLM refinement in Stage 5 |
| **Orchestrator conflicts** | 4 | Write integration tests in Sprint 4; coordinate with Stage 4 & 5 owners |
| **Coverage gaps** | 5 | Use pytest-cov to identify hotspots; write targeted tests |
| **E2E integration issues** | 5 | Write basic integration tests in Sprint 4 for early detection |

## Definition of Done (Per Sprint)

- ✓ All stories in sprint have passing unit tests
- ✓ All stories in sprint have integration tests (where applicable)
- ✓ All code merged to main branch with code review approval
- ✓ Documentation updated (docstrings, SKILL.md where applicable)
- ✓ No high-priority bugs reported in QA
- ✓ Acceptance criteria verified by developer + AI agents

---

**Document**: Roadmap & Sprint Plan | **Stage**: 4.5 | **Date**: 2025-03-14 | **Version**: 1.0
