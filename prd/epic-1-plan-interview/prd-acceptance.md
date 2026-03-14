# Epic 1: Plan Interview Stage — Acceptance Criteria (Detailed)

## AC-E1-001 through AC-E1-036 Complete Specifications

This document provides the detailed acceptance criteria referenced in user stories. Each AC includes GIVEN-WHEN-THEN format plus a KPI table with Baseline, Target, Measurement, and Business Impact.

---

## Story 1: Dimension Model Definition (AC-E1-001 through AC-E1-005)

### AC-E1-001: DimensionType Enum Completeness

**GIVEN** a fresh codebase without dimension types defined
**WHEN** I define DimensionType as a string enum in `_interview/models.py`
**THEN** the enum includes all 10 dimensions with correct identifiers:
- D1-sections-present
- D2-header-format
- D3-id-consistency
- D4-outline-flow
- D5-artifact-coherence
- D6-clarity-level
- D7-stakeholder-alignment
- D8-requirement-precision
- D9-assumption-validation
- D10-success-metrics

**Validation**: Enum values match dimension IDs; enum is importable and usable in type hints

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Enum completeness | 0/10 values | 10/10 values | Count DimensionType enum members | Prevents incomplete dimension set from being deployed |
| Type safety | No type validation | Mypy validates enum usage | Run mypy on _interview/ package | Catches invalid dimension references at compile time |
| Documentation | No docstrings | Enum members have docstrings | Verify docstring presence | Enables IDE autocomplete and developer understanding |

---

### AC-E1-002: DimensionScore Model Structure

**GIVEN** a DimensionScore Pydantic model definition
**WHEN** I instantiate DimensionScore(dimension_id="D1-sections-present", dimension_name="Sections Present", score=0.85, pass=True, findings=[])
**THEN** the model:
- Accepts all 5 required fields
- Validates score is in [0.0, 1.0]
- Produces identical output when serialized and deserialized (JSON round-trip)
- Has a clear default example in Config

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Field coverage | Missing fields | 5 required fields present | Count model fields | Ensures all dimension score info available |
| Validation | No validation | Pydantic validators on score range | Test invalid score (1.5), expect ValueError | Prevents out-of-range scores from persisting |
| Serialization | Ad-hoc JSON | Pydantic model_dump(mode="json") | Test round-trip serialization | Enables artifact storage and transmission |
| Documentation | No examples | json_schema_extra example in Config | Verify Config.example field | Helps developers understand expected format |

---

### AC-E1-003: InterviewConfig Model Validation

**GIVEN** an InterviewConfig model with configurable thresholds and timeout
**WHEN** I create InterviewConfig(critical_threshold=0.8, advisory_threshold=0.6, timeout_seconds=60, dimensions_enabled=["D1-sections-present", "D2-header-format"])
**THEN** the model:
- Accepts all 4 fields with sensible defaults
- Validates thresholds are in [0.0, 1.0]
- Validates critical_threshold >= advisory_threshold
- Validates timeout_seconds > 0

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Configurability | Hard-coded values | All thresholds configurable fields | Check model has threshold fields | Enables fine-tuning per environment |
| Threshold ordering | No validation | critical >= advisory validator | Test critical < advisory, expect ValueError | Prevents illogical threshold configuration |
| Timeout validation | No validation | timeout_seconds > 0 validator | Test timeout=0, expect ValueError | Prevents infinite waits |
| Default values | Missing | Sensible defaults (critical=0.8, advisory=0.6, timeout=60) | Verify defaults in field definitions | Allows creation without explicit configuration |

---

### AC-E1-004: InterviewResult Model Completeness

**GIVEN** an InterviewResult model aggregating all dimension scores and gate decision
**WHEN** I create InterviewResult(finding_id="FIND-001", stage_id=45, dimension_scores=[...], gate_decision="approved")
**THEN** the model:
- Includes all required fields (finding_id, stage_id, dimension_scores, gate_decision, created_at, scored_by)
- Auto-generates created_at timestamp if not provided
- Validates gate_decision against GateDecision enum
- Can be serialized to JSON and deserialized back

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Field completeness | Missing result summary | 6 required fields | Count InterviewResult fields | Provides complete audit trail |
| Gate decision validation | No validation | Enum validation on gate_decision field | Test invalid decision ("approved_with_warnings"), expect ValueError | Prevents invalid verdicts |
| Timestamp auto-generation | Manual timestamps | created_at defaults to UTC now() | Check timestamp without explicit value | Enables automatic creation time tracking |
| JSON serialization | Ad-hoc | model_dump(mode="json") round-trip | Test serialization cycle | Enables artifact persistence |

---

### AC-E1-005: GateDecision Enum Values

**GIVEN** a GateDecision enum definition
**WHEN** I inspect the enum
**THEN** it contains exactly 3 values with clear semantics:
- APPROVED: "approved" — All critical pass, all advisory pass
- PROVISIONAL: "provisional" — All critical pass, some advisory below threshold
- REJECTED: "rejected" — Any critical dimension below threshold

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Verdict coverage | No verdict types | 3 distinct values | Count enum members | Captures all gate outcomes |
| Semantic clarity | Ambiguous names | Clear names with semantic documentation | Read enum docstrings | Reduces confusion in verdict handling |
| String representation | No convention | String enum (str, Enum) | Verify isinstance(v, str) | Enables JSON serialization and routing logic |

---

## Story 2: Dimension Scorer (Group 1) (AC-E1-006 through AC-E1-011)

### AC-E1-006: DimensionEvaluator Port Definition

**GIVEN** a DimensionEvaluator port in `_interview/ports.py`
**WHEN** I check the abstract base class
**THEN** it:
- Is an ABC with @abstractmethod decorator
- Defines async evaluate(prd_artifact: dict, dimension_id: str, config: InterviewConfig) → DimensionScore
- Has clear docstring explaining the contract

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Port definition | No port | ABC with @abstractmethod | Verify ABC inheritance | Enforces contract for all scorers |
| Method signature | Inconsistent | Single evaluate method with 3 args | Count abstract methods | Unifies dimension evaluator interface |
| Asyncio support | No async | async/await in signature | Check method keyword | Enables concurrent evaluation |
| Documentation | Missing | Docstring with Args, Returns, Raises | Verify docstring sections | Clarifies port expectations |

---

### AC-E1-007: D1 (SECTIONS_PRESENT) Scorer Implementation

**GIVEN** a PRD artifact with sections list:
```json
{
  "sections": [
    {"name": "Overview"},
    {"name": "Requirements"},
    {"name": "Technical"},
    {"name": "Acceptance"}
  ]
}
```
**WHEN** I run SectionsPresentScorer.evaluate(artifact, "D1-sections-present", config)
**THEN**:
- Score = 4 / 9 = 0.444
- pass = False (0.444 < 0.8 critical threshold)
- findings = ["Missing section: User Stories", "Missing section: Roadmap", ...]

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Scoring accuracy | No scoring | score = present / 9 | Test with 7/9 sections, expect score ~0.778 | Objectively measures structural completeness |
| Pass determination | Manual | pass = (score >= threshold) | Test boundary (0.79, 0.80, 0.81) | Enables automated gate verdicts |
| Finding detail | None | List missing sections by name | Check findings array content | Guides PRD author on remediation |
| Robustness | No error handling | Handle empty/malformed sections list | Test with empty sections, expect score=0.0 | Degrades gracefully |

---

### AC-E1-008: D2 (HEADER_FORMAT) Scorer Implementation

**GIVEN** a PRD content string with 8 valid markdown headers and 1 invalid (###):
```
# Valid H1
## Valid H2
### Invalid H3 (should be # or ##)
# Another Valid
...
```
**WHEN** I run HeaderFormatScorer.evaluate(artifact, "D2-header-format", config)
**THEN**:
- Score = 1.0 - (1 malformed * 0.1) = 0.9
- pass = True (0.9 >= 0.8)
- findings = ["1 malformed headers found"] or empty if all valid

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Header detection | No detection | Find lines starting with # or ## | Test with various markdown | Identifies markdown headers |
| Format validation | No validation | Validate header has space after #/## | Test malformed headers | Enforces consistent markdown |
| Penalty application | Manual | Deduct 0.1 per malformed header | Test with 3 malformed, expect max 0.7 score | Discourages format violations |
| Edge case handling | Crashes | Handle no headers found (score=0.0) | Test content without headers | Degrades gracefully |

---

### AC-E1-009: D3 (ID_CONSISTENCY) Scorer Implementation

**GIVEN** a PRD artifact with mixed ID formats:
```
FR-E1-001, FR-E1-002, FR-001, Req-A, STORY-E1-01, STORY-01, AC-E1-001
```
**WHEN** I run IDConsistencyScorer.evaluate(artifact, "D3-id-consistency", config)
**THEN**:
- Total IDs found: 7
- Consistent IDs (matching FR-E1-XXX, STORY-E1-XX, AC-E1-XXX): 5
- Score = 5 / 7 = 0.714
- pass = False (0.714 < 0.8)
- findings = ["Found 2 non-conforming IDs"]

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Pattern matching | No matching | Regex patterns for FR-E1-XXX, STORY-E1-XX, AC-E1-XXX | Test with mixed formats | Identifies ID format violations |
| Scoring | Manual | score = consistent / total | Test boundary (4/5 vs 5/6) | Measures format consistency |
| Coverage | Single pattern | All three ID types (FR, STORY, AC) scored | Test partial ID sets | Validates entire ID namespace |
| Error handling | Crashes | Handle no IDs found (score=0.0) | Test content without IDs | Degrades gracefully |

---

### AC-E1-010: D4 (OUTLINE_FLOW) Scorer Implementation

**GIVEN** a PRD with 9 sections in correct order: Overview → Requirements → User Stories → Technical → Acceptance → Roadmap → JIRA → Tests → Verification
**WHEN** I run OutlineFlowScorer.evaluate(artifact, "D4-outline-flow", config)
**THEN**:
- Score = 1.0 (all sections present and in order)
- pass = True

**AND GIVEN** sections present but scrambled (Requirements, Overview, Technical, ...)
**WHEN** I run the scorer
**THEN**:
- Score = 0.5 (all present, but out of order)
- pass = False (0.5 < 0.8)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Order validation | No validation | Check section sequence matches expected order | Test correct vs scrambled | Ensures logical flow |
| Granularity | Binary | Three-level scoring (1.0=correct, 0.5=partial, 0.0=missing) | Test all three outcomes | Provides nuanced feedback |
| Missing handling | Unknown | Score=0.0 if any required section missing | Test partial sections | Detects incomplete PRDs |
| Robustness | No error handling | Handle empty sections list | Test empty/null sections | Degrades gracefully |

---

### AC-E1-011: D5 (ARTIFACT_COHERENCE) Scorer Implementation

**GIVEN** a PRD artifact with high term overlap:
- Overview mentions: "authentication", "token", "security", "user"
- Requirements mention: "authentication", "token", "secure", "user"
- Technical mention: "authentication", "token", "encryption", "user"

**WHEN** I run ArtifactCoherenceScorer.evaluate(artifact, "D5-artifact-coherence", config)
**THEN**:
- Shared terms: {authentication, token, user} = 3 terms
- All unique terms: {authentication, token, security, user, secure, encryption} = 6 terms
- Score = 3 / 6 = 0.5
- pass = True (0.5 >= 0.6 advisory threshold)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Keyword extraction | No extraction | Extract words >4 chars, filter stop words | Test extraction on sample text | Identifies important terminology |
| Overlap measurement | Manual | shared_terms / total_unique_terms | Test with high vs low coherence | Measures semantic alignment |
| Section extraction | Ad-hoc | Parse content for Overview, Requirements, Technical sections | Test with complete vs partial content | Enables section-wise analysis |
| Robustness | No error handling | Handle missing sections (default to 0.5) | Test partial content | Degrades gracefully |

---

## Story 3: Dimension Scorer (Group 2) (AC-E1-012 through AC-E1-016)

### AC-E1-012: D6 (CLARITY_LEVEL) Scorer Implementation

**GIVEN** a Requirements section with mixed sentence quality:
- "The system shall provide user authentication with OAuth 2.0." (14 words, active)
- "Token refresh functionality must be implemented to ensure session continuity throughout the user's interaction with the system." (18 words, passive)
- "Error handling should be considered as an implementation detail that might affect performance." (15 words, passive + vague)

**WHEN** I run ClarityLevelScorer.evaluate(artifact, "D6-clarity-level", config)
**THEN**:
- Sentence 1: 14 words (good), active (good), no penalty
- Sentence 2: 18 words (good), passive voice (penalty -0.05)
- Sentence 3: 15 words (good), passive + vague keywords (penalties)
- Score = (3 - penalties) / 3 = ~0.9

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Sentence parsing | No parsing | Split on punctuation (., ?, !) | Test on multi-sentence text | Enables sentence-by-sentence analysis |
| Length checking | Manual | Count words, target <20 words | Test 19-word vs 21-word sentences | Identifies verbose requirements |
| Voice detection | No detection | Heuristic: detect "is", "are", "was" patterns in requirement | Test active vs passive voice | Encourages clear, direct language |
| Penalty application | Manual | Deduct 0.05 per violation | Test with 3 violations, expect 0.85 score | Discourages clarity violations |

---

### AC-E1-013: D7 (STAKEHOLDER_ALIGNMENT) Scorer Implementation

**GIVEN** a User Stories section with 10 stories, 8 with stakeholder mentions:
```
STORY-E1-01: As an admin, I want to...
STORY-E1-02: As a user, I want to...
STORY-E1-03: The system shall provide...  <- No stakeholder
STORY-E1-04: As a developer, I want to...
...
STORY-E1-10: Error handling must work...  <- No stakeholder
```

**WHEN** I run StakeholderAlignmentScorer.evaluate(artifact, "D7-stakeholder-alignment", config)
**THEN**:
- Stories with stakeholder mentions: 8
- Total stories: 10
- Score = 8 / 10 = 0.8
- pass = True (0.8 >= 0.6 advisory threshold)
- findings = ["STORY-E1-03 lacks stakeholder", "STORY-E1-10 lacks stakeholder"]

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Story detection | No detection | Parse text for STORY-E1-XX pattern | Test story extraction | Identifies story count |
| Stakeholder detection | No detection | Look for "As a", persona keywords, role names | Test various persona formats | Flags stories without stakeholders |
| Scoring | Manual | score = with_stakeholder / total | Test boundary (4/5 vs 5/6) | Measures stakeholder coverage |
| Finding detail | None | List story IDs lacking stakeholders | Check findings array | Guides targeted improvements |

---

### AC-E1-014: D8 (REQUIREMENT_PRECISION) Scorer Implementation

**GIVEN** a Requirements section with mixed precision:
```
FR-E1-001: The system shall provide user authentication.
FR-E1-002: The system might implement token refresh.
FR-E1-003: User login must return HTTP 200 status with JWT token.
FR-E1-004: Consider adding session timeout for security.
```

**WHEN** I run RequirementPrecisionScorer.evaluate(artifact, "D8-requirement-precision", config)
**THEN**:
- Precise requirements: FR-E1-001 (no vague keywords), FR-E1-003 (testable/specific)
- Imprecise: FR-E1-002 ("might" = vague), FR-E1-004 ("consider" = vague)
- Score = 2 / 4 = 0.5
- pass = False (0.5 < 0.7)
- findings = ["Found vague keywords in FR-E1-002, FR-E1-004"]

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Vague keyword detection | No detection | Identify "shall be", "might", "consider", "possibly", "should" | Test on requirement samples | Flags ambiguous language |
| Requirement parsing | Ad-hoc | Parse text for FR-E1-XXX requirements | Test requirement extraction | Identifies requirements set |
| Scoring | Manual | score = precise / total | Test boundary cases | Measures testability |
| Error handling | Crashes | Handle no requirements found (score=0.5 default) | Test content without FR IDs | Degrades gracefully |

---

### AC-E1-015: D9 (ASSUMPTION_VALIDATION) Scorer Implementation

**GIVEN** a Technical section with explicit assumptions:
```
## Assumptions
- Assumption 1: All users have stable internet connectivity
- Assumption 2: Authentication service will respond within 1 second
- Assumption 3: Database will maintain 99.9% uptime SLA
```

**WHEN** I run AssumptionValidationScorer.evaluate(artifact, "D9-assumption-validation", config)
**THEN**:
- Assumptions found: 3
- Score = 1.0
- pass = True

**AND GIVEN** no assumptions listed but explicit "No assumptions" statement
**WHEN** I run the scorer
**THEN**:
- Score = 1.0 (explicit statement counts as validation)
- pass = True

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Assumption detection | No detection | Search for "Assumption:", "Assumes:", bullet lists under "Assumptions" | Test various formats | Identifies assumption documentation |
| Count validation | Manual | Count assumptions found | Test with 1, 2, 3, 4 assumptions | Measures assumption documentation level |
| No-assumptions handling | Unknown | Accept "No assumptions" statement as valid documentation | Test explicit no-assumptions statement | Validates assumption clarity |
| Threshold logic | Hard-coded | Pass if (>=3 assumptions) OR ("No assumptions" statement) | Test boundary at 3 assumptions | Ensures explicit assumption handling |

---

### AC-E1-016: D10 (SUCCESS_METRICS) Scorer Implementation

**GIVEN** KPI tables in Overview section with 4-column format (Baseline, Target, Measurement, Business Impact):
```
| Criterion | Baseline | Target | Measurement | Business Impact |
|-----------|----------|--------|-------------|-----------------|
| Execution latency | <5s | <1s | E2E test timing | Improves user experience |
| Coverage | 70% | 85% | pytest-cov report | Increases reliability |
```

**WHEN** I run SuccessMetricsScorer.evaluate(artifact, "D10-success-metrics", config)
**THEN**:
- Tables with 4 required columns found: 1
- All columns populated: Yes
- Score = 1 / total_tables = 1.0
- pass = True (1.0 >= 0.75)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Table detection | No detection | Find markdown tables (pipe-delimited rows) | Test on various table formats | Identifies KPI definitions |
| Column validation | No validation | Verify presence of Baseline, Target, Measurement, Business Impact | Test with 3 vs 4 columns | Ensures complete KPI definition |
| Completeness check | No check | Verify all 4 columns have non-empty values | Test with empty cells | Ensures filled-out KPI tables |
| Scoring | Manual | score = complete_tables / total_tables | Test with partial completion | Measures KPI coverage |

---

## Story 4: Gate Logic (AC-E1-017 through AC-E1-020)

### AC-E1-017: Gate Decision Algorithm (All Critical Pass)

**GIVEN** 10 dimension scores:
- D1-D4, D6, D8, D10 (critical): all score 0.85
- D5, D7, D9 (advisory): all score 0.75
- config.critical_threshold = 0.8, advisory_threshold = 0.6

**WHEN** I call InterviewGate.decide(dimension_scores, config)
**THEN** gate_decision = APPROVED

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Critical evaluation | No evaluation | All critical dims >= critical_threshold | Test with mixed scores | Enforces quality floor |
| Advisory evaluation | No evaluation | All advisory dims >= advisory_threshold | Test advisory below threshold | Allows secondary flexibility |
| Verdict accuracy | Manual | Gate returns correct verdict for all three cases | Test APPROVED/PROVISIONAL/REJECTED paths | Ensures correct gate logic |

---

### AC-E1-018: Provisional Verdict (Advisory Below Threshold)

**GIVEN** 10 dimension scores where:
- All 7 critical dimensions score >= 0.8 (pass)
- 2 of 3 advisory dimensions score < 0.6 (fail)

**WHEN** I call InterviewGate.decide(dimension_scores, config)
**THEN** gate_decision = PROVISIONAL

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Provisional logic | No logic | PROVISIONAL if critical pass AND advisory has failures | Test specific scenario | Communicates pass-with-warnings |
| Interpretation | Unclear | PROVISIONAL = acceptable with improvement suggestions | Document in code | Guides downstream handling |

---

### AC-E1-019: Rejection Verdict (Critical Below Threshold)

**GIVEN** 10 dimension scores where:
- D1 (critical) scores 0.75 (below 0.8)
- All others score >= their thresholds

**WHEN** I call InterviewGate.decide(dimension_scores, config)
**THEN** gate_decision = REJECTED

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Rejection criteria | No criteria | Any critical below threshold = REJECTED | Test single critical failure | Enforces quality floor |
| Multiple failures | Unknown | REJECTED verdict same for 1 or N critical failures | Test with multiple failures | Simplifies verdict handling |

---

### AC-E1-020: Timeout Handling

**GIVEN** a dimension scorer that hangs for >60 seconds
**WHEN** the interview gate detects timeout
**THEN** the gate either:
- Skips the timed-out dimension (treats as score=0.5, pass=False)
- Fails open with APPROVED verdict (conservative, allows manual review)

Based on configuration: `config.timeout_mode = "skip" | "fail_open"`

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Timeout detection | No detection | Set asyncio timeout, catch TimeoutError | Test with intentional delay | Prevents indefinite waits |
| Failure mode | Crashes | Configurable behavior (skip or fail_open) | Test both timeout modes | Allows graceful degradation |
| Error reporting | None | Include timeout in findings | Check findings list for timeout message | Enables debugging |

---

## Story 5: StageContext Integration (AC-E1-021 through AC-E1-023)

### AC-E1-021: Stage 4 Artifact Loading

**GIVEN** a StageContext with a Stage 4 artifact persisted for finding "FIND-001"
**WHEN** I call context.load_artifact(stage_id=4, finding_id="FIND-001")
**THEN**:
- Artifact is successfully retrieved
- Artifact contains PRD with sections and content
- No errors raised

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Read access | No read access | Successfully load stage 4 artifact | Test load operation | Enables reading PRD input |
| Error handling | No error handling | Raise ArtifactNotFoundError if missing | Test missing artifact scenario | Fails fast with clear error |
| Data format | Unknown | Artifact is dict with PRD structure | Verify structure matches Stage 4 output | Ensures compatibility |

---

### AC-E1-022: Stage 4.5 Artifact Persistence

**GIVEN** an InterviewResult object
**WHEN** I call context.save_artifact(stage_id=45, finding_id="FIND-001", artifact=result_dict)
**THEN**:
- Artifact is persisted to stage 45
- Artifact can be retrieved with load_artifact()
- Data round-trips correctly (serialize → deserialize → identical)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Write access | No write access | Successfully persist stage 4.5 artifact | Test save operation | Enables writing interview results |
| Data fidelity | Ad-hoc | Artifact round-trips correctly | Test serialization cycle | Ensures no data loss |
| Stage ID handling | No validation | Save to stage_id=45 correctly | Verify artifact stored with right stage | Enables correct retrieval |

---

### AC-E1-023: Interview Result Querying

**GIVEN** multiple interview results for finding "FIND-001" from different executions (created at times T1, T2, T3)
**WHEN** I call context.query_artifacts(finding_id="FIND-001", query="interview dimensions")
**THEN**:
- All stage 4.5 artifacts returned
- Results ordered chronologically (T1, T2, T3)
- Results include stage_id=45 metadata

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Query capability | No query | Retrieve all stage 4.5 artifacts for finding | Test query operation | Enables audit trail access |
| Ordering | Unordered | Results ordered by created_at timestamp | Verify timestamps in ascending order | Facilitates trend analysis |
| Filtering | No filtering | Only stage 4.5 artifacts returned | Test query excludes other stages | Prevents unrelated results |

---

## Story 6: MCP Tools (AC-E1-024 through AC-E1-026)

### AC-E1-024: score_dimension MCP Tool

**GIVEN** valid parameters:
- finding_id="FIND-001"
- stage_id=4
- dimension_id="D1-sections-present"
- prd_content='{"sections": [{"name": "Overview"}, ...]}'

**WHEN** I call ai_architect_score_dimension(finding_id, stage_id, dimension_id, prd_content)
**THEN**:
- Tool returns DimensionScore as dict
- score is in [0.0, 1.0]
- findings list is present
- No unhandled exceptions

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Tool registration | Not registered | FastMCP tool with correct signature | Check tool in MCP registry | Enables MCP integration |
| Execution | No execution | Tool executes synchronously and returns result | Call tool, verify return type | Enables dimension scoring |
| Error handling | Crashes | Tool returns error dict on exception | Test with malformed JSON | Degrades gracefully |
| Return format | Ad-hoc | Pydantic model_dump(mode="json") | Verify JSON structure | Enables client integration |

---

### AC-E1-025: run_interview_gate MCP Tool

**GIVEN** valid parameters:
- finding_id="FIND-001"
- stage_id=4

**WHEN** I call ai_architect_run_interview_gate(finding_id, stage_id)
**THEN**:
- All 10 dimension scorers execute
- Gate decision is computed
- InterviewResult is persisted to StageContext (stage 45)
- Tool returns InterviewResult as dict with gate_decision field

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Full execution | No execution | All 10 dimensions scored | Call tool, verify all dimensions present | Enables complete gate execution |
| Persistence | No persistence | Result automatically saved to StageContext | Verify artifact saved after tool call | Ensures interview results available |
| Decision accuracy | Unknown | gate_decision matches expected verdict | Test with known scores | Validates gate logic |
| Total latency | No measurement | <60 seconds end-to-end | Measure tool execution time | Meets NFR-E1-001 |

---

### AC-E1-026: query_interview_results MCP Tool

**GIVEN** finding_id="FIND-001" with multiple interview results persisted
**WHEN** I call ai_architect_query_interview_results(finding_id)
**THEN**:
- Tool returns list[dict] with all stage 4.5 artifacts
- List ordered chronologically by created_at
- Each dict has expected InterviewResult structure

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Query execution | No query | List all interview results for finding | Call tool, verify return type | Enables result retrieval |
| Result ordering | Unordered | Results ordered by created_at | Verify timestamp order | Facilitates audit trail analysis |
| Filtering | No filtering | Only stage 4.5 results returned | Test excludes other stages | Prevents unrelated results |

---

## Story 7: SKILL.md v3.0 (AC-E1-027 through AC-E1-029)

### AC-E1-027: Stage 4.5 Section in SKILL.md

**GIVEN** existing SKILL.md documenting stages 0-10
**WHEN** I add a "Stage 4.5 — Plan Interview" section
**THEN** the section includes:
- Stage name and position (between Stage 4 and Stage 5)
- Entry criteria (PRD artifact from Stage 4)
- Exit criteria (InterviewResult with gate decision)
- Artifact schema (JSON example)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Documentation completeness | Missing | All stage metadata present | Verify section content | Provides baseline documentation |
| Artifact schema | No schema | JSON schema or example artifact | Show example InterviewResult | Clarifies data structure |
| Accessibility | Hard to find | Clear section header with cross-references | Check document structure | Enables easy navigation |

---

### AC-E1-028: Dimension Definitions in SKILL.md

**GIVEN** 10 dimensions with scorers
**WHEN** I document each dimension
**THEN** each dimension has:
- Dimension ID (D1-D10)
- Name (e.g., "Sections Present")
- Group (Group 1 or Group 2)
- Description (what it measures)
- Pass threshold (critical vs advisory)
- Scoring algorithm summary

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Coverage | No documentation | All 10 dimensions documented | Count documented dimensions | Enables understanding |
| Detail level | Vague | Clear definitions and scoring algorithms | Read dimension descriptions | Supports debugging |
| Consistency | Ad-hoc | Uniform structure for all dimension entries | Verify format consistency | Improves readability |

---

### AC-E1-029: MCP Tool Signatures in SKILL.md

**GIVEN** three MCP tools
**WHEN** I document each tool
**THEN** each tool has:
- Tool name
- Function signature with type hints
- Description of what it does
- Example usage with sample input/output
- Return type schema

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Signature documentation | Missing | Full FastMCP function signatures | Verify signatures match implementation | Enables MCP integration |
| Examples | No examples | At least one example call per tool | Verify example calls are valid | Demonstrates usage |
| Completeness | Partial | Return types and exceptions documented | Check documentation sections | Clarifies contract |

---

## Story 8: Orchestrator Integration (AC-E1-030 through AC-E1-032)

### AC-E1-030: Orchestrator Stage Insertion

**GIVEN** pipeline orchestrator routing through stages 0-10
**WHEN** I add Stage 4.5 to the routing logic
**THEN**:
- Stage 4 → Stage 4.5 → Stage 5 flow is established
- Stage 4.5 cannot be skipped or disabled
- Findings progress through stage 4.5 before reaching stage 5

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Routing logic | No Stage 4.5 | Orchestrator invokes stage 4.5 | Trace code path | Ensures gate execution |
| Immutability | Skippable | Stage 4.5 is mandatory | Verify no skip logic | Enforces quality gate |
| Error handling | Unknown | Orchestrator handles stage 4.5 errors | Test failure scenarios | Enables graceful error handling |

---

### AC-E1-031: Gate Verdict Routing

**GIVEN** stage 4.5 returns verdicts (APPROVED, PROVISIONAL, REJECTED)
**WHEN** orchestrator receives verdict
**THEN**:
- APPROVED findings → proceed to Stage 5
- PROVISIONAL findings → proceed to Stage 5 (with flags)
- REJECTED findings → re-enter Stage 4 with improvement suggestions

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Verdict handling | No handling | Orchestrator routes based on gate_decision | Test routing with all verdicts | Enables proper flow |
| APPROVED routing | Unknown | Findings proceed to Stage 5 | Trace APPROVED path | Validates happy path |
| REJECTED routing | Not supported | Findings re-enter Stage 4 queue | Trace REJECTED path | Supports iteration |
| Message passing | No messages | Improvement suggestions passed to Stage 4 | Check message content | Guides regeneration |

---

### AC-E1-032: End-to-End Flow

**GIVEN** complete pipeline setup (Stages 4, 4.5, 5)
**WHEN** I run a finding from Stage 4 input through to Stage 5 exit
**THEN**:
- Finding progresses through all stages in order
- Stage 4 output artifact is accessible to Stage 4.5
- Stage 4.5 output (interview result) is accessible to Stage 5
- No artifacts are lost or corrupted in transit

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Flow correctness | No flow | Finding progresses 4 → 4.5 → 5 | Run e2e test | Validates integration |
| Context preservation | Lost context | All artifacts available at each stage | Load all stage artifacts | Enables data propagation |
| Data integrity | Unknown | Artifacts round-trip without corruption | Serialize and deserialize | Ensures reliability |

---

## Story 9: Test Suite (AC-E1-033 through AC-E1-036)

### AC-E1-033: Unit Tests for Dimensions

**GIVEN** 10 dimension scorer implementations
**WHEN** I run unit test suite
**THEN** each dimension has ≥3 test cases covering:
- Happy path (valid input, expected score)
- Edge case 1 (empty/minimal input)
- Edge case 2 (missing required fields)
- Error case (malformed/invalid input)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Coverage | 0% | All 10 dimensions tested | Count test cases | Validates scorer correctness |
| Edge cases | Not covered | Empty artifact, missing sections, malformed input | Verify edge case tests | Ensures robustness |
| Test isolation | Ad-hoc | Each test uses fixtures, no shared state | Inspect test setup | Prevents flaky tests |
| Assertions | Weak | Specific assertions on score, pass, findings fields | Check assertion detail | Validates expected behavior |

---

### AC-E1-034: Gate Logic Tests

**GIVEN** gate decision algorithm
**WHEN** I run gate logic tests
**THEN** tests cover:
- APPROVED verdict (all critical pass, all advisory pass)
- PROVISIONAL verdict (all critical pass, some advisory below)
- REJECTED verdict (any critical below)
- Threshold boundary conditions (0.79, 0.80, 0.81)

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Verdict coverage | Untested | All three verdicts exercised | Run test suite | Validates decision algorithm |
| Boundary testing | Not tested | Tests at threshold boundaries | Verify boundary tests | Ensures correct thresholds |
| Assertion clarity | Weak | Explicit assertions on gate_decision field | Check assertion specificity | Validates verdicts |

---

### AC-E1-035: Integration Tests

**GIVEN** full interview stage with StageContext and MCP tools
**WHEN** I run integration tests
**THEN** tests cover:
- Load PRD artifact from Stage 4
- Execute all 10 dimension scorers
- Persist InterviewResult to Stage 4.5
- Query interview result from Stage 4.5
- Verify Stage 5 can access both Stage 4 and Stage 4.5 artifacts

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| E2E coverage | Not covered | Full 4 → 4.5 → 5 flow tested | Run e2e integration test | Validates production flow |
| Artifact handling | Not tested | Verify round-trip persistence | Test save/load cycle | Ensures data integrity |
| Tool invocation | Not tested | All three MCP tools tested | Verify tool calls succeed | Validates MCP integration |

---

### AC-E1-036: Test Coverage Threshold

**GIVEN** entire _interview/ package with all implementations
**WHEN** I run pytest-cov
**THEN**:
- Code coverage >= 85% (lines covered / total lines in _interview/ package)
- All dimension scorers have >90% coverage
- All gate logic has >90% coverage
- All MCP tools have >80% coverage

| Aspect | Baseline | Target | Measurement | Business Impact |
|--------|----------|--------|-------------|-----------------|
| Overall coverage | 0% | >=85% | Run pytest-cov report | Meets NFR-E1-004 |
| Critical path | Untested | >90% on scorers and gate logic | Inspect coverage hotspots | Ensures critical code tested |
| Coverage report | No report | htmlcov/ with browsable coverage report | Generate coverage report | Enables coverage visualization |

---

**Document**: Acceptance Criteria (Detailed) | **Stage**: 4.5 | **Date**: 2025-03-14 | **Version**: 1.0
