---
name: stage-7-verification
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-6-implementation]
postreq-skills: [stage-8-benchmark]
---

## Allostatic Priming

You are a deterministic validator. No judgment. No interpretation. Rules run. Vision diffs. Build compiles or it does not. You do not fix — you report. Every check is binary: pass or fail. You run 64 HOR rules, structural checks, and build gates. No LLM calls. No fuzzy matching. No "close enough."

## Trigger

USE WHEN: verify code, run gates, check implementation, HOR rules, visual regression, 64 rules, deterministic, no LLM, structural check, build gate, binary validation, compliance check
NOT FOR: code implementation — stage 6, benchmark — stage 8, any LLM reasoning

## Survival Question

> "Do all 64 HOR rules pass, does the build succeed, and are there no visual regressions?"

## Before you start

1. `ai_architect_load_context(stage="stage-6", finding_id="{findingID}")` — load implementation manifest from Stage 6
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 7, check retryCount

Missing Stage 6 implementation manifest = BLOCK. Cannot verify without implementation.

**CRITICAL:** This stage is fully deterministic. No LLM calls. No `ai_architect_enhance_prompt`. No `ai_architect_select_strategy`. No `ai_architect_expand_thought`. Only deterministic tools from the allowlist below.

## Allowed tools (closed allowlist)

Only these tools may be called in Stage 7:
- `ai_architect_run_hor_rules`
- `ai_architect_run_hor_category`
- `ai_architect_run_hor_single`
- `ai_architect_run_build`
- `ai_architect_run_tests`
- `ai_architect_compound_score`
- `ai_architect_verify_graph`
- `ai_architect_load_context`
- `ai_architect_save_context`
- `ai_architect_save_session_state`
- `ai_architect_append_audit_event`
- `ai_architect_emit_ooda_checkpoint`
- `ai_architect_fs_read`
- `ai_architect_fs_write`
- `ai_architect_fs_list`
- `ai_architect_git_diff`

Any tool not on this list = BLOCK. Enforced by `hooks/pre-tool-use/stage-7-gate.sh`.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-6-implementation-manifest.json` | JSON | StageContext[stage-6] | YES — BLOCK if missing |
| Implementation branch | git ref | `pipeline/{findingID}` | YES — code must exist |
| PRD files | MD | StageContext[stage-4] | YES — for HOR rule evaluation |

## Operations

### 1. Run 64 HOR rules on implementation

```
ai_architect_run_hor_rules(
  document={implementation_content + prd_content},
  categories=["all"]
)
→ All 64 pure functions evaluate implementation against PRD
→ Returns per-rule: {rule_id, category, pass/fail, violation_details}
→ Compound score computed from results

Categories (10):
  - Core PRD structural (23 rules, 48 critical: −0.15 per violation)
  - Architecture & Code Quality (7 rules)
  - Security (8 rules)
  - Data Protection & Compliance (6 rules)
  - Error Handling & Resilience (5 rules)
  - Concurrency & State Management (3 rules)
  - Senior Code Quality Standards (6 rules)
  - Comprehensive Testing (6 rules)
  - Observability & Monitoring (4 rules)
  - Dependency & Supply Chain (2 rules)
```

Can also run by category for targeted verification:
```
ai_architect_run_hor_category(
  document={content},
  category="security"
)
```

### 2. Build gate (blocking)

```
ai_architect_run_build(
  project_path="{project_root}",
  scheme="{scheme_name}"
)
→ Build succeeds = PASS
→ Build fails = BLOCK — immediate loop to Stage 6 with build errors injected
→ This is a blocking gate — no downstream stages execute on build failure
```

### 3. Structural graph verification

```
ai_architect_verify_graph(
  claims=["{implementation_imports}"],
  graph_type="dependency"
)
→ Verify no circular dependencies in implementation
→ Verify implementation matches PRD file change manifest
```

### 4. Git diff verification

```
ai_architect_git_diff(ref="main...pipeline/{findingID}")
→ Verify diff matches implementation manifest
→ No files changed outside manifest scope
→ No untracked files that should be committed
```

### 5. Compute compound verification score

```
ai_architect_compound_score(
  scores={
    "hor_rules_pass_rate": {pass_count / 64},
    "build_result": {1.0 if pass else 0.0},
    "graph_verification": {1.0 if no cycles else 0.0},
    "manifest_match": {1.0 if diff matches manifest else 0.0}
  },
  weights={
    "hor_rules_pass_rate": 0.4,
    "build_result": 0.3,
    "graph_verification": 0.15,
    "manifest_match": 0.15
  }
)
```

### 6. Decision: pass or loop to Stage 6

**All gates pass:**
```
ai_architect_save_context(
  stage="stage-7",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "horResults": {per_rule_results},
    "horPassRate": {pass_count / 64},
    "buildResult": "pass",
    "graphVerification": "pass",
    "compoundScore": {score},
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-7-hor-report.json",
  content={HOR report JSON}
)

ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 8,
  "retryCount": 0
})
```

**Any blocking gate fails:**
```
→ Inject failure context (failed HOR rules, build errors, graph violations)
→ Loop back to Stage 6 for fixes
→ Max 3 retries of the 7→6 loop

ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 6,
  "retryCount": {current + 1},
  "retryReason": "verification_failure",
  "failedGates": [...]
})
```

### 7. Audit event

```
ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 7,
  "outcome": "pass|loop_to_6",
  "findingID": "{findingID}",
  "compoundScore": {score},
  "horPassRate": {rate},
  "buildResult": "pass|fail",
  "retryCount": N
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-7", checks={
  "all_64_hor_rules_evaluated": true/false,
  "build_succeeds": true/false,
  "no_circular_dependencies": true/false,
  "diff_matches_manifest": true/false,
  "loop_count_under_3": true/false,
  "no_llm_calls_made": true/false,
  "stage_6_output_untouched": true/false
})
```

- [ ] All 64 HOR rules evaluated?
- [ ] Build succeeds (blocking gate)?
- [ ] No circular dependencies in implementation?
- [ ] Git diff matches implementation manifest?
- [ ] Loop count < 3 (Stage 7→6 retries)?
- [ ] No LLM calls made (deterministic stage)?
- [ ] Stage 6 implementation untouched (read-only — fixes go through new Stage 6 pass)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-7-hor-report.json` | `{data_dir}/artifacts/` | `{findingID, horResults, horPassRate, buildResult, graphVerification, compoundScore}` |
| StageContext[stage-7] | `ai_architect_save_context` | Same as HOR report |
| AuditEvent | `ai_architect_append_audit_event` | `{type, stage, outcome, compoundScore, retryCount}` |

## Stop criteria

- **Pass:** All 64 HOR rules pass. Build succeeds. No circular deps. Diff matches manifest. PipelineState.currentStage = 8.
- **Retry:** Any blocking gate fails — loop to Stage 6 with failure context. Max 3 retries of the 7→6 loop.
- **Escalate:** 3 retries exhausted. Build failures persist. HOR violations unfixable without PRD change.

## Effort level: LOW
