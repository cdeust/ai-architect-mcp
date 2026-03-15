---
name: stage-5-review
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-4-5-interview]
postreq-skills: [stage-6-implementation]
---

## Allostatic Priming

You are a hostile reviewer. Your job is to find what fails, not to validate what passes. Run the full verification suite and loop back to generation if anything is below threshold. You assume the PRD is wrong until the algorithms prove otherwise. You run 7 verification algorithms — not opinions.

## Trigger

USE WHEN: PRD review, verify PRD, run verification, check PRD quality, review specification, 7 algorithms, compound score, evaluator, quality gate, review loop
NOT FOR: generate PRD — stage 4, implement — stage 6, health check — stage 0

## Survival Question

> "Have all 7 verification algorithms run and returned scores above threshold — with no claim marked as overclaiming?"

## Before you start

1. `ai_architect_load_context(stage="stage-4", finding_id="{findingID}")` — load PRD from Stage 4
2. `ai_architect_load_context(stage="stage-4.5", finding_id="{findingID}")` — load interview results (advisory warnings if PROVISIONAL)
3. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 5, check retryCount

Missing Stage 4 PRD = BLOCK. Missing Stage 4.5 interview result = BLOCK.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| 9 PRD files | MD/JSON | StageContext[stage-4] | YES — BLOCK if missing |
| Interview result | JSON | StageContext[stage-4.5] | YES — BLOCK if missing |
| Advisory warnings | list | Interview result | NO — only if PROVISIONAL |
| retryCount | int | PipelineState | YES |

## Operations

### 1. Run Standard Chain-of-Verification (Algorithm 1)

```
ai_architect_verify_claim(
  claim="{prd_requirement_claims}",
  evidence="{prd_content}",
  method="chain_of_verification"
)
→ Systematic verification of each requirement claim against evidence
→ Returns per-claim verdicts: PASS, SPEC-COMPLETE, NEEDS-RUNTIME, INCONCLUSIVE, FAIL
```

### 2. Run Zero-LLM Graph Verification (Algorithm 3)

```
ai_architect_verify_graph(
  claims=["{all_FR_IDs}", "{all_AC_IDs}", "{all_UT_IDs}", "{all_STORY_IDs}"],
  graph_type="traceability"
)
→ Verify complete acyclic traceability graph
→ Detect orphan IDs, circular references, missing links
→ Binary pass/fail
```

### 3. Run NLI Entailment Evaluator (Algorithm 5)

```
ai_architect_evaluate_nli(
  premise="{requirements_text}",
  hypothesis="{acceptance_criteria_text}",
  threshold=0.85
)
→ Natural Language Inference: do acceptance criteria entail requirements?
→ Score 0.0–1.0 per pair
```

### 4. Run Claim Decomposition

```
ai_architect_decompose_claim(
  claim="{complex_prd_claims}",
  depth=2
)
→ Break complex claims into atomic verifiable units
→ Each sub-claim gets independent verification
```

### 5. Run Multi-Agent Debate (Algorithm 6)

```
ai_architect_debate_claim(
  claim="{prd_controversial_claims}",
  agents=["advocate", "critic", "judge"],
  rounds=3
)
→ Tool-MAD, A-HMAD, FREE-MAD argue against PRD claims
→ Flag overclaiming (claims without NEEDS-RUNTIME markers)
→ A universal PASS across all claims is itself a violation
```

### 6. Run KS Adaptive Stability Consensus (Algorithm 7)

```
ai_architect_consensus(
  scores=[
    {alg1_score},
    {alg3_score},
    {alg5_score},
    {alg6_score}
  ],
  method="ks_adaptive",
  early_stopping=true
)
→ Beta-Binomial early stopping when evaluators converge
→ Saves 30-50% cost on clear pass/fail cases
→ Returns consensus score 0.0–1.0
```

### 7. Confidence fusion across all algorithms

```
ai_architect_fuse_confidence(
  sources=[
    {"algorithm": "chain_of_verification", "score": {alg1}},
    {"algorithm": "graph_verification", "score": {alg3}},
    {"algorithm": "nli_entailment", "score": {alg5}},
    {"algorithm": "multi_agent_debate", "score": {alg6}},
    {"algorithm": "ks_consensus", "score": {alg7}}
  ]
)
→ Weighted fusion of all algorithm scores
→ Final compound review score 0.0–1.0
```

### 8. Decision: pass or loop

**If compound score ≥ threshold:**
```
ai_architect_save_context(
  stage="stage-5",
  finding_id="{findingID}",
  data={
    "algorithmScores": {
      "chain_of_verification": {score},
      "graph_verification": {score},
      "nli_entailment": {score},
      "claim_decomposition": {score},
      "multi_agent_debate": {score},
      "ks_consensus": {score},
      "confidence_fusion": {score}
    },
    "compoundScore": {final_score},
    "overclaiming": [...],
    "failedRules": [],
    "decision": "pass",
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path=".ai-architect/artifacts/stage-5-verification-report.json",
  content={verification report JSON}
)

ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 6,
  "retryCount": 0
})
```

**If compound score < threshold:**
```
→ Inject failure context (failed rules, overclaiming flags, low-scoring algorithms)
→ Loop back to Stage 4 step 5 (skip clarification, reuse ClarificationReport)
→ Max 3 retries of the Stage 5→4 loop

ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 4,
  "retryCount": {current + 1},
  "retryReason": "review_score_below_threshold",
  "failedAlgorithms": [...]
})
```

### 9. Audit event

```
ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 5,
  "outcome": "pass|loop_to_4",
  "findingID": "{findingID}",
  "compoundScore": {score},
  "retryCount": N
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-5", checks={
  "all_7_algorithms_executed": true/false,
  "consensus_score_computed": true/false,
  "compound_score_gte_threshold": true/false,
  "no_overclaiming_without_needs_runtime": true/false,
  "loop_count_under_3": true/false,
  "stage_4_output_untouched": true/false
})
```

- [ ] All verification algorithms executed?
- [ ] Consensus score computed by KS Adaptive Stability?
- [ ] Compound score ≥ threshold?
- [ ] No overclaiming without NEEDS-RUNTIME marker?
- [ ] Loop count < 3 (Stage 5→4 retries)?
- [ ] Stage 4 PRD files untouched (read-only during review)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-5-verification-report.json` | `.ai-architect/artifacts/` | `{algorithmScores, compoundScore, overclaiming, failedRules, decision}` |
| StageContext[stage-5] | `ai_architect_save_context` | Same as verification report |
| AuditEvent | `ai_architect_append_audit_event` | `{type, stage, outcome, compoundScore, retryCount}` |

## Stop criteria

- **Pass:** All 7 algorithms executed. Compound score ≥ threshold. No overclaiming. Proceed to Stage 6. PipelineState.currentStage = 6.
- **Retry:** Compound score < threshold — loop to Stage 4 step 5 with failure context. Max 3 retries of the 5→4 loop.
- **Escalate:** 3 retries exhausted. Compound score still below threshold. Persistent overclaiming. Algorithm execution errors.

## Effort level: HIGH
