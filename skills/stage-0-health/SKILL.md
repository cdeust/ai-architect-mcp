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
2. `ai_architect_fs_read(path="{data_dir}/artifacts/skill-version-manifest.json")` — load expected skill versions.

Missing session state on first run = expected. Missing skill-version-manifest = BLOCK.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `skill-version-manifest.json` | JSON | `{data_dir}/artifacts/` | YES — BLOCK if absent |
| `PipelineState` | object | `ai_architect_load_session_state` | NO — first run creates it |

## Operations

### 1. MCP server health check

```
ai_architect_load_context(stage_id=0, finding_id="{findingID}")
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
- Memory: `ai_architect_check_context_budget(total_tokens=200000, used_tokens=0)`
- HOR: `ai_architect_run_hor_rules` (dry run with empty input)
- Xcode: `ai_architect_run_build` (connectivity check only)

### 2. Validate skill versions

```
ai_architect_fs_read(path="{data_dir}/artifacts/skill-version-manifest.json")
→ For each skill in manifest:
  ai_architect_fs_read(path="skills/{skill-name}/SKILL.md")
  → Parse frontmatter version field
  → Compare to manifest version
  → Mismatch = BLOCK with message: "Skill '{name}' version {actual} does not match manifest {expected}"
```

### 3. Git and GitHub connectivity

```
ai_architect_git_diff(base="HEAD~1", head="HEAD")
→ Success = git operational
→ Failure = BLOCK — git not available

ai_architect_fs_list(path=".")
→ Confirms filesystem adapter operational
```

### 4. Codebase intelligence probe (optional)

Probe for codebase intelligence engine MCP tools (`ai_architect_codebase_*`). If available, record `codebase_intelligence: "ai_codebase_intelligence"` in the health report. Downstream stages use the codebase intelligence engine for blast radius, symbol search, and dependency graphs when available. If unavailable, record `codebase_intelligence: "filesystem_only"` — downstream stages fall back to `ai_architect_fs_list` + grep patterns.

Available codebase intelligence tools (from `codebase-intelligence` MCP server):
- `ai_architect_codebase_list_repos()` — list indexed repositories
- `ai_architect_codebase_query(query, repo="", limit=5, max_symbols=10, include_content=false)` — hybrid search
- `ai_architect_codebase_context(name="", uid="", file_path="", include_content=false, repo="")` — 360-degree symbol view
- `ai_architect_codebase_impact(target, direction="upstream", maxDepth=3, repo="")` — blast radius analysis
- `ai_architect_codebase_cypher(query, repo="")` — raw Cypher queries
- `ai_architect_codebase_detect_changes(repo="", scope="unstaged", base_ref="")` — git diff to affected symbols

Git analytics tools (science-backed, from `codebase-intelligence` MCP server):
- `ai_architect_codebase_ownership(path, repo="")` — per-file ownership ratio and minor contributors (Bird et al. 2011, "Don't Touch My Code!")
- `ai_architect_codebase_bus_factor(path, repo="")` — knowledge concentration risk per module (Avelino et al. 2016, "A Novel Approach for Estimating Truck Factors")
- `ai_architect_codebase_churn(path, repo="")` — relative code churn: additions, deletions, churn ratio (Nagappan & Ball 2005, "Use of Relative Code Churn Measures to Predict System Defect Density")
- `ai_architect_codebase_cochange(path, repo="")` — co-change frequency detecting hidden temporal coupling (Gall et al. 1998, "Detection of Logical Coupling Based on Product Release History")
- `ai_architect_codebase_dead_code(path, repo="")` — unreachable code candidates via call graph analysis (Grove et al. 1997, "Call Graph Construction in Object-Oriented Languages")

Probe each git analytics tool with a known path. If any responds: record `git_analytics: "available"` in the health report. If all fail or timeout: record `git_analytics: "unavailable"` — downstream stages skip analytics enrichment.

### 5. Foundation Models reachability (optional)

Foundation Models availability is checked but not blocking. Pipeline continues if Foundation Models is offline — Apple Intelligence features degrade gracefully.

### 6. Write health report

```
ai_architect_save_context(
  stage_id=0,
  finding_id="{findingID}",
  artifact={
    "mcp_server": "reachable",
    "tool_groups": {"verification": true, "prompting": true, "context": true, "scoring": true, "adapters": true, "interview": true, "memory": true, "hor": true, "xcode": true},
    "skill_versions": "all_match",
    "git": "operational",
    "github": "authenticated",
    "foundation_models": true/false,
    "git_analytics": "available"/"unavailable",
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-0-health-report.json",
  content={health report JSON}
)
```

### 7. Update pipeline state

```
ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 1,
  "status": "running",
  "completed_stages": [0]
})

ai_architect_append_audit_event(event_data={
  "event_id": "stage-0-complete-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 0,
  "tool_name": "stage-0-health",
  "outcome": "pass",
  "message": "Stage 0 health check completed for finding {findingID}"
})
```

## OODA Checkpoint

Emit one OODA checkpoint per verification point. Each call uses the real tool signature:

```
ai_architect_emit_ooda_checkpoint(stage_id=0, phase="observe", decision="MCP server reachable: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=0, phase="observe", decision="All tool groups present: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=0, phase="observe", decision="All skill versions match manifest: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=0, phase="observe", decision="Git operational: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=0, phase="observe", decision="GitHub authenticated: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=0, phase="decide", decision="Health report written: {true/false}", confidence=1.0, session_id="{sessionID}")
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
| `stage-0-health-report.json` | `{data_dir}/artifacts/` | `{mcp_server, tool_groups, skill_versions, git, github, foundation_models, git_analytics, timestamp}` |
| StageContext[stage-0] | `ai_architect_save_context` | Same as report |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 1}` |

## Stop criteria

- **Pass:** All mandatory checks green. Health report written. PipelineState.currentStage = 1.
- **Retry:** Not applicable — health check is binary. If it fails, fix the environment, do not retry the check.
- **Escalate:** Any mandatory check fails (MCP unreachable, skill version mismatch, git unavailable). Report which check failed and what to fix.

## Effort level: LOW
