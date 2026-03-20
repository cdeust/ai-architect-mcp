---
name: stage-1-discovery
version: "1.0"
last-updated: "2026-03"
status: active
prereq-skills: [stage-0-health]
postreq-skills: [stage-2-impact]
---

## Allostatic Priming

You are a research analyst scanning source categories for signals worth building against. You score for relevance and uniqueness. You do not generate solutions — you surface problems worth solving. Source material may be in any format. Every finding must earn a relevance score ≥ 0.6 to proceed.

## Trigger

USE WHEN: discovery, scan sources, find findings, research, what should we build, source scan, relevance scoring, new findings, signal detection
NOT FOR: impact analysis, integration design, PRD generation, implementation, verification — those are other stages

## Survival Question

> "Have I found at least one finding with a relevance score ≥ 0.6 that is not already in the active findings queue?"

## Before you start

1. `ai_architect_load_context(stage="stage-0", finding_id="{findingID}")` — verify Stage 0 health report exists and all checks passed
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 1
3. `ai_architect_list_experience_patterns(category="pattern")` — load non-decayed patterns for relevance enrichment
4. `ai_architect_query_context(query="active findings queue")` — load existing findings to prevent duplicates

Missing Stage 0 health report = BLOCK. Do not discover without a green health check.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-0-health-report.json` | JSON | StageContext[stage-0] | YES — BLOCK if missing |
| Source material | YAML/MD/URL/PDF | User-provided or scheduled | YES — at least one source |
| Active findings queue | list | StageContext | NO — empty on first run |
| ExperiencePatterns | list | `ai_architect_list_experience_patterns` | NO — enrichment only |

## Operations

### 1. Source ingestion (parallel fan-out)

Read source material through filesystem adapter. Accept source paths as input or scan repo root for recognized formats:

```
ai_architect_fs_list(path=".")
→ For each source file:
  ai_architect_fs_read(path="{filename}")
  → Route by extension:
    .yaml/.yml → YAML parser (TechnicalVeil or generic YAML findings)
    .md → Markdown ingestion
    .pdf → PDF ingestion
    .url → URL fetch ingestion
```

If codebase intelligence engine is available (from Stage 0 health report `codebase_intelligence: "ai_codebase_intelligence"`):
```
ai_architect_codebase_query(query="{finding_keywords}", repo_path="{target_repo}")
→ Symbol and pattern discovery across the codebase
→ Enriches findings with structural context
```

Six adapter types (CombinedIngestionAdapter routes automatically):
- `TechnicalVeilIngestionAdapter` — YAML format (TechnicalVeil schema)
- `YAMLFindingsAdapter` — generic YAML findings
- `GenericMarkdownIngestionAdapter` — markdown folder ingestion
- `URLIngestionAdapter` — URL fetch, web content
- `PDFIngestionAdapter` — PDF document ingestion
- `CombinedIngestionAdapter` — routes to appropriate adapter by source type

### 2. Strategy selection for scoring

```
ai_architect_select_strategy(
  task_type="discovery",
  context="scoring findings for relevance to codebase"
)
→ Returns recommended strategy (graphOfThoughts for exploratory, verifiedReasoning for constrained)
```

### 3. Score each finding for relevance

For each ingested finding, Claude scores using the selected strategy:

```
ai_architect_enhance_prompt(
  prompt="Score this finding for relevance: {finding_summary}",
  strategy="{selected_strategy}",
  context="{codebase_context + existing_findings}"
)
→ Claude evaluates: relevance to codebase, novelty vs existing findings, compound impact potential
→ Assigns relevance score 0.0–1.0
```

### 4. Structural verification and deduplication

```
ai_architect_verify_graph(
  claims=["{finding_1}", "{finding_2}", ...],
  graph_type="dependency"
)
→ Deduplicate findings with >80% semantic overlap
→ Rank by relevance score
→ Filter below 0.6 threshold
```

### 5. Write findings to StageContext

```
ai_architect_save_context(
  stage="stage-1",
  finding_id="{findingID}",
  data={
    "findings": [
      {
        "id": "{findingID}",
        "source": "{source_file}",
        "category": "{source_category}",
        "relevanceScore": 0.0-1.0,
        "summary": "{finding_summary}",
        "status": "new"
      }
    ],
    "sources_processed": N,
    "findings_above_threshold": M,
    "timestamp": "{ISO8601}"
  }
)

ai_architect_fs_write(
  path="{data_dir}/artifacts/stage-1-findings.json",
  content={findings JSON}
)
```

### 6. Update pipeline state and audit

```
ai_architect_save_session_state(session_id="{sessionID}", state={
  "currentStage": 2,
  "activeFindingID": "{top_finding_id}",
  "retryCount": 0
})

ai_architect_append_audit_event(event={
  "type": "stage_complete",
  "stage": 1,
  "outcome": "pass",
  "findingID": "{findingID}",
  "findings_count": N,
  "above_threshold": M
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage="stage-1", checks={
  "at_least_one_finding_above_0.6": true/false,
  "no_duplicates_in_active_queue": true/false,
  "all_source_adapters_returned_or_failed": true/false,
  "findings_written_to_stage_context": true/false,
  "stage_0_output_untouched": true/false
})
```

- [ ] At least one finding with relevance score ≥ 0.6?
- [ ] No finding duplicates existing active queue?
- [ ] All source adapters returned or explicitly failed?
- [ ] FindingList written to StageContext?
- [ ] Stage 0 output untouched (read-only)?

## Expected output

| Artifact | Location | Schema |
|----------|----------|--------|
| `stage-1-findings.json` | `{data_dir}/artifacts/` | `{findings: [{id, source, category, relevanceScore, summary, status}], sources_processed, findings_above_threshold}` |
| StageContext[stage-1] | `ai_architect_save_context` | Same as findings JSON |
| PipelineState update | `ai_architect_save_session_state` | `{currentStage: 2, activeFindingID: "{top_finding}"}` |

## Stop criteria

- **Pass:** At least one finding with relevance ≥ 0.6. Findings written to StageContext. No duplicates. PipelineState.currentStage = 2.
- **Retry:** All findings below 0.6 threshold — expand source categories or lower threshold to 0.5 (max 1 retry with relaxed threshold). If still zero: escalate.
- **Escalate:** Zero findings after retry. All source adapters failed. No source material provided.

## Effort level: MED
