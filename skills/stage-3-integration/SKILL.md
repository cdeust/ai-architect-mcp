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

**MANDATORY: Load ALL required upstream artifacts.**

1. `ai_architect_load_context(stage_id=0, finding_id="{findingID}")` — load Stage 0 health report (codebase intelligence engine availability)
2. `ai_architect_load_context(stage_id=1, finding_id="{findingID}")` — load Stage 1 findings
3. `ai_architect_load_context(stage_id=2, finding_id="{findingID}")` — load Stage 2 impact map (propagation paths, affected engines)
4. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 3
5. `ai_architect_list_experience_patterns(category="decision")` — load architecture decisions for context

**If `codebase_intelligence: "ai_codebase_intelligence"` in Stage 0 health report:**
6. `ai_architect_codebase_cypher(query="MATCH (a)-[:CodeRelation {type: 'IMPLEMENTS'}]->(b) WHERE b.name IN {affected_ports} RETURN a.name, a.filePath", repo_path="{target_repo}")` — find existing adapter implementations
7. `ai_architect_codebase_context(name="{affected_port}", include_source=true, repo_path="{target_repo}")` — for each affected port from impact map

Missing Stage 2 impact map = BLOCK. Cannot design integration without knowing blast radius.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-2-impact-map.json` | JSON | StageContext[stage-2] | YES — BLOCK if missing |
| ImpactMap.affectedEngines | list | Stage 2 output | YES |
| Port/interface definitions | files | Codebase (discovered via search) | YES — need to cross-reference |

## Operations

### 1. Discover interface/protocol definitions and cross-reference with impact map

If codebase intelligence engine is available (from Stage 0 health report):
```
ai_architect_codebase_context(
  name="{affected_engines}",
  include_source=true,
  repo_path="{target_repo}"
)
→ Resolve dependency graph for affected symbols

ai_architect_codebase_context(
  name="{port_name}",
  include_source=true,
  repo_path="{target_repo}"
)
→ Full context for each affected interface/protocol
```

Fallback (filesystem scan):
```
ai_architect_fs_list(path=".")
→ Search for interface/protocol/abstract class definitions
→ Common patterns: *Port*, *Protocol*, *Interface*, *Abstract*

For each interface file:
  ai_architect_fs_read(path="{interface_file}")
  → Parse protocol/interface definition
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
  path="{data_dir}/artifacts/stage-3-integration-design.md",
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
| `stage-3-integration-design.md` | `{data_dir}/artifacts/` | Markdown with affected ports, adapter changes, composition root, file manifest |
| StageContext[stage-3] | `ai_architect_save_context` | `{findingID, affectedPorts, adapterChanges, compositionRootChanges, fileChangeManifest, adapterContext}` |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 4}` |

## Stop criteria

- **Pass:** All affected ports identified. No circular deps. File change manifest complete. Integration design written. PipelineState.currentStage = 4.
- **Retry:** Circular dependency detected — redesign adapter boundaries. Max 2 retries.
- **Escalate:** Cannot resolve circular dependency after retries. Impact map references engines not found in codebase. Port definitions unreadable.

## Effort level: MED
