# Epic 1: Plan Interview Stage — Functional & Non-Functional Requirements

## Functional Requirements (FRs)

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|-----------|--------|
| **FR-E1-001** | System shall define a DimensionType enum with 10 dimension identifiers (D1-D10). Enum values: SECTIONS_PRESENT, HEADER_FORMAT, ID_CONSISTENCY, OUTLINE_FLOW, ARTIFACT_COHERENCE, CLARITY_LEVEL, STAKEHOLDER_ALIGNMENT, REQUIREMENT_PRECISION, ASSUMPTION_VALIDATION, SUCCESS_METRICS. | P0 | None | [SUGGESTED] Domain model foundation |
| **FR-E1-002** | System shall provide a DimensionScore Pydantic model with fields: dimension_id (str), dimension_name (str), score (float, 0.0-1.0), pass (bool), findings (list[str]). All fields required. | P0 | FR-E1-001 | [SUGGESTED] Core data structure |
| **FR-E1-003** | System shall provide an InterviewConfig Pydantic model with fields: critical_threshold (float, default 0.8), advisory_threshold (float, default 0.6), timeout_seconds (int, default 60), dimensions_enabled (list[str]). Thresholds must be in range [0.0, 1.0]. | P0 | FR-E1-001 | [SUGGESTED] Configuration model |
| **FR-E1-004** | System shall provide an InterviewResult Pydantic model with fields: finding_id (str), stage_id (int), dimension_scores (list[DimensionScore]), gate_decision (str: APPROVED/PROVISIONAL/REJECTED), created_at (datetime), scored_by (str). | P0 | FR-E1-002 | [SUGGESTED] Result aggregation |
| **FR-E1-005** | System shall provide a GateDecision enum with three values: APPROVED (all critical thresholds met), PROVISIONAL (some advisory dimensions below threshold), REJECTED (one or more critical dimensions below threshold). | P0 | None | [SUGGESTED] Gate verdict classification |
| **FR-E1-006** | Dimension D1 (SECTIONS_PRESENT) shall check that all 9 required sections exist in the PRD artifact: Overview, Requirements, User Stories, Technical, Acceptance, Roadmap, JIRA, Tests, Verification. Score = (count_present / 9). Pass if score ≥ threshold. | P1 | FR-E1-001 | [SUGGESTED] Group 1 structural dimension |
| **FR-E1-007** | Dimension D2 (HEADER_FORMAT) shall validate that section headers follow the markdown convention (# or ##) and are non-empty. Score based on proportion of properly formatted headers. Deduct 0.1 per malformed header (min score 0.0). | P1 | FR-E1-001 | [SUGGESTED] Group 1 structural dimension |
| **FR-E1-008** | Dimension D3 (ID_CONSISTENCY) shall check that requirement IDs, user story IDs, and acceptance criterion IDs follow a consistent pattern (FR-E1-XXX, STORY-E1-XXX, AC-E1-XXX). Score = (count_consistent / count_total). Pass if ≥ threshold. | P1 | FR-E1-001 | [SUGGESTED] Group 1 structural dimension |
| **FR-E1-009** | Dimension D4 (OUTLINE_FLOW) shall validate that the PRD artifact has a clear logical progression: Overview → Requirements → Stories → Technical → Acceptance → Roadmap → JIRA → Tests → Verification. Score = 1.0 if order correct, 0.5 if sections present but out of order, 0.0 if sections missing. | P1 | FR-E1-001 | [SUGGESTED] Group 1 structural dimension |
| **FR-E1-010** | Dimension D5 (ARTIFACT_COHERENCE) shall measure semantic coherence across the PRD artifact using keyword overlap: compare terms used in Overview vs. Requirements vs. Technical. Score = (shared_terms / total_unique_terms). Penalize unrelated vocabulary. | P1 | FR-E1-001 | [SUGGESTED] Group 1 structural dimension |
| **FR-E1-011** | Dimension D6 (CLARITY_LEVEL) shall assess the clarity of prose in key sections (Overview, Requirements, User Stories). Measure sentence length (target <20 words), passive voice usage (target <20%), jargon density. Score penalty per violation: -0.05 per violating sentence (min 0.0). | P2 | FR-E1-001 | [SUGGESTED] Group 2 quality dimension |
| **FR-E1-012** | Dimension D7 (STAKEHOLDER_ALIGNMENT) shall validate that all user stories include at least one persona or stakeholder reference. Score = (stories_with_stakeholder / total_stories). Pass if ≥ threshold. | P2 | FR-E1-001 | [SUGGESTED] Group 2 quality dimension |
| **FR-E1-013** | Dimension D8 (REQUIREMENT_PRECISION) shall check that functional requirements use precise, testable language (avoid vague terms like "shall be", "might", "consider"). Score based on proportion of precise requirements. Penalize vague language. | P2 | FR-E1-001 | [SUGGESTED] Group 2 quality dimension |
| **FR-E1-014** | Dimension D9 (ASSUMPTION_VALIDATION) shall verify that the PRD explicitly lists assumptions or constraints in the Technical or Overview section. Count assumptions found and score = (assumptions_count / target_count). Pass if ≥ 3 assumptions found OR explicit "No assumptions" statement. | P2 | FR-E1-001 | [SUGGESTED] Group 2 quality dimension |
| **FR-E1-015** | Dimension D10 (SUCCESS_METRICS) shall check that the PRD defines measurable success criteria with baselines, targets, measurements, and business impact (per KPI table format). Score = (tables_with_all_4_fields / total_kpi_tables). Pass if ≥ threshold. | P2 | FR-E1-001 | [SUGGESTED] Group 2 quality dimension |
| **FR-E1-016** | System shall implement a DimensionEvaluator port (abstract protocol) with method: async evaluate(prd_artifact: dict, dimension_id: str, config: InterviewConfig) → DimensionScore. Concrete scorers implement this port. | P0 | FR-E1-001 | [SUGGESTED] Architecture pattern |
| **FR-E1-017** | System shall implement a Scorer class that orchestrates all 10 dimension evaluators. Scorer.evaluate_all() returns InterviewResult with all dimension scores and gate decision. Execution time <60 seconds total. | P1 | FR-E1-016 | [SUGGESTED] Orchestration component |
| **FR-E1-018** | System shall implement gate logic: PRD passes if (all critical dimensions score ≥ critical_threshold) AND (all advisory dimensions score ≥ advisory_threshold). Gate decision = APPROVED if passes, REJECTED if any critical fails, PROVISIONAL if only advisory dimensions below threshold. | P1 | FR-E1-017 | [SUGGESTED] Gate verdict logic |
| **FR-E1-019** | System shall integrate with StageContextPort: read Stage 4 artifact (PRD content), write Stage 4.5 artifact (interview result with dimension scores), enable Stage 5 to query interview results. Stage IDs: 4 (input), 45 (output, internal representation). | P1 | FR-E1-004 | Codebase analysis (StageContext pattern) |
| **FR-E1-020** | System shall provide MCP tool ai_architect_score_dimension(finding_id: str, stage_id: int, dimension_id: str, prd_content: str) that synchronously scores a single dimension and returns DimensionScore. Tool must handle errors and return clear error messages. | P1 | FR-E1-016 | [SUGGESTED] MCP integration |
| **FR-E1-021** | System shall provide MCP tool ai_architect_run_interview_gate(finding_id: str, stage_id: int) that executes the full interview gate (all 10 dimensions) and returns InterviewResult with gate decision. Tool must persist result to StageContext. | P1 | FR-E1-017 | [SUGGESTED] MCP integration |
| **FR-E1-022** | System shall provide MCP tool ai_architect_query_interview_results(finding_id: str) that retrieves all interview results for a finding from StageContext. Returns list[InterviewResult] in chronological order. | P1 | FR-E1-019 | [SUGGESTED] MCP integration |
| **FR-E1-023** | System shall update SKILL.md v3.0 to document Stage 4.5 orchestration: stage name, entry/exit criteria, artifact schemas, MCP tool signatures, dimension definitions. | P1 | All MCP tools | [SUGGESTED] Documentation |
| **FR-E1-024** | System shall update pipeline orchestrator (_orchestrator module) to insert Stage 4.5 between Stage 4 and Stage 5. Orchestrator must pass findings through interview gate and handle APPROVED/PROVISIONAL/REJECTED verdicts. | P1 | FR-E1-021 | Codebase analysis (orchestrator pattern) |
| **FR-E1-025** | System shall provide composition root (_composition.py) setup for Stage 4.5: register DimensionEvaluator implementations, inject StageContextPort, configure FastMCP tool registration. | P1 | FR-E1-016, FR-E1-019 | Codebase analysis (composition pattern) |

## Non-Functional Requirements (NFRs)

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| **NFR-E1-001** | **Execution latency per dimension** | <60 seconds (all 10 dims should complete in <60s total; avg <6s per dim) | Measure elapsed time for Scorer.evaluate_all() end-to-end |
| **NFR-E1-002** | **Scoring accuracy & consistency** | Dimension scorers produce identical scores when evaluated on same PRD artifact twice (100% consistency) | Run same dimension scorer twice on same artifact, compare results |
| **NFR-E1-003** | **Gate decision correctness** | No false negatives (defective PRDs incorrectly approved); <5% false positive rate (correct PRDs incorrectly rejected) | Manual audit of edge cases; Stage 5 feedback on PRD quality |
| **NFR-E1-004** | **Test coverage** | ≥85% code coverage (lines executed in tests) | Run pytest-cov on _interview/ package; report coverage % |
| **NFR-E1-005** | **Integration completeness** | All MCP tools functional, all StageContext reads/writes successful, full end-to-end flow verified | End-to-end integration tests from Stage 4 → 4.5 → 5 |
| **NFR-E1-006** | **Error handling robustness** | All dimension scorers handle malformed input gracefully (no unhandled exceptions); timeouts trigger fail-open gate logic | Test with empty artifacts, malformed JSON, missing sections |
| **NFR-E1-007** | **Type safety** | All domain models use Pydantic v2 with Field descriptions; no implicit type conversions | Type check entire _interview/ package with mypy |
| **NFR-E1-008** | **Documentation completeness** | All modules, classes, and functions have docstrings; SKILL.md documents all 10 dimensions and gate logic | Enforce docstrings in code review |

## Requirement Traceability

- **FR-E1-001 through FR-E1-005**: Domain model foundation (User Story 1: Dimension Model Definition)
- **FR-E1-006 through FR-E1-015**: Dimension implementations (User Stories 2-3: Group 1 & 2 dimensions)
- **FR-E1-016 through FR-E1-018**: Scorer + gate logic (User Story 4: Gate Logic)
- **FR-E1-019**: StageContext integration (User Story 5: StageContext Integration)
- **FR-E1-020 through FR-E1-022**: MCP tools (User Story 6: MCP Tools)
- **FR-E1-023 through FR-E1-025**: Documentation & orchestration (User Stories 7-8)
- **NFR-E1-001 through NFR-E1-008**: Quality gates across entire epic

---

**Document**: Functional & Non-Functional Requirements | **Stage**: 4.5 | **Date**: 2025-03-14 | **Version**: 1.0
