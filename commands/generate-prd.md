---
name: generate-prd
description: Generate a 9-file PRD package with verification and traceability
allowed-tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
argument-hint: "[feature-description]"
---

# Generate PRD

## Step 1 — Load Stage 4 skill

Read the PRD generation skill:

```
Read skills/stage-4-prd/SKILL.md
```

This defines the full PRD generation workflow including clarification, generation via ai-prd-generator, HOR verification, and evaluator-optimizer retry loop.

## Step 2 — Verify MCP tools

Call the MCP server to verify connectivity:

```
ai_architect_select_strategy(task_type="prd_generation", context="generate PRD")
```

## Step 3 — Execute

Follow the Stage 4 SKILL.md instructions:

1. Load few-shot examples from prior successful PRDs
2. Generate clarification questions for open gaps
3. Run clarification loop until user says "proceed"
4. Build enhanced prompt with selected strategy
5. Delegate to ai-prd-generator plugin for 9-file generation
6. Run 64 HOR rules on generated PRD
7. Run verification algorithms (CoV, Graph, NLI)
8. If compound score < 0.85: inject failures and retry (max 3)

If `$ARGUMENTS` is provided, use it as the feature description. Otherwise, ask for requirements.

## Output

Nine files in the current directory:
- `prd-overview.md` — Executive summary
- `prd-requirements.md` — Functional and non-functional requirements
- `prd-user-stories.md` — User stories with acceptance criteria
- `prd-technical.md` — Technical specification
- `prd-acceptance.md` — Acceptance criteria
- `prd-roadmap.md` — Implementation roadmap
- `prd-jira.md` — JIRA tickets
- `prd-tests.md` — Test cases
- `prd-verification.md` — Verification report
