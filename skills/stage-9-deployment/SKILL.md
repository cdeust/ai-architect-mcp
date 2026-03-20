---
name: stage-9-deployment
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-8-benchmark]
postreq-skills: [stage-10-pr]
---

## Allostatic Priming

You are a QA gate. All tests must pass. No exceptions. You do not interpret failures — you report them and block. The full test suite runs: unit tests, integration tests, and any end-to-end tests defined in prd-tests.md. A single failure blocks progression.

## Trigger

USE WHEN: run tests, test suite, deploy, all tests pass, QA gate, test execution, swift test, pytest, full test run, test validation, coverage check
NOT FOR: code implementation — stage 6, verification rules — stage 7, benchmarking — stage 8, PRD generation, pull request

## Survival Question

> "Do all tests in the full suite pass with zero failures?"

## Before you start

1. `ai_architect_load_context(stage="stage-8", finding_id="{findingID}")` — load benchmark report (confirms performance gates passed)
2. `ai_architect_load_context(stage="stage-4", finding_id="{findingID}")` — load prd-tests.md for test suite definitions
3. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 9

Missing Stage 8 benchmark report = BLOCK. Cannot run tests without verified benchmarks.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-8-benchmark-report.json` | JSON | StageContext[stage-8] | YES — BLOCK if missing |
| `prd-tests.md` | MD | StageContext[stage-4] | YES — test suite definitions |
| Implementation branch | git ref | `pipeline/{findingID}` | YES — code to test |

## Operations

### 1. Run full test suite

```
ai_architect_run_tests(
  project_path="{project_root}",
  test_filter="*",
  timeout=600
)
→ Runs all @Test @Suite tests defined in prd-tests.md
→ Captures: pass/fail per test, coverage percentage, failure details
→ Zero failures required for progression
```

Test categories from prd-tests.md:
- Unit tests (UT-XXX → AC-XXX traceability)
- Integration tests
- End-to-end tests (if defined)

### 2. Run Python test suite (MCP server)

```
ai_architect_run_tests(
  project_path="mcp/",
  test_filter="*",
  timeout=300
)
→ pytest on MCP server tests
→ Captures pass/fail and coverage
```

### 3. Capture coverage and failures

```
For each test result:
  {
    "test_name": "{test_name}",
    "suite": "{suite_name}",
    "result": "pass|fail",
    "duration_ms": N,
    "failure_message": "{if_failed}",
    "ac_ref": "AC-XXX"
  }

Coverage summary:
  {
    "line_coverage": 0.0-1.0,
    "branch_coverage": 0.0-1.0,
    "uncovered_files": [...]
  }
```

### 4. Write test report

```
ai_architect_save_context(
  stage="stage-9",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "testResults": [...],
    "totalTests": N,
    "passed": M,
    "failed": F,
    "coverage": {
      "line": 0.0-1.0,
      "branch": 0.0-1.0
    },
    "allTestsPass": true/false,
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-9-test-report.json",
  content={test report JSON}
)
```

### 5. Update pipeline state and audit

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 10,
  "activeFindingID": "{findingID}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 9,
  "outcome": "pass",
  "findingID": "{findingID}",
  "totalTests": N,
  "passed": M,
  "failed": F,
  "coverage": {...}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-9", checks={
  "all_tests_executed": true/false,
  "zero_failures": true/false,
  "coverage_captured": true/false,
  "test_report_written": true/false,
  "stage_8_output_untouched": true/false
})
```

- [ ] All tests executed?
- [ ] Zero failures?
- [ ] Coverage captured?
- [ ] Test report written to StageContext?
- [ ] Stage 8 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-9-test-report.json` | `{data_dir}/artifacts/` | `{findingID, testResults, totalTests, passed, failed, coverage, allTestsPass}` |
| StageContext[stage-9] | `ai_architect_save_context` | Same as test report |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 10}` |

## Stop criteria

- **Pass:** All tests pass. Zero failures. Coverage captured. Test report written. PipelineState.currentStage = 10.
- **Retry:** Test failures — loop back to Stage 6 for fixes. Max 2 retries. Test failures require implementation changes.
- **Escalate:** Tests fail after retries. Coverage below acceptable threshold. Test infrastructure broken (cannot execute tests).

## Effort level: MED
