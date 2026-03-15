---
name: stage-0-health
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [orchestrator]
postreq-skills: [stage-1-discovery]
---

## Allostatic Priming

You are a systems operator running pre-flight checks. Nothing proceeds until everything is green. You do not interpret results — you verify them. Every dependency, every tool, every skill version must be confirmed available and at the expected version before the pipeline can begin.

## Trigger

USE WHEN: health check, pre-flight, validate environment, check dependencies, system ready, tool availability, skill version, dependency validation, startup verification, environment check, system status, ready check
NOT FOR: discovery scanning, impact analysis, PRD generation, code implementation, verification, deployment — those are downstream stages

## Survival Question

> "Is every dependency, tool, and skill version available and correct for this pipeline run?"

## Before you start

1. `ai_architect_load_session_state` — read PipelineState. If currentStage > 0, this stage was already completed — skip.
2. `ai_architect_fs_read(path="artifacts/skill-version-manifest.json")` — load expected skill versions.

Missing session state on first run = expected. Missing skill-version-manifest = BLOCK.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `skill-version-manifest.json` | JSON | `artifacts/` | YES — BLOCK if absent |
| `PipelineState` | object | `ai_architect_load_session_state` | NO — first run creates it |

## Operations

### 1. MCP server health check

```
ai_architect_load_context(stage="health-check", finding_id="{findingID}")
→ If MCP server responds: PASS
→ If timeout or error: BLOCK — MCP server unreachable
```

Verify all tool groups present by calling one tool from each group:
- Verification: `ai_architect_verify_claim` (dry run)
- Prompting: `ai_architect_select_strategy`
- Context: `ai_architect_load_context`
- Scoring: `ai_architect_compound_score`
- Adapters: `ai_architect_fs_list`
- Interview: `ai_architect_query_interview_results`
- Memory: `ai_architect_check_context_budget`
- HOR: `ai_architect_run_hor_rules` (dry run with empty input)
- Xcode: `ai_architect_run_build` (connectivity check only)

### 2. Validate skill versions

```
ai_architect_fs_read(path="artifacts/skill-version-manifest.json")
→ For each skill in manifest:
  ai_architect_fs_read(path="skills/{skill-name}/SKILL.md")
  → Parse frontmatter version field
  → Compare to manifest version
  → Mismatch = BLOCK with message: "Skill '{name}' version {actual} does not match manifest {expected}"
```

### 3. Git and GitHub connectivity

```
ai_architect_git_diff(ref="HEAD")
→ Success = git operational
→ Failure = BLOCK — git not available

ai_architect_fs_list(path=".")
→ Confirms filesystem adapter operational
```

### 4. Foundation Models reachability (optional)

Foundation Models availability is checked but not blocking. Pipeline continues if Foundation Models is offline — Apple Intelligence features degrade gracefully.

### 5. Write health report

```
ai_architect_save_context(
  stage="stage-0",
  finding_id="{findingID}",
  data={
    "mcp_server": "reachable",
    "tool_groups": {"verification": true, "prompting": true, "context": true, "scoring": true, "adapters": true, "interview": true, "memory": true, "hor": true, "xcode": true},
    "skill_versions": "all_match",
    "git": "operational",
    "github": "authenticated",
    "foundation_models": true/false,
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path=".ai-architect/artifacts/stage-0-health-report.json",
  content={health report JSON}
)
```

### 6. Update pipeline state

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 1,
  "activeFindingID": "{findingID}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 0,
  "outcome": "pass",
  "findingID": "{findingID}"
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-0", checks={
  "mcp_server_reachable": true/false,
  "all_tool_groups_present": true/false,
  "all_skill_versions_match_manifest": true/false,
  "git_operational": true/false,
  "github_authenticated": true/false,
  "health_report_written": true/false
})
```

- [ ] All MCP tool groups reachable?
- [ ] All skill versions match manifest?
- [ ] Git operational?
- [ ] GitHub authenticated?
- [ ] Health report written to StageContext?
- [ ] No scope bleed into adjacent stage?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-0-health-report.json` | `.ai-architect/artifacts/` | `{mcp_server, tool_groups, skill_versions, git, github, foundation_models, timestamp}` |
| StageContext[stage-0] | `ai_architect_save_context` | Same as report |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 1}` |

## Stop criteria

- **Pass:** All mandatory checks green. Health report written. PipelineState.currentStage = 1.
- **Retry:** Not applicable — health check is binary. If it fails, fix the environment, do not retry the check.
- **Escalate:** Any mandatory check fails (MCP unreachable, skill version mismatch, git unavailable). Report which check failed and what to fix.

## Effort level: LOW
