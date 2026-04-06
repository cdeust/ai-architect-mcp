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

1. `ai_architect_load_context(stage_id=6, finding_id="{findingID}")` — load implementation manifest from Stage 6
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
  artifact={implementation_content + prd_content as dict},
  base_score=1.0
)
→ All 64 pure functions evaluate implementation against PRD
→ Returns per-rule results, passed/failed counts, and adjusted score

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
  category="security",
  artifact={content as dict}
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
  graph_data={
    "nodes": [
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "{module_name}", "node_type": "implementation"}
    ],
    "edges": [
      {"source_id": "{importer_uuid}", "target_id": "{imported_uuid}", "relationship": "depends", "weight": 1.0}
    ]
  }
)
→ Verify no cycles (circular dependencies) in implementation
→ Verify no contradictions or orphans in dependency graph
```

### 4. Git diff verification

```
ai_architect_git_diff(base="main", head="pipeline/{findingID}")
→ Verify diff matches implementation manifest
→ No files changed outside manifest scope
→ No untracked files that should be committed
```

### 5. Compute compound verification score

```
ai_architect_compound_score(
  relevance={pass_count / 64},
  uniqueness={1.0 if build_pass else 0.0},
  impact={1.0 if no_cycles else 0.0},
  confidence={1.0 if diff_matches_manifest else 0.0},
  weights={
    "relevance": 0.4,
    "uniqueness": 0.3,
    "impact": 0.15,
    "confidence": 0.15
  }
)
```

### 6. Decision: pass or loop to Stage 6

**All gates pass:**
```
ai_architect_save_context(
  stage_id=7,
  finding_id="{findingID}",
  artifact={
    "finding_id": "{findingID}",
    "hor_results": {per_rule_results},
    "hor_pass_rate": {pass_count / 64},
    "build_result": "pass",
    "graph_verification": "pass",
    "compound_score": {score},
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-7-hor-report.json",
  content={HOR report JSON}
)

ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 8,
  "status": "running",
  "completed_stages": [0, 1, 2, 3, 4, 5, 6, 7]
})
```

**Any blocking gate fails:**
```
→ Inject failure context (failed HOR rules, build errors, graph violations)
→ Loop back to Stage 6 for fixes
→ Max 3 retries of the 7→6 loop

ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 6,
  "status": "running",
  "completed_stages": [0, 1, 2, 3, 4, 5],
  "metadata": {"retry_count": "{current + 1}", "retry_reason": "verification_failure"}
})
```

### 7. Audit event

```
ai_architect_append_audit_event(event_data={
  "event_id": "stage-7-verification-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 7,
  "tool_name": "stage-7-verification",
  "outcome": "pass",
  "message": "Stage 7 verification completed for finding {findingID}: {decision}",
  "metadata": {"compound_score": "{score}", "hor_pass_rate": "{rate}", "build_result": "{pass|fail}"}
})
```

## Cortex memory integration

### After verification — store failure patterns for proactive detection

**WHEN:** After the verification decision (step 6) is made, regardless of pass or fail.
**WHY:** Verification failures reveal systemic weaknesses in the pipeline's code generation. If Stage 7 repeatedly fails on the same HOR rules, the same build errors, or the same graph violations, future runs should check for these patterns proactively in Stage 6 before reaching verification. Storing pass patterns is also valuable — it confirms which approaches produce clean implementations.
**HOW:**

On failure (any blocking gate fails):
```
cortex:remember(
  content="Verification FAILURE for finding {findingID} in repo {target_repo}: failed_hor_rules={list_of_failed_rule_ids}, build_errors={build_error_summary}, graph_violations={cycle_or_orphan_details}, compound_score={score}, retry_number={current_retry}",
  tags=["verification-failure", "repo:{target_repo_name}", "finding:{findingID}", "stage:7"]
)
```

On pass (all gates pass):
```
cortex:remember(
  content="Verification PASS for finding {findingID} in repo {target_repo}: hor_pass_rate={pass_count}/64, compound_score={score}, total_7_to_6_retries={retry_count}, close_calls={rules_that_barely_passed}",
  tags=["verification-pass", "repo:{target_repo_name}", "finding:{findingID}", "stage:7"]
)
```

What to store on failure:
- Exact HOR rule IDs that failed — enables pattern detection across runs (e.g., "security rules fail 40% of the time")
- Build error categories (missing imports, type mismatches, unresolved references) — enables Stage 6 to add pre-checks
- Graph violations (which modules formed cycles, which IDs were orphaned)
- The retry number — first failure vs third failure tells different stories

What to store on pass:
- Rules that barely passed (score close to threshold) — these are fragile and may fail on the next run
- Total retries needed — zero retries means the implementation approach was sound; three retries means it was marginal

**NOTE:** This stage is deterministic. The `cortex:remember` call happens AFTER all deterministic checks complete. It does not influence the pass/fail decision. It is a post-decision recording step only.

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage_id=7, phase="observe", decision="All 64 HOR rules evaluated: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=7, phase="observe", decision="Build succeeds: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=7, phase="observe", decision="No circular dependencies: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=7, phase="observe", decision="Diff matches manifest: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=7, phase="observe", decision="Loop count under 3: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=7, phase="observe", decision="No LLM calls made: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=7, phase="decide", decision="Stage 6 output untouched: {true/false}", confidence=1.0, session_id="{sessionID}")
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
