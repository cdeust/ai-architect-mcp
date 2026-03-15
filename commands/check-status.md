---
name: check-status
description: Check pipeline state — current stage, active finding, retry counts
allowed-tools: Bash, Read, Glob, Grep
---

# Check Status

## Step 1 — Load pipeline state

```
ai_architect_load_session_state(session_id="current")
```

## Step 2 — Report

Display the current pipeline state:
- Current stage (0-10 or "complete")
- Active finding ID
- Retry count
- Context budget usage

```
ai_architect_check_context_budget()
ai_architect_query_audit_events(filter={"type": "stage_transition"}, limit=10)
```

Report the last 10 stage transitions and current position in the pipeline.
