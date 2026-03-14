# Epic 1: Plan Interview Stage — User Stories

## Story 1: Dimension Model Definition — 3 SP

**Title**: Define domain models for interview dimensions, scores, and gate decisions

**Description**:
As a developer, I want to define the core domain models (DimensionType, DimensionScore, InterviewConfig, InterviewResult, GateDecision) so that downstream components have a shared, type-safe contract for dimension scoring and gate verdicts.

**Acceptance Criteria**:

### AC-E1-001: DimensionType Enum
**GIVEN** a fresh codebase without dimension types defined
**WHEN** I define DimensionType as a Pydantic enum with 10 values
**THEN** the enum includes all 10 dimensions (D1-D10) with string identifiers matching the dimension names

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Enum completeness | 0/10 dims | 10/10 dims | Count enum values | Enables all dimension scorers to reference a single source of truth |
| Type safety | No validation | Pydantic validation | Type check with mypy | Prevents invalid dimension IDs in scorer calls |

### AC-E1-002: DimensionScore Model
**GIVEN** a DimensionScore model definition in the domain layer
**WHEN** I instantiate a DimensionScore with score=0.85, pass=True, findings=["Valid sections"]
**THEN** the model validates that score is in [0.0, 1.0], all fields are present, and the model serializes to JSON

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Field coverage | Missing fields | 5 required fields (dimension_id, name, score, pass, findings) | Inspect model definition | Ensures consistent dimension score representation |
| Serialization | No serialization | Round-trip JSON serialization | Test model_dump() and model_validate() | Enables artifact persistence in StageContext |

### AC-E1-003: InterviewConfig Model
**GIVEN** an InterviewConfig model with threshold fields
**WHEN** I create InterviewConfig(critical_threshold=0.8, advisory_threshold=0.6, timeout_seconds=60, dimensions_enabled=["D1", "D2"])
**THEN** the model validates that thresholds are in [0.0, 1.0] and timeout > 0

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Threshold validation | No validation | Pydantic validators enforce [0.0, 1.0] range | Attempt to set invalid threshold, expect ValueError | Prevents misconfiguration of critical decision thresholds |
| Configurability | Hard-coded values | All thresholds configurable | Check model fields with defaults | Enables fine-tuning of gate sensitivity per environment |

### AC-E1-004: InterviewResult Model
**GIVEN** an InterviewResult model aggregating all dimension scores
**WHEN** I create InterviewResult(finding_id="FIND-001", stage_id=45, dimension_scores=[...], gate_decision="APPROVED")
**THEN** the model includes all required fields and validates that gate_decision is a valid GateDecision value

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Completeness | Missing result summary | All fields present (finding_id, stage_id, dimension_scores, gate_decision, created_at, scored_by) | Inspect model definition | Provides complete audit trail of interview execution |
| Gate decision validation | No validation | Enum validation on gate_decision field | Try invalid decision value, expect ValueError | Prevents invalid gate verdicts from persisting |

### AC-E1-005: GateDecision Enum
**GIVEN** a GateDecision enum definition
**WHEN** I check the enum values
**THEN** the enum contains exactly three values: APPROVED, PROVISIONAL, REJECTED

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Verdict coverage | No verdict types | 3 distinct verdicts (APPROVED, PROVISIONAL, REJECTED) | Count enum values | Enables clear gate-decision classification |
| Semantic correctness | Ambiguous meanings | Clear semantics (APPROVED=all critical pass, PROVISIONAL=some advisory below, REJECTED=critical below) | Document in code | Reduces ambiguity in stage routing decisions |

---

## Story 2: Dimension Scorer Implementation (Group 1) — 5 SP

**Title**: Implement scorers for Group 1 dimensions (Structural Completeness)

**Description**:
As a developer, I want to implement DimensionEvaluator protocol and five Group 1 scorers (D1-D5: SECTIONS_PRESENT, HEADER_FORMAT, ID_CONSISTENCY, OUTLINE_FLOW, ARTIFACT_COHERENCE) so that structural completeness of PRDs can be measured objectively.

**Acceptance Criteria**:

### AC-E1-006: DimensionEvaluator Port
**GIVEN** a DimensionEvaluator abstract protocol in _adapters/ports.py
**WHEN** I check the protocol signature
**THEN** it defines an async evaluate(prd_artifact: dict, dimension_id: str, config: InterviewConfig) → DimensionScore method

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Port definition | No port | Abstract ABC with @abstractmethod | Verify ABC inheritance | Enforces contract for all dimension implementations |
| Asyncio support | No async | All evaluators are async functions | Check async/await syntax | Enables concurrent dimension evaluation |

### AC-E1-007: D1 (SECTIONS_PRESENT) Scorer
**GIVEN** a PRD artifact with 7 of 9 required sections
**WHEN** I run the SECTIONS_PRESENT scorer
**THEN** the score = 7/9 = 0.778, pass = (0.778 ≥ threshold), findings include list of missing sections

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Scoring accuracy | No scoring | Score = count_present / 9 | Test with various PRD artifacts | Objectively validates structural completeness |
| Error messages | None | findings field lists missing sections by name | Check findings list in DimensionScore | Enables targeted remediation of PRDs |

### AC-E1-008: D2 (HEADER_FORMAT) Scorer
**GIVEN** a PRD artifact with 8 markdown headers (# or ##) and 1 malformed header (###)
**WHEN** I run the HEADER_FORMAT scorer
**THEN** the score reflects proportion of correct headers, deduct 0.1 per malformed header

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Format validation | No validation | Detect # or ## headers, fail non-matching patterns | Test with various header styles | Ensures consistent markdown formatting |
| Penalty application | No penalties | Score deduction for malformed headers | Test edge case with multiple format violations | Discourages format inconsistency |

### AC-E1-009: D3 (ID_CONSISTENCY) Scorer
**GIVEN** a PRD artifact with 15 requirement IDs, 10 consistently named (FR-E1-001 format) and 5 inconsistent (FR-001, Req-001)
**WHEN** I run the ID_CONSISTENCY scorer
**THEN** the score = 10/15 = 0.667, findings identify non-conforming IDs

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Pattern recognition | No validation | Detect FR-E1-XXX, STORY-E1-XXX, AC-E1-XXX patterns | Test with mixed ID formats | Enforces consistent ID naming across PRDs |
| Coverage | Single pattern | Score all three ID types (FR, STORY, AC) | Test on complete PRD | Validates entire ID namespace |

### AC-E1-010: D4 (OUTLINE_FLOW) Scorer
**GIVEN** a PRD artifact with 9 sections in correct order
**WHEN** I run the OUTLINE_FLOW scorer
**THEN** the score = 1.0 (all sections in correct order); if out of order but present, score = 0.5; if missing sections, score = 0.0

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Order validation | No validation | Check section sequence (Overview → Requirements → Stories → Technical → ... → Verification) | Test with correct, scrambled, and partial orderings | Ensures logical flow of PRD content |
| Granularity | Binary pass/fail | Three-level scoring (correct=1.0, partial=0.5, missing=0.0) | Verify scoring logic | Provides nuanced feedback on structure issues |

### AC-E1-011: D5 (ARTIFACT_COHERENCE) Scorer
**GIVEN** a PRD artifact with high term overlap across Overview, Requirements, Technical sections
**WHEN** I run the ARTIFACT_COHERENCE scorer
**THEN** the score reflects semantic cohesion; high score for aligned terminology, low score for unrelated vocabulary

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Coherence measurement | No measurement | Calculate shared_terms / total_unique_terms | Test with coherent vs. incoherent PRDs | Detects misaligned or contradictory PRD content |
| Vocabulary analysis | No analysis | Extract and compare keywords from section text | Verify term extraction accuracy | Enables detection of semantic drift across sections |

---

## Story 3: Dimension Scorer Implementation (Group 2) — 5 SP

**Title**: Implement scorers for Group 2 dimensions (Content Quality)

**Description**:
As a developer, I want to implement five Group 2 scorers (D6-D10: CLARITY_LEVEL, STAKEHOLDER_ALIGNMENT, REQUIREMENT_PRECISION, ASSUMPTION_VALIDATION, SUCCESS_METRICS) so that content quality of PRDs can be measured objectively.

**Acceptance Criteria**:

### AC-E1-012: D6 (CLARITY_LEVEL) Scorer
**GIVEN** a Requirements section with sentences of varying lengths (some >20 words, some <20 words) and passive voice usage
**WHEN** I run the CLARITY_LEVEL scorer
**THEN** the score reflects proportion of sentences meeting clarity criteria, with penalties for long sentences and excessive passive voice

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Sentence analysis | No analysis | Parse sentences, count words, detect passive voice | Test on sample requirement text | Objectively measures readability |
| Penalty application | No penalties | Deduct 0.05 per violation (long sentence OR passive voice) | Verify penalty logic on test cases | Encourages clear, active voice requirements |

### AC-E1-013: D7 (STAKEHOLDER_ALIGNMENT) Scorer
**GIVEN** a User Stories section with 10 stories, 8 mentioning stakeholders and 2 without
**WHEN** I run the STAKEHOLDER_ALIGNMENT scorer
**THEN** the score = 8/10 = 0.8, findings list stories missing stakeholder references

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Story scanning | No scanning | Parse user stories, detect persona/stakeholder keywords | Test with standard "As a..." format | Ensures all stories map to stakeholders |
| Coverage reporting | No reporting | findings field lists story IDs without stakeholders | Verify findings list accuracy | Enables targeted story refinement |

### AC-E1-014: D8 (REQUIREMENT_PRECISION) Scorer
**GIVEN** requirements with mixed precision (some vague "shall be", some precise "returns 200 OK")
**WHEN** I run the REQUIREMENT_PRECISION scorer
**THEN** the score reflects proportion of precise, testable requirements; penalize vague language

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Vague term detection | No detection | Identify vague keywords (shall be, might, consider, possibly) | Test on requirement samples | Flags ambiguous language in requirements |
| Scoring model | No scoring | Score = (precise_reqs / total_reqs); deduct for vague language | Verify scoring on test fixtures | Ensures testable, unambiguous requirements |

### AC-E1-015: D9 (ASSUMPTION_VALIDATION) Scorer
**GIVEN** a Technical section that lists 3 explicit assumptions OR states "No assumptions"
**WHEN** I run the ASSUMPTION_VALIDATION scorer
**THEN** the score = 1.0 (assumptions documented); if <3 and no "No assumptions" statement, score = 0.0

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Assumption detection | No detection | Scan text for "Assumption:", "Assumes:", or "No assumptions" statements | Test with various phrasing | Ensures explicit assumption documentation |
| Threshold logic | No logic | Pass if (≥3 assumptions found) OR ("No assumptions" statement present) | Verify both passing conditions | Validates assumption transparency |

### AC-E1-016: D10 (SUCCESS_METRICS) Scorer
**GIVEN** a KPI table with 4 columns (Baseline, Target, Measurement, Business Impact) in Overview or Acceptance sections
**WHEN** I run the SUCCESS_METRICS scorer
**THEN** the score = (complete_tables / total_tables); complete table must have all 4 columns with non-empty values

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Table detection | No detection | Scan artifact for markdown tables with 4+ columns | Test with various table formats | Identifies KPI definitions |
| Field validation | No validation | Check that Baseline, Target, Measurement, Business Impact columns all populated | Verify column completeness | Ensures measurable success criteria |

---

## Story 4: Gate Logic Implementation — 5 SP

**Title**: Implement interview gate decision logic with threshold evaluation

**Description**:
As a developer, I want to implement the gate decision logic that evaluates all dimension scores against critical and advisory thresholds so that PRDs are automatically classified as APPROVED, PROVISIONAL, or REJECTED.

**Acceptance Criteria**:

### AC-E1-017: Gate Decision Algorithm
**GIVEN** 10 dimension scores with 7 critical and 3 advisory dimensions
**WHEN** all critical dimensions score ≥0.8 and all advisory ≥0.6
**THEN** gate decision = APPROVED

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Critical evaluation | No evaluation | All critical dimensions must score ≥ critical_threshold | Test with mixed critical scores | Enforces quality floor on critical dimensions |
| Advisory evaluation | No evaluation | All advisory dimensions must score ≥ advisory_threshold | Test with mixed advisory scores | Allows some flexibility on secondary dimensions |

### AC-E1-018: Provisional Verdict
**GIVEN** 10 dimension scores where all critical ≥0.8 but 2 advisory <0.6
**WHEN** I run the gate logic
**THEN** gate decision = PROVISIONAL; interpretation: "PRD acceptable but has improvement opportunities"

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Verdict clarity | No verdict | PROVISIONAL indicates pass-with-warnings state | Document verdict semantics | Communicates actionable feedback to PRD authors |
| Actionability | No actions | PROVISIONAL triggers Stage 5 review with lower scrutiny | Test routing logic downstream | Prevents unnecessary stage rejection |

### AC-E1-019: Rejection Verdict
**GIVEN** 10 dimension scores where at least one critical dimension scores <0.8
**WHEN** I run the gate logic
**THEN** gate decision = REJECTED; findings include which critical dimensions failed

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Rejection criteria | No criteria | Any critical dimension below threshold triggers REJECTED | Test threshold boundary conditions | Enforces mandatory quality bar |
| Feedback detail | No feedback | findings identify which critical dimensions caused rejection | Verify findings accuracy | Enables targeted PRD regeneration |

### AC-E1-020: Timeout Handling
**GIVEN** a dimension scorer that exceeds 60-second timeout
**WHEN** the dimension scorer times out
**THEN** the gate treats the timeout as a non-critical error; either skip the timed-out dimension (score=0.5) or fail-open with APPROVED (conservative) based on configuration

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Timeout detection | No timeout handling | Set 60-second per-dimension timeout; detect and handle exceeded time | Test with intentional delay in scorer | Prevents gate from blocking indefinitely |
| Failure mode | Crashes | Configurable behavior: skip dimension (score=0.5) or fail-open | Test timeout configuration options | Allows graceful degradation |

---

## Story 5: StageContext Integration — 3 SP

**Title**: Integrate interview stage with StageContextPort for artifact persistence

**Description**:
As a developer, I want to integrate the interview gate with StageContextPort so that dimension scores and gate decisions are persisted and queryable by downstream stages.

**Acceptance Criteria**:

### AC-E1-021: Stage 4 Artifact Loading
**GIVEN** a finding with ID "FIND-001" that has a Stage 4 artifact (PRD content)
**WHEN** I call context.load_artifact(stage_id=4, finding_id="FIND-001")
**THEN** the artifact is retrieved and contains the generated PRD with all sections

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Read access | No read access | Successfully load Stage 4 artifact | Test load operation on stored artifact | Enables interview stage to access PRD for scoring |
| Error handling | No error handling | Raise ArtifactNotFoundError if artifact missing | Test missing artifact scenario | Fails fast with clear error message |

### AC-E1-022: Stage 4.5 Artifact Persistence
**GIVEN** an InterviewResult with dimension scores and gate decision
**WHEN** I call context.save_artifact(stage_id=45, finding_id="FIND-001", artifact=interview_result_dict)
**THEN** the artifact is persisted and can be retrieved by Stage 5

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Write access | No write access | Successfully persist interview result | Test save operation | Enables downstream stages to access interview results |
| Data fidelity | No validation | Artifact round-trips correctly (write, read, deserialize) | Test serialization round-trip | Ensures data integrity across stage boundaries |

### AC-E1-023: Interview Result Querying
**GIVEN** multiple interview results for the same finding across different executions
**WHEN** I call context.query_artifacts(finding_id="FIND-001", query="interview dimensions")
**THEN** all matching interview results are returned in chronological order

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Query capability | No query | Retrieve all stage 4.5 artifacts for a finding | Test query operation | Enables audit trail of dimension scoring history |
| Ordering | Unordered | Results ordered by creation timestamp | Verify chronological order | Facilitates trend analysis across multiple interview runs |

---

## Story 6: MCP Tool Integration — 3 SP

**Title**: Register FastMCP tools for dimension scoring and gate execution

**Description**:
As a developer, I want to implement FastMCP tools (ai_architect_score_dimension, ai_architect_run_interview_gate, ai_architect_query_interview_results) so that the orchestrator and AI agents can trigger dimension scoring and gate verdicts.

**Acceptance Criteria**:

### AC-E1-024: score_dimension MCP Tool
**GIVEN** a valid finding_id, stage_id, dimension_id, and prd_content string
**WHEN** I call ai_architect_score_dimension(finding_id, stage_id, dimension_id, prd_content)
**THEN** the tool returns a DimensionScore object with score in [0.0, 1.0] and findings list

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Tool registration | Not registered | Tool appears in FastMCP registry with correct signature | Check MCP tool list | Enables MCP consumers to discover tool |
| Execution | No execution | Tool executes synchronously and returns result | Call tool, verify return type | Enables dimension scoring via MCP |

### AC-E1-025: run_interview_gate MCP Tool
**GIVEN** a valid finding_id and stage_id
**WHEN** I call ai_architect_run_interview_gate(finding_id, stage_id)
**THEN** the tool executes all 10 dimension scorers, persists the result to StageContext, and returns an InterviewResult with gate_decision

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Full execution | No execution | All 10 dimensions scored, gate decision computed | Call tool, verify all dimensions present | Enables complete gate execution via MCP |
| Persistence | No persistence | Result automatically saved to StageContext stage 45 | Verify artifact saved after tool call | Ensures interview results available to Stage 5 |

### AC-E1-026: query_interview_results MCP Tool
**GIVEN** a valid finding_id
**WHEN** I call ai_architect_query_interview_results(finding_id)
**THEN** the tool returns list[InterviewResult] from StageContext in chronological order

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Query execution | No query | List all interview results for the finding | Call tool, verify return type | Enables retrieval of interview history |
| Result ordering | Unordered | Results ordered by created_at timestamp | Verify timestamps are in ascending order | Facilitates audit trail analysis |

---

## Story 7: SKILL.md v3.0 Update — 2 SP

**Title**: Update SKILL.md to document Stage 4.5 orchestration and dimension specifications

**Description**:
As a developer, I want to update SKILL.md v3.0 with comprehensive documentation of Stage 4.5 so that other developers and AI agents understand the interview gate, dimension definitions, and MCP tools.

**Acceptance Criteria**:

### AC-E1-027: Stage 4.5 Section in SKILL.md
**GIVEN** an existing SKILL.md file documenting stages 0-10
**WHEN** I add a new "Stage 4.5 — Plan Interview" section
**THEN** the section includes: stage name, position in pipeline, entry criteria, exit criteria, artifact schema

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Documentation completeness | Missing section | All stage metadata documented | Verify section content | Provides baseline documentation for developers |
| Artifact schema | No schema | JSON schema or example artifact included | Show example InterviewResult | Clarifies data structure for downstream consumers |

### AC-E1-028: Dimension Definitions in SKILL.md
**GIVEN** 10 dimensions with scorers, pass thresholds, and impact levels
**WHEN** I document each dimension in SKILL.md
**THEN** each dimension has: ID, name, description, pass threshold (critical/advisory), scoring algorithm summary

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Coverage | No documentation | All 10 dimensions documented | Count documented dimensions | Enables understanding of gate behavior |
| Detail level | Vague | Clear definition of what each dimension measures and how | Read dimension descriptions | Supports debugging and configuration |

### AC-E1-029: MCP Tool Signatures in SKILL.md
**GIVEN** three MCP tools (score_dimension, run_interview_gate, query_interview_results)
**WHEN** I document each tool in SKILL.md
**THEN** each tool has: name, signature, description, example usage, return type

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Signature documentation | Missing | Full FastMCP function signatures with type hints | Verify signatures match implementation | Enables MCP integration by orchestrator |
| Examples | No examples | At least one example call per tool | Verify example calls are valid | Demonstrates tool usage for developers |

---

## Story 8: Orchestrator Integration & E2E Flow — 3 SP

**Title**: Integrate Stage 4.5 into the pipeline orchestrator and validate end-to-end flow

**Description**:
As a developer, I want to integrate Stage 4.5 into the pipeline orchestrator so that findings flow from Stage 4 through Stage 4.5 to Stage 5 with proper gate verdict routing.

**Acceptance Criteria**:

### AC-E1-030: Orchestrator Stage Insertion
**GIVEN** an existing orchestrator that routes findings through stages 0-10
**WHEN** I add Stage 4.5 to the orchestrator routing logic
**THEN** Stage 4 → Stage 4.5 → Stage 5 flow is established; stage 4.5 cannot be skipped

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Routing logic | No Stage 4.5 | Orchestrator invokes Stage 4.5 after Stage 4 completes | Trace orchestrator code path | Ensures gate is always executed |
| Immutability | Skippable | Stage 4.5 is mandatory (cannot be disabled or skipped) | Verify no skip logic for stage 45 | Enforces quality gate on all findings |

### AC-E1-031: Gate Verdict Routing
**GIVEN** Stage 4.5 returns verdicts (APPROVED, PROVISIONAL, REJECTED)
**WHEN** the orchestrator receives the verdict
**THEN** APPROVED/PROVISIONAL findings advance to Stage 5; REJECTED findings are routed to Stage 4 re-entry queue with improvement suggestions

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Verdict handling | No handling | Orchestrator routes based on gate_decision value | Test routing with all three verdicts | Enables proper finding flow based on quality |
| Re-entry support | Not supported | REJECTED findings can re-enter Stage 4 | Test REJECTED routing logic | Supports iterative PRD improvement |

### AC-E1-032: End-to-End Flow
**GIVEN** a finding with generated PRD in Stage 4 artifact
**WHEN** I run the full pipeline from Stage 4 → 4.5 → 5
**THEN** the finding successfully flows through all stages; Stage 5 receives enriched context with interview results; no artifacts are lost

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Flow correctness | No flow | Finding progresses through 4 → 4.5 → 5 | Run e2e test, verify stage progression | Validates core pipeline integration |
| Context preservation | Lost context | All Stage 4 + Stage 4.5 artifacts available to Stage 5 | Load both stage 4 and 45 artifacts, verify content | Enables Stage 5 to use interview results |

---

## Story 9: Comprehensive Test Suite — 5 SP

**Title**: Implement unit, integration, and acceptance tests for the interview stage

**Description**:
As a developer, I want to implement a comprehensive test suite covering all dimensions, gate logic, artifact persistence, and MCP tools so that the interview stage is production-ready with ≥85% coverage.

**Acceptance Criteria**:

### AC-E1-033: Unit Tests for Dimensions
**GIVEN** 10 dimension scorer implementations
**WHEN** I run the unit test suite
**THEN** each dimension has ≥3 test cases covering happy path, edge cases (empty input, missing sections), and error scenarios

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Coverage | 0% | All 10 dimensions tested | Count test cases per dimension | Validates scorer correctness |
| Edge cases | Not covered | Empty artifact, missing sections, malformed input tested | Verify edge case tests exist | Ensures robustness to degenerate inputs |

### AC-E1-034: Gate Logic Tests
**GIVEN** gate decision algorithm with threshold logic
**WHEN** I run gate logic tests
**THEN** tests cover all three verdicts (APPROVED, PROVISIONAL, REJECTED) with various threshold combinations

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Verdict coverage | Untested | All three verdicts exercised | Run gate logic test suite | Validates decision algorithm correctness |
| Threshold sensitivity | Not tested | Tests with scores at threshold boundaries (0.79, 0.80, 0.81) | Verify boundary tests | Ensures correct threshold comparison |

### AC-E1-035: Integration Tests
**GIVEN** full interview stage with StageContext and MCP tools
**WHEN** I run integration tests
**THEN** tests cover artifact read from Stage 4, all 10 dimensions scored, result persisted to Stage 4.5, and Stage 5 can query results

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| End-to-end coverage | Not covered | Full Stage 4 → 4.5 → 5 flow tested | Run e2e integration test | Validates production flow |
| Persistence validation | Not tested | Verify artifact round-trip (save → load) | Test artifact serialization | Ensures data integrity |

### AC-E1-036: Test Coverage
**GIVEN** the entire _interview/ package with all implementations
**WHEN** I run pytest-cov on the package
**THEN** code coverage is ≥85% (lines covered / total lines)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Coverage % | 0% | ≥85% | Run pytest-cov report | Meets NFR-E1-004 requirement |
| Critical path coverage | Not tested | All dimension scorers, gate logic, MCP tools have >90% coverage | Inspect coverage report hotspots | Ensures critical code is well-tested |

---

## Story Point Summary

| Story | Title | SP | Group |
|-------|-------|-----|-------|
| 1 | Dimension Model Definition | 3 | Prerequisite |
| 2 | Dimension Scorer (Group 1) | 5 | Core Implementation |
| 3 | Dimension Scorer (Group 2) | 5 | Core Implementation |
| 4 | Gate Logic | 5 | Core Implementation |
| 5 | StageContext Integration | 3 | Integration |
| 6 | MCP Tools | 3 | Integration |
| 7 | SKILL.md Update | 2 | Documentation |
| 8 | Orchestrator Integration | 3 | Integration |
| 9 | Test Suite | 5 | Quality |
| **TOTAL** | **9 stories** | **34 SP** | - |

---

**Document**: User Stories | **Stage**: 4.5 | **Date**: 2025-03-14 | **Version**: 1.0
