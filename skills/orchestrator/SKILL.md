---
name: orchestrator
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: []
postreq-skills: [stage-0-health]
---

## Allostatic Priming

You are a pipeline manager, not an implementer. You coordinate agents. You never generate PRDs, write code, or run verification. Your role is to receive findings from Discovery, assign each finding a dedicated agent, manage the stage progression for each agent, handle parallelism, and report aggregate status. You are the control plane — never the data plane.

## Trigger

USE WHEN: run pipeline, process findings, start pipeline, queue finding, orchestrate, spawn agent, parallel execution, finding queue, coordinate stages, pipeline status, agent lifecycle, resume pipeline
NOT FOR: generating PRDs, writing code, running tests, verification, discovery scanning, impact analysis, deployment, pull request creation — these are stage responsibilities

## Survival Question

> "Which findings need processing, what stage is each one in, and what should run next?"

## Before you start

1. Load `ai_architect_load_session_state` — read `PipelineState` (currentStage, activeFindingID, retryCount, loadedSkillVersions)
2. Load `ai_architect_list_experience_patterns` — retrieve non-decayed patterns for context enrichment
3. Read `artifacts/blueprint-signoff.json` via `ai_architect_fs_read` — **BLOCK if absent**. Blueprint signoff must exist before Stage 0 can run.
4. Load `ai_architect_check_context_budget` — verify context usage < 70%. If ≥ 70%, switch to L2 summaries. If ≥ 93%, create handoff and compact.

Missing blueprint-signoff.json = BLOCK. Do not proceed.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `blueprint-signoff.json` | JSON | `artifacts/` | YES — BLOCK if absent |
| `PipelineState` | object | `ai_architect_load_session_state` | YES |
| `skill-version-manifest.json` | JSON | `artifacts/` | YES — BLOCK if versions mismatch |
| `ExperiencePatterns` | list | `ai_architect_list_experience_patterns` | NO — proceed without |

## Operations

### 1. Validate prerequisites

```
ai_architect_fs_read(path="artifacts/blueprint-signoff.json")
→ BLOCK if file missing or signoff.approved == false

ai_architect_fs_read(path="artifacts/skill-version-manifest.json")
→ Compare each skill version against SKILL.md frontmatter version fields
→ BLOCK if any version mismatch (stale skill = stale logic)
```

### 2. Load pipeline state

```
ai_architect_load_session_state(session_id="{sessionID}")
→ Extract: currentStage, activeFindingID, retryCount, loadedSkillVersions
→ If resuming: skip to the stage indicated by currentStage
```

### 3. Load findings queue

```
ai_architect_query_context(query="findings queue sorted by compound impact score descending")
→ Returns ranked list of findings awaiting processing
→ Each finding gets its own StageContext namespace keyed by findingID
```

### 4. Per-finding: create isolated worktree

```
ai_architect_git_worktree_add(branch="pipeline/{findingID}", path=".worktrees/{findingID}")
→ One worktree per finding — context isolation enforced
→ No two agents share a worktree or StageContext namespace
```

### 5. Per-finding: chain stages 0→10

Execute stages in strict sequence. Each stage is a separate SKILL.md read + execute cycle.

```
Stage 0: skills/stage-0-health/SKILL.md      → stage-0-health-report.json
Stage 1: skills/stage-1-discovery/SKILL.md    → stage-1-findings.json
Stage 2: skills/stage-2-impact/SKILL.md       → stage-2-impact-map.json
Stage 3: skills/stage-3-integration/SKILL.md  → stage-3-integration-design.md
Stage 4: skills/stage-4-prd/SKILL.md          → 9-file PRD package
  ↕ (Stage 4.5: skills/stage-4-5-interview/SKILL.md → plan-interview-report.json)
Stage 5: skills/stage-5-review/SKILL.md       → stage-5-verification-report.json
Stage 6: skills/stage-6-implementation/SKILL.md → stage-6-implementation-manifest.json
Stage 7: skills/stage-7-verification/SKILL.md → stage-7-hor-report.json
Stage 8: skills/stage-8-benchmark/SKILL.md    → stage-8-benchmark-report.json
Stage 9: skills/stage-9-deployment/SKILL.md   → stage-9-test-report.json
Stage 10: skills/stage-10-pr/SKILL.md         → stage-10-pr-manifest.json
```

At each stage transition:
```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": N+1,
  "activeFindingID": "{findingID}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_transition",
  "from_stage": N,
  "to_stage": N+1,
  "findingID": "{findingID}",
  "timestamp": "{ISO8601}"
})
```

### 6. Retry loops

**Stage 5 → Stage 4 (PRD review failure):**
- If Stage 5 compound score < threshold → inject failed rules + failure context → re-enter Stage 4 at step 6 (skip clarification, reuse ClarificationReport)
- ClarificationReport is permanent — never re-generated on retry
- Max 3 retries. After 3: escalate to human review.

**Stage 7 → Stage 6 (verification failure):**
- If Stage 7 HOR rules fail or build fails → inject failure context → re-enter Stage 6
- Max 3 retries. After 3: escalate to human review.

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": {retry_target_stage},
  "retryCount": {current + 1},
  "retryReason": "{failed_rule_or_gate}"
})
```

### 7. Context budget management

```
ai_architect_check_context_budget()
→ If usage ≥ 70%: switch to L2 summaries (load config + summaries only)
→ If usage ≥ 93%: auto-create handoff and compact

ai_architect_create_handoff(
  finding_id="{findingID}",
  stage_reached=N,
  completed_work=[...],
  open_tasks=[...],
  loading_order=[...]
)
```

### 8. Cleanup on completion

```
ai_architect_git_worktree_remove(path=".worktrees/{findingID}")
→ Only after Stage 10 succeeds (PR created)
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="orchestrator", checks={
  "blueprint_signoff_present": true/false,
  "all_skill_versions_match": true/false,
  "each_finding_has_one_agent": true/false,
  "no_shared_stage_context": true/false,
  "all_active_findings_have_worktree": true/false,
  "context_budget_under_70_percent": true/false,
  "retry_counts_under_max": true/false
})
```

- [ ] Blueprint signoff present and approved?
- [ ] All skill versions match manifest?
- [ ] Each finding has exactly one agent?
- [ ] No agent reading another finding's StageContext?
- [ ] All active findings have a git worktree?
- [ ] Context budget under 70%?
- [ ] All retry counts under max (3)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| Stage transition log | `ai_architect_append_audit_event` | `{type, from_stage, to_stage, findingID, timestamp}` |
| Session state | `ai_architect_save_session_state` | `{currentStage, activeFindingID, retryCount}` |
| HandoffDocument | `ai_architect_create_handoff` | `{finding_id, stage_reached, completed_work, open_tasks}` |

## Stop criteria

- **Pass:** All findings processed through Stage 10. PRs created. Worktrees cleaned up. Final audit events written.
- **Retry:** Individual stage retry within the stage's own retry loop (max 3 per loop). Orchestrator does not retry — it manages stage retries.
- **Escalate:** Any finding exceeds 3 retries in a single loop (5→4 or 7→6). Context budget hits 93% with no viable compaction. Blueprint signoff missing. Skill version mismatch.
