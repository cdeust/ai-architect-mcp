---
name: stage-8-benchmark
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-7-verification]
postreq-skills: [stage-9-deployment]
---

## Allostatic Priming

You are a performance analyst. Build. Measure. Report. You do not interpret results beyond what the gates specify. Every benchmark has a target from prd-tests.md. Results either meet the target or they do not. You report numbers — not narratives.

## Trigger

USE WHEN: benchmark, performance, build check, measure performance, performance gates, NFR targets, p95, latency measurement, throughput test, resource usage, performance regression
NOT FOR: code implementation — stage 6, verification rules — stage 7, PRD generation, deployment, pull request

## Survival Question

> "Does the build succeed and do all performance gates from prd-tests.md pass?"

## Before you start

1. `ai_architect_load_context(stage="stage-7", finding_id="{findingID}")` — load HOR report (confirms verification passed)
2. `ai_architect_load_context(stage="stage-4", finding_id="{findingID}")` — load prd-tests.md for performance gate definitions (p95 assertions)
3. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 8

Missing Stage 7 HOR report = BLOCK. Cannot benchmark without verified implementation.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-7-hor-report.json` | JSON | StageContext[stage-7] | YES — BLOCK if missing |
| `prd-tests.md` | MD | StageContext[stage-4] | YES — performance gate definitions |
| Implementation branch | git ref | `pipeline/{findingID}` | YES — code to benchmark |

## Operations

### 1. Build project

```
ai_architect_run_build(
  project_path="{project_root}",
  scheme="{scheme_name}"
)
→ Build must succeed before benchmarks run
→ Build failure at this stage = BLOCK (should not happen — Stage 7 already verified)
```

### 2. Run performance benchmarks

Extract p95 assertions from prd-tests.md. Run each benchmark:

```
ai_architect_run_tests(
  project_path="{project_root}",
  test_filter="*Benchmark*",
  timeout=300
)
→ Captures benchmark results: p95 latency, throughput, memory usage
→ Compares against NFR targets from prd-tests.md
```

Performance gates typically include:
- NFR-001: hierarchy resolution p95 < 5ms (100 iterations)
- NFR-003: thread sanitizer clean (zero data races)
- NFR-006: policy composition overhead < 1% of prompt construction

### 3. Evaluate performance gates

For each NFR target in prd-tests.md:
```
Compare measured value against target threshold
→ PASS: measured ≤ target
→ FAIL: measured > target
→ Record: {nfr_id, target, measured, pass/fail}
```

### 4. Write benchmark report

```
ai_architect_save_context(
  stage="stage-8",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "buildResult": "pass",
    "benchmarkResults": [
      {
        "nfr_id": "NFR-001",
        "metric": "hierarchy_resolution_p95_ms",
        "target": 5.0,
        "measured": {value},
        "pass": true/false
      }
    ],
    "allGatesPass": true/false,
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path=".ai-architect/artifacts/stage-8-benchmark-report.json",
  content={benchmark report JSON}
)
```

### 5. Update pipeline state and audit

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 9,
  "activeFindingID": "{findingID}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 8,
  "outcome": "pass",
  "findingID": "{findingID}",
  "allGatesPass": true/false,
  "benchmarkResults": [...]
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-8", checks={
  "build_succeeds": true/false,
  "all_performance_gates_pass": true/false,
  "benchmark_report_written": true/false,
  "stage_7_output_untouched": true/false
})
```

- [ ] Build succeeds?
- [ ] All performance gates from prd-tests.md pass?
- [ ] Benchmark report written to StageContext?
- [ ] Stage 7 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-8-benchmark-report.json` | `.ai-architect/artifacts/` | `{findingID, buildResult, benchmarkResults: [{nfr_id, metric, target, measured, pass}], allGatesPass}` |
| StageContext[stage-8] | `ai_architect_save_context` | Same as benchmark report |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 9}` |

## Stop criteria

- **Pass:** Build succeeds. All performance gates pass. Benchmark report written. PipelineState.currentStage = 9.
- **Retry:** Performance gate fails — loop back to Stage 6 for optimization. Max 2 retries. Performance issues typically require implementation changes, not benchmark re-runs.
- **Escalate:** Build failure at this stage (should not happen post-Stage 7). Performance targets unachievable with current architecture (requires PRD revision).

## Effort level: MED
