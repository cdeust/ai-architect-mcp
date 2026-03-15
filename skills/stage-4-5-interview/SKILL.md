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

1. `ai_architect_load_context(stage="stage-4", finding_id="{findingID}")` — load PRD artifact from Stage 4
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 4.5
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
ai_architect_load_context(stage="stage-4", finding_id="{findingID}")
→ Extract PRD content for interview evaluation
→ Parse into structured format: title, content, sections, requirements, user_stories, assumptions, success_metrics
```

### 2. Score all 10 interview dimensions

Run each dimension scorer against the PRD artifact:

```
For each dimension D1–D10:
  ai_architect_score_dimension(
    finding_id="{findingID}",
    dimension="D{N}",
    prd_artifact={prd_content}
  )
```

**10 Interview Dimensions:**

| ID | Dimension | Probing Question |
|----|-----------|-----------------|
| D1 | Technical Implementation | "What happens when X fails?" |
| D2 | UI/UX | "How does the user recover from this state?" |
| D3 | Risks | "What's the worst-case scenario here?" |
| D4 | Tradeoffs | "You chose X over Y. What did you give up?" |
| D5 | Edge Cases | "What if this input is empty? Duplicated? Huge?" |
| D6 | Dependencies | "What breaks if this service is down?" |
| D7 | Testing | "How do you verify this actually works?" |
| D8 | Deployment | "Can you roll this back in 5 minutes?" |
| D9 | Gaps | "What's missing from this plan?" |
| D10 | Security | "Where can this be exploited?" |

Each dimension returns a score 0.0–1.0 and a list of findings (if any).

### 3. Run interview gate evaluation

```
ai_architect_run_interview_gate(
  finding_id="{findingID}",
  prd_artifact={prd_content}
)
→ Aggregates all 10 dimension scores
→ Returns gate decision: APPROVED | PROVISIONAL | REJECTED
→ Critical dimensions (D1, D3, D6, D10) below 0.5 → REJECTED
→ Advisory dimensions below 0.6 → PROVISIONAL with warnings
→ All dimensions ≥ 0.6 → APPROVED
```

### 4. Write interview result to StageContext

```
ai_architect_save_context(
  stage="stage-4.5",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "dimensionScores": {
      "D1_technical": 0.0-1.0,
      "D2_ux": 0.0-1.0,
      "D3_risks": 0.0-1.0,
      "D4_tradeoffs": 0.0-1.0,
      "D5_edge_cases": 0.0-1.0,
      "D6_dependencies": 0.0-1.0,
      "D7_testing": 0.0-1.0,
      "D8_deployment": 0.0-1.0,
      "D9_gaps": 0.0-1.0,
      "D10_security": 0.0-1.0
    },
    "gateDecision": "APPROVED|PROVISIONAL|REJECTED",
    "findings": [...],
    "advisoryWarnings": [...],
    "timestamp": "{ISO8601}"
  }
)
```

### 5. Route based on gate decision

**APPROVED:**
```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 5,
  "retryCount": 0
})
→ Proceed to Stage 5 (PRD Review)
```

**PROVISIONAL:**
```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 5,
  "retryCount": 0,
  "advisoryWarnings": [...]
})
→ Proceed to Stage 5 with advisory warnings attached
```

**REJECTED:**
```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 4,
  "retryCount": {current + 1},
  "retryReason": "interview_rejection",
  "rejectionFindings": [...]
})
→ Return to Stage 4 for regeneration (max 2 retries from interview)
```

### 6. Audit event

```
ai_architect_append_audit_event(event={
  "type": "interview_complete",
  "stage": 4.5,
  "outcome": "{gate_decision}",
  "findingID": "{findingID}",
  "dimensionScores": {...},
  "retryCount": N
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-4.5", checks={
  "all_10_dimensions_scored": true/false,
  "gate_decision_computed": true/false,
  "no_critical_dimension_below_0.5": true/false,
  "interview_result_written": true/false,
  "stage_4_output_untouched": true/false
})
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
