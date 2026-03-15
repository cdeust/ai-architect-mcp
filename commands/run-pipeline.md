---
name: run-pipeline
description: Run the full 11-stage autonomous pipeline — findings to pull requests
allowed-tools: Bash, Read, Write, Glob, Grep, WebFetch, WebSearch
argument-hint: "[finding-source-path-or-description]"
---

# Run Pipeline

## Step 1 — Load the orchestrator skill

Read the orchestrator skill instructions:

```
Read skills/orchestrator/SKILL.md
```

This file defines the full 11-stage pipeline: health check, discovery, impact analysis, integration design, PRD generation, plan interview, PRD review, implementation, verification, benchmark, deployment, and pull request creation.

## Step 2 — Verify MCP server

Call the MCP tools to verify the server is running:

```
ai_architect_check_context_budget()
ai_architect_load_session_state(session_id="current")
```

If the MCP server is not reachable, ensure the plugin is installed:
```bash
pip install -e mcp/
```

## Step 3 — Execute

Follow the orchestrator SKILL.md instructions exactly:

1. Validate blueprint signoff
2. Check skill versions
3. Load findings queue
4. Chain stages 0→10 per finding
5. Manage retry loops (Stage 5→4, Stage 7→6)
6. Write audit trail at every transition

If `$ARGUMENTS` is provided, use it as the source for Stage 1 discovery. Otherwise, scan `sources/` directory.
