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

1. `ai_architect_load_context(stage_id=4, finding_id="{findingID}")` — load PRD from Stage 4
2. `ai_architect_load_context(stage_id=4, finding_id="{findingID}-interview")` — load interview results (advisory warnings if PROVISIONAL)
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
  content="{prd_requirement_claim_text}",
  claim_type="atomic_fact",
  context="{prd_content}",
  priority=80
)
→ Chain of Verification: systematic verification of each requirement claim
→ Returns per-claim evaluation with score and verdict
```

### 2. Run Zero-LLM Graph Verification (Algorithm 3)

```
ai_architect_verify_graph(
  graph_data={
    "nodes": [
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "FR-001", "node_type": "requirement"},
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "AC-001", "node_type": "test"},
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "STORY-001", "node_type": "specification"}
    ],
    "edges": [
      {"source_id": "{FR_uuid}", "target_id": "{AC_uuid}", "relationship": "tests", "weight": 1.0},
      {"source_id": "{STORY_uuid}", "target_id": "{FR_uuid}", "relationship": "requires", "weight": 1.0}
    ]
  }
)
→ Verify complete acyclic traceability graph
→ Detect orphan IDs, cycles, contradictions
→ Binary pass/fail per structural check
```

### 3. Run NLI Entailment Evaluator (Algorithm 5)

```
ai_architect_evaluate_nli(
  claim_content="{acceptance_criterion_text}",
  premise="{requirement_text}",
  strict=true
)
→ Natural Language Inference: does each AC entail its FR?
→ Returns ClaimEvaluation with score 0.0–1.0 per pair
```

### 4. Run Claim Decomposition

```
ai_architect_decompose_claim(
  content="{complex_prd_claim_text}",
  priority=80
)
→ Break complex claims into atomic verifiable units
→ Each sub-claim gets independent verification via verify_claim
```

### 5. Run Multi-Agent Debate (Algorithm 6)

```
ai_architect_debate_claim(
  content="{prd_controversial_claim_text}",
  num_agents=3,
  max_rounds=3
)
→ Tool-MAD, A-HMAD, FREE-MAD argue against PRD claims
→ Flag overclaiming (claims without NEEDS-RUNTIME markers)
→ A universal PASS across all claims is itself a violation
```

### 6. Run KS Adaptive Stability Consensus (Algorithm 7)

```
ai_architect_consensus(
  scores=[{alg1_score}, {alg3_score}, {alg5_score}, {alg6_score}],
  confidences=[{alg1_confidence}, {alg3_confidence}, {alg5_confidence}, {alg6_confidence}],
  algorithm="adaptive_stability"
)
→ KS Adaptive Stability: Beta-Binomial early stopping when evaluators converge
→ Saves 30-50% cost on clear pass/fail cases
→ Returns ConsensusResult with final score 0.0–1.0
```

### 7. Confidence fusion across all algorithms

```
ai_architect_fuse_confidence(
  estimates=[
    {"source": "thought_buffer", "value": {alg1_score}, "uncertainty": 0.1, "reasoning": "Chain of Verification score"},
    {"source": "adaptive_expansion", "value": {alg3_score}, "uncertainty": 0.05, "reasoning": "Graph Verification score"},
    {"source": "collaborative_inference", "value": {alg5_score}, "uncertainty": 0.1, "reasoning": "NLI Entailment score"},
    {"source": "metacognitive", "value": {alg6_score}, "uncertainty": 0.15, "reasoning": "Multi-Agent Debate score"},
    {"source": "trm_refinement", "value": {alg7_score}, "uncertainty": 0.1, "reasoning": "KS Consensus score"}
  ]
)
→ Weighted fusion of all algorithm confidence estimates
→ Returns FusedConfidence with point estimate, lower/upper bounds
```

### 8. Decision: pass or loop

**If compound score ≥ threshold:**
```
ai_architect_save_context(
  stage_id=5,
  finding_id="{findingID}",
  artifact={
    "algorithm_scores": {
      "chain_of_verification": {score},
      "graph_verification": {score},
      "nli_entailment": {score},
      "claim_decomposition": {score},
      "multi_agent_debate": {score},
      "ks_consensus": {score},
      "confidence_fusion": {score}
    },
    "compound_score": {final_score},
    "overclaiming": [...],
    "failed_rules": [],
    "decision": "pass",
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-5-verification-report.json",
  content={verification report JSON}
)

ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 6,
  "status": "running",
  "completed_stages": [0, 1, 2, 3, 4, 5]
})
```

**If compound score < threshold:**
```
→ Inject failure context (failed rules, overclaiming flags, low-scoring algorithms)
→ Loop back to Stage 4 step 5 (skip clarification, reuse ClarificationReport)
→ Max 3 retries of the Stage 5→4 loop

ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 4,
  "status": "running",
  "completed_stages": [0, 1, 2, 3],
  "metadata": {"retry_count": "{current + 1}", "retry_reason": "review_score_below_threshold"}
})
```

### 9. Audit event

```
ai_architect_append_audit_event(event_data={
  "event_id": "stage-5-review-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 5,
  "tool_name": "stage-5-review",
  "outcome": "pass",
  "message": "Stage 5 review completed for finding {findingID}: {decision}",
  "metadata": {"compound_score": "{score}", "retry_count": "{N}"}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage_id=5, phase="observe", decision="All 7 algorithms executed: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=5, phase="observe", decision="Consensus score computed: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=5, phase="observe", decision="Compound score >= threshold: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=5, phase="observe", decision="No overclaiming without NEEDS-RUNTIME: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=5, phase="observe", decision="Loop count under 3: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=5, phase="decide", decision="Stage 4 output untouched: {true/false}", confidence=1.0, session_id="{sessionID}")
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
| `stage-5-verification-report.json` | `{data_dir}/artifacts/` | `{algorithmScores, compoundScore, overclaiming, failedRules, decision}` |
| StageContext[stage-5] | `ai_architect_save_context` | Same as verification report |
| AuditEvent | `ai_architect_append_audit_event` | `{type, stage, outcome, compoundScore, retryCount}` |

## Stop criteria

- **Pass:** All 7 algorithms executed. Compound score ≥ threshold. No overclaiming. Proceed to Stage 6. PipelineState.currentStage = 6.
- **Retry:** Compound score < threshold — loop to Stage 4 step 5 with failure context. Max 3 retries of the 5→4 loop.
- **Escalate:** 3 retries exhausted. Compound score still below threshold. Persistent overclaiming. Algorithm execution errors.

## Effort level: HIGH
