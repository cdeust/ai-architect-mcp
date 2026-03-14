# Epic 1: Plan Interview Stage (Stage 4.5) — PRD Overview

## Executive Summary

**Plan Interview Stage (Stage 4.5)** is a mandatory interrogation gate inserted between Stage 4 (PRD Generation) and Stage 5 (PRD Review). It performs a comprehensive 10-dimensional analysis of generated PRDs before they advance through the pipeline. This gate prevents low-quality PRDs from wasting review cycles and enforces architectural consistency across all findings.

### Stage Position in Pipeline
```
Stage 4 (PRD Generation)
          ↓
Stage 4.5 (Plan Interview) ← NEW
          ↓
Stage 5 (PRD Review)
```

## Problem Statement

Currently, generated PRDs flow directly from Stage 4 to Stage 5 without intermediate validation. This causes:
- **Wasted review cycles**: Stage 5 reviewers encounter incomplete or inconsistent PRDs
- **Late discovery of structural defects**: Issues caught in Stage 5 require regeneration (Stage 4 re-entry)
- **Inconsistent quality**: No standardized interrogation of PRD dimensions before advancement
- **Unclear gate criteria**: Review stage lacks clear pass/fail criteria

## Goals

| Goal | Rationale |
|------|-----------|
| **Prevent unfit PRDs from advancing** | Gate reduces rework by catching defects before review |
| **Standardize PRD quality assessment** | 10 dimensions provide objective, configurable criteria |
| **Accelerate Stage 5 review** | Pre-vetted PRDs require less rework time |
| **Enable fine-grained visibility** | Dimension scores reveal specific improvement areas |
| **Support iterative refinement** | Findings can re-enter Stage 4 with targeted improvement suggestions |

## Scope — What's In

### In Scope
- **10-dimension analysis model**: Comprehensive assessment of PRD structural and content fitness
- **Dimension evaluators**: Scorer implementations for all 10 dimensions (Group 1: 5 dims, Group 2: 5 dims)
- **Gate logic**: All-must-pass with configurable critical/advisory dimension thresholds
- **Score artifacts**: Persistence of dimension scores and gate decisions in StageContext
- **MCP tools**: FastMCP integration for dimension scoring and gate execution
- **SKILL.md v3.0**: Skill file updated with new stage orchestration
- **Orchestrator integration**: Pipeline orchestrator updated to invoke Stage 4.5
- **Full test suite**: Unit, integration, and acceptance tests (≥85% coverage)
- **Comprehensive documentation**: Requirements, architecture, user stories, acceptance criteria

### Out of Scope
- **Dimension tuning optimization**: Hyperparameter optimization deferred to Stage 5 feedback
- **Multi-stage backfill**: Applying interview gate retroactively to existing findings (future enhancement)
- **ML-based scoring**: Interview dimensions use rule-based scoring, not LLM classification
- **Stage 4 regeneration automation**: Findings failing Stage 4.5 require manual Stage 4 re-entry
- **Cross-finding dimension correlation**: Interview gate operates independently per-finding

## Key Features

### 1. 10-Dimensional Analysis
| Dimension Group | Dimensions | Purpose |
|-----------------|-----------|---------|
| **Group 1: Structural Completeness** | Sections present, header format, ID consistency, outline flow, artifact coherence | Validates PRD has all required sections with proper structure |
| **Group 2: Content Quality** | Clarity level, stakeholder alignment, requirement precision, assumption validation, success metrics | Evaluates actual content quality, not just presence |

Each dimension has:
- **Definition**: What aspect of the PRD is being evaluated
- **Scorer**: Rule-based algorithm to compute 0.0-1.0 score
- **Pass threshold**: Configurable minimum score (default: 0.7)
- **Impact level**: Critical (blocks gate) or Advisory (informs decision)

### 2. Gate Decision Model
```
PRD passes Stage 4.5 if:
- All critical dimensions score ≥ critical_threshold (default: 0.8)
- All advisory dimensions score ≥ advisory_threshold (default: 0.6)
- No evaluation errors or timeouts

Result: APPROVED, PROVISIONAL, or REJECTED
```

### 3. Artifact Enrichment
Interview stage:
- Reads Stage 4 artifact (generated PRD)
- Computes 10 dimension scores
- Writes enriched context for Stage 5:
  ```json
  {
    "interview_result": {
      "gate_decision": "APPROVED",
      "dimensions": [{
        "dimension_id": "D1",
        "name": "Sections Present",
        "score": 0.95,
        "pass": true,
        "findings": ["..."]
      }, ...],
      "dimension_summary": "9 critical pass, 1 advisory pass",
      "timestamp": "2025-03-14T...",
      "scored_by": "stage-4.5-scorer"
    }
  }
  ```

### 4. MCP Tool Integration
Three new FastMCP tools:
- `ai_architect_score_dimension(finding_id, stage_id, dimension_id, prd_content)` → DimensionScore
- `ai_architect_run_interview_gate(finding_id, stage_id)` → InterviewResult
- `ai_architect_query_interview_results(finding_id)` → list[InterviewResult]

## Quality Criteria

| Criterion | Requirement | Measurement |
|-----------|-------------|-------------|
| **Execution latency** | <60 seconds per dimension | Measure average scoring time |
| **Gate accuracy** | No false negatives (defective PRDs rejected) | Manual audit of edge cases |
| **Dimension reliability** | Consistent scores across reruns | Test score stability |
| **Test coverage** | ≥85% code coverage | pytest-cov report |
| **Integration completeness** | Fully integrated with StageContext | End-to-end tests |

## Team & Timeline

| Role | Size | Effort |
|------|------|--------|
| **Developers** | 1 | 7-10 weeks (~39 Fibonacci points) |
| **AI agents** | 2 | 7-10 weeks (dimension evaluation + orchestration) |

### Timeline Breakdown
- **Week 1**: Domain models + Scorer interface (Sprint 1: 8 SP)
- **Weeks 2-3**: Dimension 1-5 implementation (Sprint 2: 10 SP)
- **Weeks 4-5**: Dimension 6-10 + gate logic (Sprint 3: 10 SP)
- **Weeks 6-7**: Integration + MCP tools + SKILL.md (Sprint 4: 8 SP)
- **Weeks 8-10**: Test suite + documentation (Sprint 5: 5 SP)

## Dependencies

### Upstream (must exist)
- **Stage 4 output**: PRD artifacts in StageContext
- **StageContextPort**: Artifact storage interface
- **Finding model**: All findings have unique IDs

### Downstream (will depend on this)
- **Stage 5 (PRD Review)**: Consumes interview results to understand fit-for-review
- **Pipeline orchestrator**: Must route findings through Stage 4.5

## Success Metrics

| Metric | Target | Baseline |
|--------|--------|----------|
| PRD stage advancement time | <120s (end-to-end) | Not yet measured |
| False positive rate | <5% (PRDs rejected incorrectly) | N/A |
| Stage 5 rework reduction | 30% fewer regeneration requests | 100% (new gate) |
| Developer confidence in PRDs | 80%+ approval by Stage 5 reviewers | Not yet measured |
| Test coverage | ≥85% | 0% (new code) |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Dimension scoring too strict** | High false rejection rate, pipeline stalls | Start with advisory thresholds, tune based on Stage 5 feedback |
| **Evaluation timeouts** | Gate delays entire pipeline | Set 60s per-dimension timeout, fail-open on timeout |
| **Incomplete PRD detection fails** | Low-quality PRDs advance undetected | Integrate unit tests to validate each dimension scorer |
| **Artifact storage failures** | Gate cannot persist scores | Add retry logic + circuit breaker pattern |

## Definitions & Glossary

- **Critical dimension**: Blocks gate if score below threshold; non-negotiable quality bar
- **Advisory dimension**: Informs decision but doesn't block; suggests improvement areas
- **Gate decision**: Final verdict (APPROVED, PROVISIONAL, REJECTED)
- **Dimension score**: Normalized 0.0-1.0 score for a single aspect of the PRD
- **Interview result**: Complete artifact containing all dimension scores + gate decision
- **Stage 4.5 (Plan Interview)**: New mandatory interrogation stage between Generation and Review
- **StageContext**: Per-finding, per-stage artifact storage system
- **SKILL.md**: Skill file documenting stage orchestration and tool registrations

## Related Documents

- `prd-requirements.md`: Detailed functional & non-functional requirements
- `prd-user-stories.md`: 8-10 stories with acceptance criteria
- `prd-technical.md`: Architecture, domain models, implementation details
- `prd-acceptance.md`: Full acceptance criteria with KPI tables
- `prd-roadmap.md`: Sprint plan for 7-10 week delivery
- `prd-jira.md`: JIRA ticket export with task breakdown
- `prd-tests.md`: Complete test specifications with pytest code
- `prd-verification.md`: Structural integrity & claim verification

---

**Document**: PRD Overview | **Stage**: 4.5 (Plan Interview) | **Date**: 2025-03-14 | **Version**: 1.0
