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

1. `ai_architect_load_context(stage="stage-1", finding_id="{findingID}")` — load findings from Stage 1
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 2
3. `ai_architect_list_experience_patterns(category="pattern")` — load architecture patterns for impact context

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
→ Identify key structural files: Package.swift, port definitions, adapter files

ai_architect_fs_read(path="{port_files}")
→ Load port protocols to understand dependency structure
```

### 2. Run Collaborative Inference (Algorithm 8)

Multiple perspectives analyze the finding's impact:

```
ai_architect_expand_thought(
  thought="Analyze impact of finding '{findingID}' on codebase",
  strategy="collaborative_inference",
  perspectives=["performance", "security", "maintainability", "scope"]
)
→ Returns multi-perspective impact analysis
→ Each perspective scores 0.0–1.0
```

### 3. Enhance prompt for propagation mapping

```
ai_architect_select_strategy(
  task_type="impact_analysis",
  context="trace dependency graph for cascade points"
)

ai_architect_enhance_prompt(
  prompt="Decompose finding '{findingID}' into affected packages, trace dependency graph, identify cascade points",
  strategy="planAndSolve",
  context="{codebase_structure + finding_details}"
)
→ Returns: affected packages, dependency chains, cascade points
```

### 4. Compute compound impact score

```
ai_architect_compound_score(
  scores={
    "relevance": {from_stage_1},
    "performance_impact": {from_step_2},
    "security_impact": {from_step_2},
    "maintainability_impact": {from_step_2},
    "scope_impact": {from_step_2},
    "propagation_depth": {number_of_cascade_levels},
    "affected_package_count": N
  },
  weights={
    "relevance": 0.2,
    "performance_impact": 0.15,
    "security_impact": 0.2,
    "maintainability_impact": 0.15,
    "scope_impact": 0.15,
    "propagation_depth": 0.1,
    "affected_package_count": 0.05
  }
)
→ Returns compound impact score 0.0–1.0
```

### 5. Trace propagation paths

```
ai_architect_trace_propagation(
  finding_id="{findingID}",
  entry_points=["{affected_port_1}", "{affected_port_2}"],
  depth=3
)
→ Returns propagation tree: which adapters, engines, and modules are affected
→ Identifies cascade points where a single change triggers multiple downstream updates
```

### 6. Write impact map to StageContext

```
ai_architect_save_context(
  stage="stage-2",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "compoundImpactScore": 0.0-1.0,
    "propagationPaths": [...],
    "affectedEngines": [...],
    "affectedPackages": [...],
    "cascadePoints": [...],
    "perspectiveScores": {
      "performance": 0.0-1.0,
      "security": 0.0-1.0,
      "maintainability": 0.0-1.0,
      "scope": 0.0-1.0
    },
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path=".ai-architect/artifacts/stage-2-impact-map.json",
  content={impact map JSON}
)
```

### 7. Update pipeline state and audit

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 3,
  "activeFindingID": "{findingID}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 2,
  "outcome": "pass",
  "findingID": "{findingID}",
  "compoundImpactScore": {score}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-2", checks={
  "compound_impact_score_computed": true/false,
  "propagation_paths_non_empty": true/false,
  "affected_engines_listed": true/false,
  "impact_map_written_to_stage_context": true/false,
  "stage_1_output_untouched": true/false
})
```

- [ ] Compound impact score computed (0.0–1.0)?
- [ ] Propagation paths non-empty?
- [ ] Affected engines listed?
- [ ] ImpactMap written to StageContext?
- [ ] Stage 1 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-2-impact-map.json` | `.ai-architect/artifacts/` | `{findingID, compoundImpactScore, propagationPaths, affectedEngines, affectedPackages, cascadePoints, perspectiveScores}` |
| StageContext[stage-2] | `ai_architect_save_context` | Same as impact map |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 3}` |

## Stop criteria

- **Pass:** Compound impact score computed. Propagation paths non-empty. Impact map written. PipelineState.currentStage = 3.
- **Retry:** Propagation paths empty (no cascade detected) — re-run with broader codebase context (load more port files). Max 2 retries.
- **Escalate:** Finding has zero affected packages after retry. Compound scoring tool returns error. Codebase structure unreadable.

## Effort level: MED
