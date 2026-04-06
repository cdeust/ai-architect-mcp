---
name: stage-2-impact
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-1-discovery]
postreq-skills: [stage-3-integration]
---

## Allostatic Priming

You are a senior architect assessing blast radius. Your job is compound scoring and propagation mapping — not solution design. You find what breaks when this changes. Every finding gets a compound impact score (0.0–1.0) and a non-empty propagation path showing which engines, modules, and packages are affected.

## Trigger

USE WHEN: impact analysis, blast radius, propagation, compound score, what breaks, affected engines, dependency graph, cascade, impact mapping
NOT FOR: design integration, generate PRD, discovery — that was stage 1

## Survival Question

> "Do I have a compound impact score and a non-empty propagation path for this finding?"

## Before you start

**MANDATORY: Load ALL required upstream artifacts.**

1. `ai_architect_load_context(stage_id=0, finding_id="{findingID}")` — load Stage 0 health report (check `codebase_intelligence` field for codebase intelligence engine availability)
2. `ai_architect_load_context(stage_id=1, finding_id="{findingID}")` — load Stage 1 findings (finding details, relevance scores, codebase matches)
3. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 2
4. `ai_architect_list_experience_patterns(stage_id=2, min_relevance=0.1)` — load architecture patterns for impact context

**If `codebase_intelligence: "ai_codebase_intelligence"` in Stage 0 health report:**
5. `ai_architect_codebase_impact(target="{primary_symbol}", direction="upstream", repo="{target_repo}")` — blast radius analysis
6. `ai_architect_codebase_context(name="{primary_symbol}", include_content=true, repo="{target_repo}")` — full symbol context with callers

Missing Stage 1 findings = BLOCK. Cannot analyze impact without findings.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-1-findings.json` | JSON | StageContext[stage-1] | YES — BLOCK if missing |
| Finding to analyze | object | Top finding from Stage 1 | YES |
| Codebase structure | files | `ai_architect_fs_list` / `ai_architect_fs_read` | YES — need dependency context |

## Operations

### 1. Load codebase structural context

```
ai_architect_fs_list(path=".")
→ Identify key structural files: build manifests (Package.swift, package.json,
  Cargo.toml, go.mod, pyproject.toml, etc.) and interface definitions

ai_architect_fs_read(path="{interface_files}")
→ Load interface/protocol definitions to understand dependency structure
```

If codebase intelligence engine is available (from Stage 0 health report):
```
ai_architect_codebase_impact(
  target="{affected_files}",
  direction="downstream",
  repo="{target_repo}"
)
→ Precise impact analysis: which files, modules, and tests are affected
→ More accurate than filesystem scanning for large codebases
```

If git analytics are available (from Stage 0 health report `git_analytics: "available"`):
```
ai_architect_codebase_ownership(path="{affected_file}", repo="{target_repo}")
→ Per-file ownership ratio and minor contributor count
→ (Bird et al. 2011) — files with ownership < 0.5 have diffuse responsibility = higher defect risk
→ If ownership < 0.5 for any affected file: flag as HIGH risk in perspective_scores

ai_architect_codebase_bus_factor(path="{affected_module}", repo="{target_repo}")
→ Knowledge concentration: how many contributors must leave before knowledge is lost
→ (Avelino et al. 2016) — bus_factor <= 2 means critical knowledge concentration
→ If bus_factor <= 2 for any affected module: flag as HIGH risk, add to cascade_points
```

Risk escalation rule: if a file in the propagation path has ownership < 0.5 OR bus_factor <= 2, increase the maintainability perspective score by 0.2 (capped at 1.0). Document the rationale in the impact map artifact under a `git_analytics_flags` field.

### 2. Run Collaborative Inference (Algorithm 8)

Multiple perspectives analyze the finding's impact:

```
ai_architect_expand_thought(
  prompt="Analyze impact of finding '{findingID}' on codebase from four perspectives: performance, security, maintainability, and scope. Score each 0.0–1.0.",
  context="{finding_details + codebase_structure}",
  max_depth=4
)
→ Returns multi-perspective impact analysis
→ Each perspective scores 0.0–1.0
```

### 3. Enhance prompt for propagation mapping

```
ai_architect_select_strategy(
  project_type="impact_analysis",
  complexity="high",
  characteristics=["dependency_tracing", "cascade_detection", "propagation_mapping"]
)

ai_architect_enhance_prompt(
  prompt="Decompose finding '{findingID}' into affected packages, trace dependency graph, identify cascade points",
  context="{codebase_structure + finding_details}",
  max_iterations=3
)
→ Returns: affected packages, dependency chains, cascade points
```

### 4. Compute compound impact score

```
ai_architect_compound_score(
  relevance={from_stage_1},
  uniqueness={novelty_vs_existing_findings},
  impact={average_of_perspective_scores},
  confidence={propagation_coverage_ratio},
  weights={
    "relevance": 0.25,
    "uniqueness": 0.15,
    "impact": 0.40,
    "confidence": 0.20
  }
)
→ Returns compound impact score 0.0–1.0
```

### 5. Trace propagation paths

```
ai_architect_trace_propagation(
  source_module="{affected_module}",
  dependency_graph={
    "{module_A}": ["{module_B}", "{module_C}"],
    "{module_B}": ["{module_D}"],
    "{module_C}": ["{module_D}", "{module_E}"]
  },
  max_depth=3
)
→ Returns propagation paths and impact score
→ Identifies cascade points where a single change triggers multiple downstream updates
```

### 6. Write impact map to StageContext

```
ai_architect_save_context(
  stage_id=2,
  finding_id="{findingID}",
  artifact={
    "finding_id": "{findingID}",
    "compound_impact_score": 0.0-1.0,
    "propagation_paths": [...],
    "affected_engines": [...],
    "affected_packages": [...],
    "cascade_points": [...],
    "perspective_scores": {
      "performance": 0.0-1.0,
      "security": 0.0-1.0,
      "maintainability": 0.0-1.0,
      "scope": 0.0-1.0
    },
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-2-impact-map.json",
  content={impact map JSON}
)
```

### 7. Update pipeline state and audit

```
ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 3,
  "status": "running",
  "completed_stages": [0, 1, 2]
})

ai_architect_append_audit_event(event_data={
  "event_id": "stage-2-complete-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 2,
  "tool_name": "stage-2-impact",
  "outcome": "pass",
  "message": "Stage 2 impact analysis completed for finding {findingID}",
  "metadata": {"compound_impact_score": "{score}"}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage_id=2, phase="observe", decision="Compound impact score computed: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=2, phase="observe", decision="Propagation paths non-empty: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=2, phase="observe", decision="Affected engines listed: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=2, phase="observe", decision="Impact map written to StageContext: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=2, phase="decide", decision="Stage 1 output untouched: {true/false}", confidence=1.0, session_id="{sessionID}")
```

- [ ] Compound impact score computed (0.0–1.0)?
- [ ] Propagation paths non-empty?
- [ ] Affected engines listed?
- [ ] ImpactMap written to StageContext?
- [ ] Stage 1 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-2-impact-map.json` | `{data_dir}/artifacts/` | `{findingID, compoundImpactScore, propagationPaths, affectedEngines, affectedPackages, cascadePoints, perspectiveScores}` |
| StageContext[stage-2] | `ai_architect_save_context` | Same as impact map |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 3}` |

## Stop criteria

- **Pass:** Compound impact score computed. Propagation paths non-empty. Impact map written. PipelineState.currentStage = 3.
- **Retry:** Propagation paths empty (no cascade detected) — re-run with broader codebase context (load more port files). Max 2 retries.
- **Escalate:** Finding has zero affected packages after retry. Compound scoring tool returns error. Codebase structure unreadable.

## Effort level: MED
