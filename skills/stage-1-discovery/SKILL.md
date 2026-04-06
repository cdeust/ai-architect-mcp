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

1. `ai_architect_load_context(stage_id=0, finding_id="{findingID}")` — verify Stage 0 health report exists and all checks passed
2. `ai_architect_load_session_state(session_id="{sessionID}")` — confirm currentStage = 1
3. `ai_architect_list_experience_patterns(stage_id=1, min_relevance=0.1)` — load non-decayed patterns for relevance enrichment
4. `ai_architect_query_context(finding_id="{findingID}", query="active findings queue")` — load existing findings to prevent duplicates

Missing Stage 0 health report = BLOCK. Do not discover without a green health check.

## Input contract

| Field | Type | Source | Required |
|-------|------|--------|----------|
| `stage-0-health-report.json` | JSON | StageContext[stage-0] | YES — BLOCK if missing |
| Source material | YAML/MD/URL/PDF | User-provided or scheduled | YES — at least one source |
| Active findings queue | list | StageContext | NO — empty on first run |
| ExperiencePatterns | list | `ai_architect_list_experience_patterns` | NO — enrichment only |

## Cortex memory integration

### Before generating findings — recall past discoveries

**WHEN:** After loading prerequisites (step 4 of "Before you start") and before source ingestion.
**WHY:** Previous pipeline runs may have already discovered findings for this repo. Some may have been resolved (shipped via PR), some may still be open, and some may have been rejected as irrelevant. Rediscovering resolved findings wastes pipeline capacity. Rediscovering rejected findings repeats a known dead end.
**HOW:**

```
cortex:recall(query="discovery findings for repo {target_repo}", limit=15)
cortex:recall(query="rejected findings low relevance for repo {target_repo}", limit=10)
```

If results are returned:
- Cross-reference recalled findings with the current active findings queue (from step 4)
- If a recalled finding was already shipped (PR merged), mark it as resolved — do not resurface
- If a recalled finding was rejected (relevance < 0.6 after retry), check if new source material changes the relevance — only resurface if new evidence exists
- If a recalled finding is still open and in the active queue, skip it during deduplication (step 4 of Operations)
- Include recalled finding IDs in the deduplication check to avoid redundant work

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
ai_architect_codebase_query(query="{finding_keywords}", repo="{target_repo}")
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
  project_type="discovery",
  complexity="medium",
  characteristics=["relevance_scoring", "source_scanning", "deduplication"]
)
→ Returns recommended strategy (graphOfThoughts for exploratory, verifiedReasoning for constrained)
```

### 3. Score each finding for relevance

For each ingested finding, Claude scores using the selected strategy:

```
ai_architect_enhance_prompt(
  prompt="Score this finding for relevance: {finding_summary}",
  context="{codebase_context + existing_findings}",
  max_iterations=3
)
→ Claude evaluates: relevance to codebase, novelty vs existing findings, compound impact potential
→ Assigns relevance score 0.0–1.0
```

### 4. Structural verification and deduplication

Build a claim relationship graph from ingested findings to detect duplicates and contradictions:

```
ai_architect_verify_graph(
  graph_data={
    "nodes": [
      {"node_id": "{uuid}", "claim_id": "{uuid}", "label": "{finding_summary}", "node_type": "requirement"}
    ],
    "edges": [
      {"source_id": "{uuid}", "target_id": "{uuid}", "relationship": "implies", "weight": 0.9}
    ]
  }
)
→ Detects cycles, contradictions, and orphans
→ Use contradiction edges to identify duplicate/overlapping findings
→ Rank remaining findings by relevance score
→ Filter below 0.6 threshold
```

### 5. Write findings to StageContext

```
ai_architect_save_context(
  stage_id=1,
  finding_id="{findingID}",
  artifact={
    "findings": [
      {
        "id": "{findingID}",
        "source": "{source_file}",
        "category": "{source_category}",
        "relevance_score": 0.0-1.0,
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
ai_architect_save_session_state(state_data={
  "session_id": "{sessionID}",
  "finding_id": "{top_finding_id}",
  "current_stage": 2,
  "status": "running",
  "completed_stages": [0, 1]
})

ai_architect_append_audit_event(event_data={
  "event_id": "stage-1-complete-{findingID}",
  "session_id": "{sessionID}",
  "stage_id": 1,
  "tool_name": "stage-1-discovery",
  "outcome": "pass",
  "message": "Stage 1 discovery completed: {N} findings, {M} above threshold",
  "metadata": {"findings_count": "{N}", "above_threshold": "{M}"}
})
```

## OODA Checkpoint

```
ai_architect_emit_ooda_checkpoint(stage_id=1, phase="observe", decision="At least one finding above 0.6: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=1, phase="observe", decision="No duplicates in active queue: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=1, phase="observe", decision="All source adapters returned or failed: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=1, phase="observe", decision="Findings written to StageContext: {true/false}", confidence=1.0, session_id="{sessionID}")
ai_architect_emit_ooda_checkpoint(stage_id=1, phase="decide", decision="Stage 0 output untouched: {true/false}", confidence=1.0, session_id="{sessionID}")
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
