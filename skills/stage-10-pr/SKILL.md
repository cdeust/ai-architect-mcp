---
name: stage-10-pr
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-9-deployment]
postreq-skills: []
---

## Allostatic Priming

You are a delivery agent. Push. Create PR. Write audit trail. Close finding. Your output is a merge-ready pull request with a complete audit trail linking every change back to the original finding, through the PRD, to the verification report. The PR description is machine-generated from stage artifacts — not hand-written.

## Trigger

USE WHEN: create PR, pull request, push branch, deliver, merge ready, audit trail, GitHub PR, sha256 manifest, delivery, close finding, PR creation
NOT FOR: code implementation — stage 6, verification — stage 7, benchmarking — stage 8, test execution — stage 9

## Survival Question

> "Is the PR open on GitHub with correct labels, body, and audit trail reference?"

## Before you start

1. `ai_architect_load_context(stage="stage-9", finding_id="{findingID}")` — load test report (confirms all tests passed)
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 10
3. Load all stage artifacts for PR body assembly

Missing Stage 9 test report = BLOCK. Cannot create PR without passing tests.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-9-test-report.json` | JSON | StageContext[stage-9] | YES — BLOCK if missing |
| `stage-7-hor-report.json` | JSON | StageContext[stage-7] | YES — for PR body |
| `stage-2-impact-map.json` | JSON | StageContext[stage-2] | YES — impact score for PR body |
| `prd-overview.md` | MD | StageContext[stage-4] | YES — PRD overview for PR body |
| Implementation branch | git ref | `pipeline/{findingID}` | YES — branch to push |

## Operations

### 1. Push branch to remote

```
ai_architect_git_push(
  branch="pipeline/{findingID}",
  remote="origin"
)
→ Push implementation branch to GitHub
→ Failure = BLOCK — network issue, auth expired, or branch conflict
```

### 2. Create pull request

Assemble PR body from stage artifacts:

```
ai_architect_github_create_pr(
  title="[{findingID}] {finding_summary}",
  body={assembled_pr_body},
  base="main",
  head="pipeline/{findingID}",
  labels=["ai-architect", "pipeline-generated"]
)

PR body template:
  ## Finding
  - **ID:** {findingID}
  - **Impact Score:** {compoundImpactScore}
  - **Source:** {finding_source}

  ## PRD Overview
  {prd-overview summary}

  ## Verification Summary
  - **HOR Rules:** {pass_count}/64 passed
  - **Build:** PASS
  - **Tests:** {passed}/{total} passed
  - **Compound Score:** {score}

  ## Audit Trail
  - Stage artifacts: `.ai-architect/artifacts/`
  - HOR report: `stage-7-hor-report.json`
  - Test report: `stage-9-test-report.json`
  - sha256 manifest: `sha256-manifest.json`

→ Returns PR URL
```

### 3. Write final audit event

```
ai_architect_append_audit_event(event={
  "type": "pipeline_complete",
  "stage": 10,
  "outcome": "delivered",
  "findingID": "{findingID}",
  "prURL": "{pr_url}",
  "totalStages": 11,
  "totalRetries": {sum_of_all_retries},
  "compoundScores": {per_stage_scores},
  "timestamp": "{ISO8601}"
})
```

### 4. Generate sha256 manifest

Hash all 9 PRD files + all stage artifacts for tamper detection:

```
ai_architect_fs_read(path=".ai-architect/prd/prd-overview.md")
... (read all 9 PRD files + stage artifacts)

ai_architect_fs_write(
  path=".ai-architect/artifacts/sha256-manifest.json",
  content={
    "files": [
      {"path": "prd-overview.md", "sha256": "{hash}"},
      {"path": "prd-requirements.md", "sha256": "{hash}"},
      ... (all 9 PRD files + all stage artifacts)
    ],
    "generated_at": "{ISO8601}",
    "finding_id": "{findingID}"
  }
)
```

### 5. Distil experience patterns

The stop hook reads AuditEvents and distils ExperiencePatterns:

```
ai_architect_save_experience_pattern(
  content="{lesson_learned}",
  category="solution|pattern|decision|workaround|gotcha",
  half_life_days={200|300}
)
→ Pattern types: solution (200d), pattern (300d), decision (300d), workaround (200d), gotcha (200d)
→ Quality signals from compoundScore + retryCount inform pattern value
```

### 6. Write PR manifest

```
ai_architect_save_context(
  stage="stage-10",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "prURL": "{pr_url}",
    "branch": "pipeline/{findingID}",
    "labels": ["ai-architect", "pipeline-generated"],
    "sha256Manifest": "{manifest_path}",
    "auditTrailClosed": true,
    "experiencePatternsWritten": true,
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path=".ai-architect/artifacts/stage-10-pr-manifest.json",
  content={PR manifest JSON}
)
```

### 7. Update pipeline state (final)

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": "complete",
  "activeFindingID": "{findingID}",
  "status": "delivered",
  "prURL": "{pr_url}"
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-10", checks={
  "branch_pushed": true/false,
  "pr_open_on_github": true/false,
  "correct_labels_applied": true/false,
  "sha256_manifest_written": true/false,
  "audit_event_closed": true/false,
  "experience_patterns_written": true/false,
  "stage_9_output_untouched": true/false
})
```

- [ ] Branch pushed to remote?
- [ ] PR open on GitHub?
- [ ] Correct labels applied?
- [ ] sha256 manifest written?
- [ ] Final AuditEvent closed (outcome: delivered)?
- [ ] ExperiencePatterns written?
- [ ] Stage 9 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| Pull Request | GitHub | Merge-ready PR with audit trail body |
| `stage-10-pr-manifest.json` | `.ai-architect/artifacts/` | `{findingID, prURL, branch, labels, sha256Manifest, auditTrailClosed}` |
| `sha256-manifest.json` | `.ai-architect/artifacts/` | `{files: [{path, sha256}], generated_at, finding_id}` |
| ExperiencePatterns | `ai_architect_save_experience_pattern` | Distilled lessons from this pipeline run |
| StageContext[stage-10] | `ai_architect_save_context` | Same as PR manifest |
| PipelineState (final) | `ai_architect_save_session_state` | `{currentStage: "complete", status: "delivered", prURL}` |

## Stop criteria

- **Pass:** PR open on GitHub. sha256 manifest written. Audit trail closed. ExperiencePatterns distilled. Finding status = delivered.
- **Retry:** Git push failure (network) — retry push. Max 3 retries. PR creation failure — retry with simplified body.
- **Escalate:** GitHub authentication expired. Branch conflict on remote. PR creation blocked by branch protection rules.

## Effort level: LOW
