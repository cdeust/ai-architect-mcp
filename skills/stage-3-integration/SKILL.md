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
5. `ai_architect_list_experience_patterns(stage_id=3, min_relevance=0.1)` — load architecture decisions for context

**If `codebase_intelligence: "ai_codebase_intelligence"` in Stage 0 health report:**
6. `ai_architect_codebase_cypher(query="MATCH (a)-[:CodeRelation {type: 'IMPLEMENTS'}]->(b) WHERE b.name IN {affected_ports} RETURN a.name, a.filePath", repo="{target_repo}")` — find existing adapter implementations
7. `ai_architect_codebase_context(name="{affected_port}", include_content=true, repo="{target_repo}")` — for each affected port from impact map

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
  include_content=true,
  repo="{target_repo}"
)
→ Resolve dependency graph for affected symbols

ai_architect_codebase_context(
  name="{port_name}",
  include_content=true,
  repo="{target_repo}"
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

### 1b. Git analytics enrichment (optional)

If git analytics are available (from Stage 0 health report `git_analytics: "available"`):
```
ai_architect_codebase_dead_code(path="{affected_module}", repo="{target_repo}")
→ Identify unreachable code candidates in the affected modules
→ (Grove et al. 1997) — dead code in the integration zone is a cleanup opportunity
→ Add dead code files to the file_change_manifest with change_type: "delete"
→ Do NOT delete code that is only unreachable due to dynamic dispatch or reflection

ai_architect_codebase_cochange(path="{affected_module}", repo="{target_repo}")
→ Detect hidden dependencies not visible in import graphs
→ (Gall et al. 1998) — files with high co-change frequency to affected ports are implicit dependencies
→ If co-change confidence > 0.7 with an affected file: add to affected_ports even if no import edge exists
→ These hidden dependencies must be included in the integration design to prevent silent breakage
```

### 2. Design adapter changes per affected engine

```
ai_architect_enhance_prompt(
  prompt="Design integration blueprint for finding '{findingID}': affected engines={affectedEngines}, affected ports={affected_ports}",
  context="{port_definitions + impact_map + codebase_structure}",
  max_iterations=3
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
  graph_data={
    "nodes": [
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "{package_name}", "node_type": "implementation"}
    ],
    "edges": [
      {"source_id": "{uuid}", "target_id": "{uuid}", "relationship": "depends", "weight": 1.0}
    ]
  }
)
→ Verify: no cycles detected (circular package dependencies)
→ Verify: no contradictions in dependency graph
```

### 4. Map composition root wiring

Identify factory files requiring update. No new package-level dependencies unless justified with a rationale documented in the integration design.

### 5. Write integration design to StageContext

```
ai_architect_save_context(
  stage_id=3,
  finding_id="{findingID}",
  artifact={
    "finding_id": "{findingID}",
    "affected_ports": [...],
    "adapter_changes": [
      {
        "engine": "{engine_name}",
        "port": "{port_protocol}",
        "adapter_file": "{file_path}",
        "change_type": "modify|create",
        "new_methods": [...]
      }
    ],
    "composition_root_changes": [...],
    "file_change_manifest": [...],
    "adapter_context": "xcode|localfs|mixed",
    "no_circular_deps": true,
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
ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 4,
  "status": "running",
  "completed_stages": [0, 1, 2, 3]
})

ai_architect_append_audit_event(event_data={
  "event_id": "stage-3-complete-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 3,
  "tool_name": "stage-3-integration",
  "outcome": "pass",
  "message": "Stage 3 integration design completed for finding {findingID}",
  "metadata": {"affected_ports_count": "{N}", "adapter_changes_count": "{M}"}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage_id=3, phase="observe", decision="All affected ports identified: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=3, phase="observe", decision="No circular package dependencies: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=3, phase="observe", decision="Adapter context decided: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=3, phase="observe", decision="File change manifest complete: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=3, phase="decide", decision="Integration design marked read-only: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=3, phase="decide", decision="Stage 2 output untouched: {true/false}", confidence=1.0, session_id="{sessionID}")
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
