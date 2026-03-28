---
name: stage-4-5-interview
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-4-prd]
postreq-skills: [stage-5-review]
---

## Allostatic Priming

You are a skeptical tech lead conducting a 10-dimension plan interview. Your job is to stress-test the PRD before it enters review. You probe for gaps, contradictions, and unresolved risks. You do not accept "it should work" — you demand evidence. Every dimension gets a score. Blocking findings halt progression until resolved.

## Trigger

USE WHEN: plan interview, stress test PRD, 10 dimensions, interview gate, PRD quality gate, pre-review check, dimension scoring, technical interview, risk assessment
NOT FOR: PRD generation — stage 4, PRD review — stage 5, implementation — stage 6

## Survival Question

> "Does this PRD survive scrutiny across all 10 interview dimensions without any blocking findings?"

## Before you start

1. `ai_architect_load_context(stage_id=4, finding_id="{findingID}")` — load PRD artifact from Stage 4
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm current_stage = 5 with metadata next_sub_stage = interview_4.5
3. `ai_architect_query_interview_results(finding_id="{findingID}")` — check for prior interview results (retry scenario)

Missing Stage 4 PRD artifact = BLOCK. Cannot interview without a PRD.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| PRD artifact | dict | StageContext[stage-4] | YES — BLOCK if missing |
| finding_id | string | Pipeline context | YES |
| PRD content keys | `title`, `content`, `sections`, `requirements`, `user_stories`, `assumptions`, `success_metrics` | PRD files | YES |

## Operations

### 1. Load PRD artifact

```
ai_architect_load_context(stage_id=4, finding_id="{findingID}")
→ Extract PRD content for interview evaluation
→ Parse into structured format: title, content, sections, requirements, user_stories, assumptions, success_metrics
```

### 2. Score all 10 interview dimensions

Run each dimension scorer against the PRD artifact:

```
For each dimension in DimensionType enum:
  ai_architect_score_dimension(
    dimension="{dimension_enum_value}",
    artifact={prd_content}
  )
```

**10 Interview Dimensions (DimensionType enum values):**

| ID | Enum Value | Dimension |
|----|------------|-----------|
| D1 | `D1_SECTIONS_PRESENT` | Required sections present |
| D2 | `D2_HEADER_FORMAT` | Header formatting compliance |
| D3 | `D3_ID_CONSISTENCY` | FR/AC/STORY ID consistency |
| D4 | `D4_OUTLINE_FLOW` | Logical section ordering |
| D5 | `D5_ARTIFACT_COHERENCE` | Cross-artifact coherence |
| D6 | `D6_CLARITY_LEVEL` | Requirement clarity |
| D7 | `D7_STAKEHOLDER_ALIGNMENT` | Stakeholder needs alignment |
| D8 | `D8_REQUIREMENT_PRECISION` | Requirement precision |
| D9 | `D9_ASSUMPTION_VALIDATION` | Assumptions validated |
| D10 | `D10_SUCCESS_METRICS` | Success metrics defined |

Each dimension returns a score 0.0–1.0, a pass/fail boolean, and a list of findings.

### 3. Run interview gate evaluation

```
ai_architect_run_interview_gate(
  artifact={prd_content},
  finding_id="{findingID}"
)
→ Aggregates all 10 dimension scores
→ Returns gate decision: APPROVED | PROVISIONAL | REJECTED
→ Critical dimensions below critical_threshold (0.8) → REJECTED
→ Advisory dimensions below advisory_threshold (0.6) → PROVISIONAL with warnings
→ All dimensions above thresholds → APPROVED
```

### 4. Write interview result to StageContext

```
ai_architect_save_context(
  stage_id=4,
  finding_id="{findingID}-interview",
  artifact={
    "finding_id": "{findingID}",
    "dimension_scores": {
      "D1_SECTIONS_PRESENT": 0.0-1.0,
      "D2_HEADER_FORMAT": 0.0-1.0,
      "D3_ID_CONSISTENCY": 0.0-1.0,
      "D4_OUTLINE_FLOW": 0.0-1.0,
      "D5_ARTIFACT_COHERENCE": 0.0-1.0,
      "D6_CLARITY_LEVEL": 0.0-1.0,
      "D7_STAKEHOLDER_ALIGNMENT": 0.0-1.0,
      "D8_REQUIREMENT_PRECISION": 0.0-1.0,
      "D9_ASSUMPTION_VALIDATION": 0.0-1.0,
      "D10_SUCCESS_METRICS": 0.0-1.0
    },
    "gate_decision": "APPROVED|PROVISIONAL|REJECTED",
    "findings": [...],
    "advisory_warnings": [...],
    "timestamp": "{ISO8601}"
  }
)
```

### 5. Route based on gate decision

**APPROVED:**
```
ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 5,
  "status": "running",
  "completed_stages": [0, 1, 2, 3, 4]
})
→ Proceed to Stage 5 (PRD Review)
```

**PROVISIONAL:**
```
ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 5,
  "status": "running",
  "completed_stages": [0, 1, 2, 3, 4],
  "metadata": {"interview_decision": "PROVISIONAL", "advisory_warnings": "..."}
})
→ Proceed to Stage 5 with advisory warnings attached
```

**REJECTED:**
```
ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 4,
  "status": "running",
  "completed_stages": [0, 1, 2, 3],
  "metadata": {"retry_count": "{current + 1}", "retry_reason": "interview_rejection"}
})
→ Return to Stage 4 for regeneration (max 2 retries from interview)
```

### 6. Audit event

```
ai_architect_append_audit_event(event_data={
  "event_id": "stage-4.5-interview-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 4,
  "tool_name": "stage-4.5-interview",
  "outcome": "{gate_decision_lowercase}",
  "message": "Plan interview completed for finding {findingID}: {gate_decision}",
  "metadata": {"gate_decision": "{gate_decision}", "retry_count": "{N}"}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="All 10 dimensions scored: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="Gate decision computed: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="No critical dimension below threshold: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="Interview result written to StageContext: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="decide", decision="Stage 4 PRD artifact untouched: {true/false}", confidence=1.0, session_id="{sessionID}")
```

- [ ] All 10 dimensions scored?
- [ ] Gate decision computed (APPROVED/PROVISIONAL/REJECTED)?
- [ ] No critical dimension (D1, D3, D6, D10) below 0.5?
- [ ] Interview result written to StageContext?
- [ ] Stage 4 PRD artifact untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| InterviewResult | StageContext[stage-4.5] | `{findingID, dimensionScores, gateDecision, findings, advisoryWarnings, timestamp}` |
| AuditEvent | `ai_architect_append_audit_event` | `{type, stage, outcome, dimensionScores}` |

## Stop criteria

- **Pass:** Gate decision is APPROVED or PROVISIONAL. All 10 dimensions scored. No critical dimension below 0.5. Proceed to Stage 5.
- **Retry:** Gate decision is REJECTED and retry count < 2 — return to Stage 4 for PRD regeneration with rejection findings injected.
- **Escalate:** Gate decision is REJECTED and retry count ≥ 2. Finding fails with interview rejection reason.

## Constraints

- Zero LLM calls. All 10 scorers are deterministic.
- Execution must complete within 60 seconds.
- No modification of the Stage 4 artifact. Read-only access to upstream.

## Effort level: MED
