---
name: stage-3-integration
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-2-impact]
postreq-skills: [stage-4-prd]
---

## Allostatic Priming

You are a software architect designing the seam where this change meets the existing system. Hexagonal architecture. Ports and adapters. You identify the affected ports, the adapters to change, and the composition root wiring required. You do not implement — you design the integration blueprint.

## Trigger

USE WHEN: integration design, architecture design, affected ports, adapter design, cross-engine, hexagonal, composition root, port inventory, seam analysis, interface design
NOT FOR: plan interview, PRD generation, impact analysis — stage 2, implementation — stage 6

## Survival Question

> "Do I have a complete list of affected ports, adapters, and composition root changes — with no circular dependency introduced?"

## Before you start

1. `ai_architect_load_context(stage="stage-2", finding_id="{findingID}")` — load impact map from Stage 2
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 3
3. `ai_architect_list_experience_patterns(category="decision")` — load architecture decisions for context

Missing Stage 2 impact map = BLOCK. Cannot design integration without knowing blast radius.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-2-impact-map.json` | JSON | StageContext[stage-2] | YES — BLOCK if missing |
| ImpactMap.affectedEngines | list | Stage 2 output | YES |
| Port definitions | files | Codebase `Domain/Ports/` | YES — need to cross-reference |

## Operations

### 1. Read port protocols and cross-reference with impact map

```
ai_architect_fs_list(path="Domain/Ports/")
→ List all port protocol files

For each port file:
  ai_architect_fs_read(path="Domain/Ports/{port_file}")
  → Parse protocol definition
  → Cross-reference with ImpactMap.affectedEngines
  → Mark ports requiring modification
```

### 2. Design adapter changes per affected engine

```
ai_architect_enhance_prompt(
  prompt="Design integration blueprint for finding '{findingID}': affected engines={affectedEngines}, affected ports={affected_ports}",
  strategy="verifiedReasoning",
  context="{port_definitions + impact_map + codebase_structure}"
)
→ Returns per-engine:
  - Which adapter files need modification
  - New port methods required (if any)
  - Composition root wiring changes
  - File change manifest
```

### 3. Verify no circular dependencies

```
ai_architect_verify_graph(
  claims=["{dependency_1}", "{dependency_2}", ...],
  graph_type="dependency"
)
→ Verify: no circular package dependencies introduced
→ Verify: adapter context decided (Xcode vs LocalFS vs mixed)
```

### 4. Map composition root wiring

Identify factory files requiring update. No new package-level dependencies unless justified with a rationale documented in the integration design.

### 5. Write integration design to StageContext

```
ai_architect_save_context(
  stage="stage-3",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "affectedPorts": [...],
    "adapterChanges": [
      {
        "engine": "{engine_name}",
        "port": "{port_protocol}",
        "adapterFile": "{file_path}",
        "changeType": "modify|create",
        "newMethods": [...]
      }
    ],
    "compositionRootChanges": [...],
    "fileChangeManifest": [...],
    "adapterContext": "xcode|localfs|mixed",
    "noCircularDeps": true,
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path=".ai-architect/artifacts/stage-3-integration-design.md",
  content={integration design markdown}
)
```

### 6. Update pipeline state and audit

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 4,
  "activeFindingID": "{findingID}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 3,
  "outcome": "pass",
  "findingID": "{findingID}",
  "affected_ports_count": N,
  "adapter_changes_count": M
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-3", checks={
  "all_affected_ports_identified": true/false,
  "no_circular_package_dependencies": true/false,
  "adapter_context_decided": true/false,
  "file_change_manifest_complete": true/false,
  "integration_design_readonly_from_here": true/false,
  "stage_2_output_untouched": true/false
})
```

- [ ] All affected ports identified?
- [ ] No new circular package dependencies?
- [ ] Adapter context decided (Xcode vs LocalFS vs mixed)?
- [ ] File change manifest complete?
- [ ] IntegrationDesign marked read-only from here — Stage 4 cannot modify it?
- [ ] Stage 2 output untouched?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-3-integration-design.md` | `.ai-architect/artifacts/` | Markdown with affected ports, adapter changes, composition root, file manifest |
| StageContext[stage-3] | `ai_architect_save_context` | `{findingID, affectedPorts, adapterChanges, compositionRootChanges, fileChangeManifest, adapterContext}` |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 4}` |

## Stop criteria

- **Pass:** All affected ports identified. No circular deps. File change manifest complete. Integration design written. PipelineState.currentStage = 4.
- **Retry:** Circular dependency detected — redesign adapter boundaries. Max 2 retries.
- **Escalate:** Cannot resolve circular dependency after retries. Impact map references engines not found in codebase. Port definitions unreadable.

## Effort level: MED
