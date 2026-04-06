---
name: stage-4-prd
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-3-integration]
postreq-skills: [stage-4-5-interview]
---

## Allostatic Priming

You are a senior product engineer writing a machine-verifiable specification contract. Every claim must be traceable. Every requirement must have an acceptance criterion. Every test must have an implementation body. You do not guess intent — you surface it first through clarification, then generate against the contract. The PRD is not documentation — it is the contract that Stage 6 implements against and Stage 7 verifies against.

## Trigger

USE WHEN: generate PRD, write specification, PRD generation, create requirements, build spec, prd-generator, clarification questions, 9-file package, specification contract
NOT FOR: PRD review — that is stage 5, implementation — stage 6, plan interview — stage 4.5

## Survival Question

> "Does this PRD package form a complete, acyclic traceability graph with no orphan IDs and compound score ≥ 0.85?"

## Before you start

**MANDATORY: Load ALL upstream artifacts. Do NOT proceed without them.**

1. `ai_architect_load_context(stage_id=1, finding_id="{findingID}")` — load Stage 1 findings (finding details, relevance scores, source material, codebase matches)
2. `ai_architect_load_context(stage_id=2, finding_id="{findingID}")` — load Stage 2 impact map (compound score, propagation paths, affected engines, cascade points)
3. `ai_architect_load_context(stage_id=3, finding_id="{findingID}")` — load Stage 3 integration design (affected ports, adapter changes, file manifest, architecture decisions)
4. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 4, check retryCount
5. `ai_architect_list_experience_patterns(stage_id=4, min_relevance=0.1)` — load solution patterns for PRD enrichment
6. `ai_architect_query_context(finding_id="{findingID}", query="PRDExample records for findingType={finding_type}")` — load few-shot examples

**MANDATORY: Load codebase intelligence (if available from Stage 0 health report).**

7. `ai_architect_codebase_query(query="{finding_keywords}", repo="{target_repo}")` — execution flows related to the finding
8. `ai_architect_codebase_context(name="{primary_affected_symbol}", include_content=true, repo="{target_repo}")` — full source code + callers + callees of the primary symbol being changed
9. `ai_architect_codebase_context(name="{caller_symbol}", include_content=true, repo="{target_repo}")` — for each direct caller identified in Stage 2

**All loaded data forms `upstream_context` — this is the input to PRD generation. Not optional. Not skippable.**

Missing Stage 3 integration design = BLOCK. Cannot generate PRD without integration blueprint.
Missing Stage 1 or Stage 2 = BLOCK. PRD requires finding details and impact analysis.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-3-integration-design.md` | MD | StageContext[stage-3] | YES — BLOCK if missing |
| `stage-2-impact-map.json` | JSON | StageContext[stage-2] | YES — for scope context |
| `stage-1-findings.json` | JSON | StageContext[stage-1] | YES — for finding details |
| ExperiencePatterns | list | `ai_architect_list_experience_patterns` | NO — enrichment only |
| PRDExample records | list | StageContext query | NO — few-shot seed |
| ClarificationReport | MD | StageContext[stage-4] | NO on first run, YES on retry (permanent, reused) |

## Cortex memory integration

### Before PRD generation — recall past PRDs and architectural decisions

**WHEN:** After loading all upstream artifacts (steps 1-9 of "Before you start") and before operations begin.
**WHY:** Past PRDs for this repo established architectural patterns, naming conventions, and design decisions. A new PRD that contradicts an established pattern without justification creates inconsistency. Past PRD failures (score < 0.85, orphan IDs, graph cycles) indicate pitfalls to avoid.
**HOW:**

```
cortex:recall(query="PRD generation architectural decisions patterns for repo {target_repo}", limit=15)
cortex:recall(query="PRD failures retry orphan IDs graph cycles for repo {target_repo}", limit=10)
```

If results are returned:
- Check for established architectural patterns (port/adapter boundaries, module naming, dependency directions) — the new PRD must not contradict them without explicit justification in the PRD overview
- Check for past PRD failures — if a specific HOR rule or graph violation caused retries in past runs, proactively address it during generation (e.g., ensure traceability IDs are complete before running HOR rules)
- Check for naming conventions and module organization established by prior PRDs — maintain consistency
- Feed relevant recalled decisions into the enhanced prompt (step 5) as additional context

### After PRD generation — store key architectural decisions

**WHEN:** After the PRD passes verification (compound score >= 0.85) and before updating pipeline state.
**WHY:** The architectural decisions made in this PRD become constraints for future PRDs. Storing them ensures consistency across pipeline runs.
**HOW:**

```
cortex:remember(
  content="PRD for finding {findingID} in repo {target_repo}: architecture={key_architecture_decisions}, new_ports={new_port_interfaces}, affected_modules={module_list}, compound_score={score}, retry_count={retries}, patterns_established={new_patterns}",
  tags=["prd", "repo:{target_repo_name}", "finding:{findingID}", "stage:4"]
)
```

What to store:
- Key architectural decisions (new ports defined, adapter changes, module splits)
- Which HOR rules were close to failing — these are fragile areas for future PRDs
- The compound score and retry count — tracks PRD quality trends over time
- Any new patterns established (naming conventions, interface shapes, dependency structures)

## Operations

### 1. Load few-shot examples (zero API cost via Foundation Models)

```
ai_architect_query_context(
  finding_id="{findingID}",
  query="PRDExample records matching findingType={finding_type}, sorted by compoundScore desc, limit 2"
)
→ Top-2 matches loaded as structural examples for PRD generation
→ These are prior successful PRDs with score ≥ 0.85
```

### 2. Generate clarification questions (skip on retry)

**Only on first run (retryCount = 0).** ClarificationReport is permanent — never re-generated on retry.

```
ai_architect_enhance_prompt(
  prompt="Generate clarification questions for gaps in IntegrationDesign not derivable from StageContext",
  context="{integration_design + impact_map + findings}",
  max_iterations=3
)
→ Returns questions targeting genuinely open gaps
```

Pre-filter against existing context:
```
ai_architect_query_context(
  finding_id="{findingID}",
  query="answers already provided in stages 1-3 for finding {findingID}"
)
→ Discard questions already answered by upstream stages
→ Surface only genuinely open questions
```

### 3. Human gate or auto-answer

**Interactive mode (Mac app / Claude Code):** Present clarification questions to user. Wait for responses.

**Headless mode (GitHub Actions):** Foundation Models auto-answers clarification questions using upstream StageContext.

### 4. Write ClarificationReport (permanent)

```
ai_architect_save_context(
  stage_id=4,
  finding_id="{findingID}-clarification",
  artifact={
    "finding_id": "{findingID}",
    "questions": [...],
    "answers": [...],
    "mode": "interactive|headless",
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-4-clarification-report.md",
  content={clarification report markdown}
)
```

### 5. Build enhanced prompt with full context

```
ai_architect_select_strategy(
  project_type="prd_generation",
  complexity="high",
  characteristics=["traceability", "9_file_package", "acceptance_criteria", "verification"]
)

ai_architect_enhance_prompt(
  prompt="Generate PRD for finding '{findingID}'",
  context="{integration_design + clarification_report + experience_patterns + prd_examples}",
  max_iterations=5
)
→ Returns enhanced prompt with ExperiencePatterns + PRD examples + ClarificationReport
```

### 6. Delegate to ai-prd-generator plugin WITH full upstream context

**CRITICAL: The PRD generator MUST receive all upstream context as its input argument.** Do NOT invoke the skill with a generic description. Serialize the actual data.

Build the PRD generator input from upstream_context:

```
prd_input = {
  "context_type": "feature",
  "finding": upstream_context.stage_1_findings,
  "impact_analysis": upstream_context.stage_2_impact,
  "integration_design": upstream_context.stage_3_integration,
  "codebase_intelligence": {
    "source": "ai_codebase_intelligence",
    "primary_symbol": {codebase intelligence symbol context with source code},
    "callers": {codebase intelligence caller contexts with source code},
    "execution_flows": {codebase intelligence query results},
    "affected_files": upstream_context.stage_3_integration.fileChangeManifest
  },
  "clarification_report": {from step 4 above},
  "enhanced_prompt": {from step 5 above}
}
```

Invoke the PRD generator skill with this serialized context as the args:

```
Skill("ai-prd-generator:generate-prd", args=JSON.stringify(prd_input))
```

The plugin handles:
- PRD context detection (8 types) — pre-set to "feature" from pipeline
- Section-by-section generation with verification
- 64 hard output rules enforcement
- 9-file automated export to `{data_dir}/prd/`

**The plugin MUST use the codebase intelligence data:**
- `primary_symbol` source code → Technical Specification code examples must reference real code
- `callers` → Impact section must list actual callers, not guesses
- `execution_flows` → Architecture section must show real dependency chains
- `affected_files` → File change manifest from Stage 3, not invented

The plugin writes to `{data_dir}/prd/`:
- `prd-overview.md`
- `prd-requirements.md`
- `prd-user-stories.md`
- `prd-technical.md`
- `prd-acceptance.md`
- `prd-roadmap.md`
- `prd-jira.md`
- `prd-tests.md`
- `prd-verification.md`

Max 25 turns for generation.

### 7. Run HOR rules on generated PRD

```
ai_architect_run_hor_rules(
  artifact={concatenated PRD content as dict},
  base_score=1.0
)
→ All 64 pure functions evaluate the PRD
→ Returns per-rule pass/fail + adjusted score
```

### 8. Run verification algorithms on PRD

```
ai_architect_verify_claim(
  content="{prd_claim_text}",
  claim_type="atomic_fact",
  context="{prd_content}",
  priority=80
)

ai_architect_verify_graph(
  graph_data={
    "nodes": [
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "FR-001", "node_type": "requirement"},
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "AC-001", "node_type": "test"},
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "STORY-001", "node_type": "specification"}
    ],
    "edges": [
      {"source_id": "{FR_uuid}", "target_id": "{AC_uuid}", "relationship": "tests", "weight": 1.0},
      {"source_id": "{STORY_uuid}", "target_id": "{FR_uuid}", "relationship": "requires", "weight": 1.0}
    ]
  }
)
→ Verify acyclic traceability graph, no orphan IDs, no contradictions

ai_architect_evaluate_nli(
  claim_content="{acceptance_criterion_text}",
  premise="{requirement_text}",
  strict=true
)
→ NLI entailment check: does each AC entail its FR?
```

### 9. Compute compound score

```
ai_architect_compound_score(
  relevance={hor_adjusted_score_from_step_7},
  uniqueness={graph_verification_score_from_step_8},
  impact={chain_of_verification_score_from_step_8},
  confidence={nli_entailment_score_from_step_8},
  weights={
    "relevance": 0.35,
    "uniqueness": 0.15,
    "impact": 0.30,
    "confidence": 0.20
  }
)
→ Compound score 0.0–1.0
```

### 10. Evaluator-optimizer loop

If compound score < 0.85:
```
→ Inject failed rules + failure context into prompt
→ Return to step 5 (reuse ClarificationReport — do NOT re-run clarification)
→ Max 3 retries

ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 4,
  "status": "running",
  "completed_stages": [0, 1, 2, 3],
  "metadata": {"retry_count": "{current + 1}", "retry_reason": "compound_score_below_threshold"}
})
```

If compound score ≥ 0.85:
```
ai_architect_save_context(
  stage_id=4,
  finding_id="{findingID}",
  artifact={
    "prd_files": [...],
    "compound_score": {score},
    "hor_results": {...},
    "verification_results": {...}
  }
)

ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{findingID}",
  "current_stage": 5,
  "status": "running",
  "completed_stages": [0, 1, 2, 3, 4],
  "metadata": {"next_sub_stage": "interview_4.5"}
})

ai_architect_append_audit_event(event_data={
  "event_id": "stage-4-complete-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 4,
  "tool_name": "stage-4-prd",
  "outcome": "pass",
  "message": "Stage 4 PRD generation completed for finding {findingID}",
  "metadata": {"compound_score": "{score}", "retry_count": "{total_retries}"}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="ClarificationReport written before generation: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="All 9 PRD files present: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="Compound score >= 0.85: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="No orphan IDs: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="Dependency graph acyclic: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="NEEDS-RUNTIME flags present: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="observe", decision="HUMAN REVIEW REQUIRED section present: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=4, phase="decide", decision="Stage 3 output untouched: {true/false}", confidence=1.0, session_id="{sessionID}")
```

- [ ] ClarificationReport written before generation starts?
- [ ] All 9 PRD files present?
- [ ] Compound score ≥ 0.85?
- [ ] No orphan FR/AC/UT/STORY IDs?
- [ ] Dependency graph acyclic?
- [ ] NEEDS-RUNTIME flags present (100% PASS is a violation)?
- [ ] HUMAN REVIEW REQUIRED section present?
- [ ] Stage 3 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| 9 PRD files | `{data_dir}/prd/` | `prd-overview.md`, `prd-requirements.md`, `prd-user-stories.md`, `prd-technical.md`, `prd-acceptance.md`, `prd-roadmap.md`, `prd-jira.md`, `prd-tests.md`, `prd-verification.md` |
| `stage-4-clarification-report.md` | `{data_dir}/artifacts/` | `{questions, answers, mode, timestamp}` |
| StageContext[stage-4] | `ai_architect_save_context` | `{prdFiles, compoundScore, horResults, verificationResults}` |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 4.5}` |

## Stop criteria

- **Pass:** All 9 PRD files generated. Compound score ≥ 0.85. No orphan IDs. Acyclic traceability graph. NEEDS-RUNTIME verdicts present. PipelineState.currentStage = 4.5.
- **Retry:** Compound score < 0.85 — inject failed rules, regenerate from step 5 (reuse ClarificationReport). Max 3 retries.
- **Escalate:** 3 retries exhausted with score still < 0.85. ai-prd-generator plugin unreachable. ClarificationReport cannot be written. Orphan IDs persist after retry.

## Effort level: MAX
