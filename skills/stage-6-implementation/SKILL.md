---
name: stage-6-implementation
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-5-review]
postreq-skills: [stage-7-verification]
---

## Allostatic Priming

You are the implementation orchestrator. You break the PRD into file-level tasks, spawn a worker per file, and synthesise. You do not write code yourself — you coordinate workers and verify their integration. Every file produced must trace back to a PRD requirement. Every test must trace back to an acceptance criterion.

## Trigger

USE WHEN: implement, write code, create branch, code generation, build feature, file-level tasks, orchestrator-workers, git branch, task decomposition, worker coordination
NOT FOR: verify — stage 7, PRD review — stage 5, anything pre-implementation

## Survival Question

> "Have all files in the PRD change manifest been implemented by dedicated workers, and does the integrated result compile?"

## Before you start

1. `ai_architect_load_context(stage="stage-5", finding_id="{findingID}")` — load verification report (confirms PRD passed review)
2. `ai_architect_load_context(stage="stage-4", finding_id="{findingID}")` — load PRD files (prd-technical.md for file manifest, prd-tests.md for test specs)
3. `ai_architect_load_context(stage="stage-3", finding_id="{findingID}")` — load integration design (composition root wiring)
4. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 6, check retryCount
5. `ai_architect_list_experience_patterns(category="solution")` — load solution patterns for implementation context

Missing Stage 5 verification report = BLOCK. Cannot implement without reviewed PRD.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-5-verification-report.json` | JSON | StageContext[stage-5] | YES — BLOCK if missing |
| `prd-technical.md` | MD | StageContext[stage-4] | YES — file change manifest |
| `prd-tests.md` | MD | StageContext[stage-4] | YES — test specifications |
| `prd-acceptance.md` | MD | StageContext[stage-4] | YES — acceptance criteria |
| `stage-3-integration-design.md` | MD | StageContext[stage-3] | YES — composition root wiring |
| ExperiencePatterns | list | `ai_architect_list_experience_patterns` | NO — enrichment |

## Operations

### 1. Create implementation branch

```
ai_architect_git_branch(
  branch_name="pipeline/{findingID}",
  base="main"
)
→ All implementation work happens on this branch
→ One branch per finding — strict isolation
```

### 2. Decompose file change manifest

Parse `prd-technical.md` file change manifest. Order by dependency:
1. Port protocols (interfaces first)
2. Domain models
3. Adapters (implementations)
4. Composition root wiring
5. Tests

```
ai_architect_enhance_prompt(
  prompt="Decompose file change manifest from prd-technical.md into ordered implementation tasks",
  strategy="planAndSolve",
  context="{prd_technical + integration_design}"
)
→ Returns ordered list of files to create/modify with dependency ordering
```

### 3. Per-file worker: implement

For each file in the manifest, spawn a worker:

```
For each file in dependency order:

  # Read existing file (if modifying)
  ai_architect_fs_read(path="{file_path}")

  # Select strategy for this file type
  ai_architect_select_strategy(
    task_type="implementation",
    context="implement {file_path} for {AC_refs}"
  )

  # Generate implementation with full context
  ai_architect_enhance_prompt(
    prompt="Implement {file_path} according to PRD spec",
    strategy="{selected_strategy}",
    context="{existing_file + relevant_ACs + experience_patterns + port_definitions}"
  )

  # Write the file
  ai_architect_fs_write(
    path="{file_path}",
    content={generated_code}
  )

  # Commit with traceability
  ai_architect_git_commit(
    message="[{findingID}] stage-6: {filename} — {AC_refs}",
    files=["{file_path}"]
  )
```

### 4. Pre-commit impact check (if codebase intelligence engine available)

If codebase intelligence engine is available, verify multi-file changes before committing:
```
ai_architect_codebase_impact(
  target="{modified_function}",
  direction="downstream",
  repo_path="{target_repo}"
)
→ Traces call chains from modified code to callers
→ Ensures no unexpected downstream breakage
```

### 5. Synthesise and verify integration

After all workers complete:

```
# Verify no import cycles
ai_architect_verify_graph(
  claims=["{all_import_statements}"],
  graph_type="dependency"
)
→ No circular imports allowed

# Verify all protocol conformances present
ai_architect_enhance_prompt(
  prompt="Verify all protocol conformances from integration design are implemented",
  strategy="verifiedReasoning",
  context="{integration_design + implemented_files}"
)

# Verify composition root wiring complete
ai_architect_fs_read(path="{composition_root_file}")
→ All new adapters wired to their ports
```

### 6. Write implementation manifest

```
ai_architect_save_context(
  stage="stage-6",
  finding_id="{findingID}",
  data={
    "findingID": "{findingID}",
    "branch": "pipeline/{findingID}",
    "filesChanged": [
      {
        "path": "{file_path}",
        "changeType": "create|modify",
        "acRefs": ["AC-001", ...],
        "commitSha": "{sha}"
      }
    ],
    "totalFiles": N,
    "totalCommits": M,
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-6-implementation-manifest.json",
  content={implementation manifest JSON}
)
```

### 7. Update pipeline state and audit

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 7,
  "activeFindingID": "{findingID}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 6,
  "outcome": "pass",
  "findingID": "{findingID}",
  "files_changed": N,
  "commits": M,
  "branch": "pipeline/{findingID}"
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-6", checks={
  "all_manifest_files_implemented": true/false,
  "no_circular_package_dependencies": true/false,
  "all_protocol_conformances_complete": true/false,
  "composition_root_wired": true/false,
  "all_commits_on_correct_branch": true/false,
  "stage_5_output_untouched": true/false
})
```

- [ ] All files in manifest implemented?
- [ ] No new circular package dependencies?
- [ ] All protocol conformances complete?
- [ ] Composition root wired correctly?
- [ ] All commits on correct branch (`pipeline/{findingID}`)?
- [ ] Stage 5 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| Code on branch | `pipeline/{findingID}` | Git branch with implementation commits |
| `stage-6-implementation-manifest.json` | `{data_dir}/artifacts/` | `{findingID, branch, filesChanged, totalFiles, totalCommits}` |
| StageContext[stage-6] | `ai_architect_save_context` | Same as manifest |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 7}` |

## Stop criteria

- **Pass:** All manifest files implemented. No import cycles. All conformances present. Composition root wired. PipelineState.currentStage = 7.
- **Retry:** Stage 7 sends back with failure context (HOR rule violations, build failure) — fix specific files and re-commit. Max 3 retries of the 7→6 loop.
- **Escalate:** 3 retries exhausted. Import cycles cannot be resolved. Protocol conformances missing with no clear implementation path.

## Effort level: MAX
