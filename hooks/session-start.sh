#!/usr/bin/env bash
set -euo pipefail

# ── session-start.sh ──────────────────────────────────────────────────────────
# Fires at the beginning of every Claude session.
# Responsibilities:
#   1. Load pipeline_state.md if it exists (resume from last session)
#   2. Verify skill-version-manifest.json is present and readable
#   3. Create traces/ directory for this session if it does not exist
#   4. Log session start event
# ──────────────────────────────────────────────────────────────────────────────

SESSION_DATE="$(date +%Y%m%d)"
TRACE_DIR="traces"

# Ensure trace directory exists
mkdir -p "$TRACE_DIR"

# Log session start
echo "{\"t\":\"$(date -u +%s)\",\"event\":\"session_start\",\"date\":\"$SESSION_DATE\"}" \
  >> "$TRACE_DIR/session-$SESSION_DATE.jsonl" 2>/dev/null || true

# Check for pipeline state from previous session
if [ -f "pipeline_state.md" ]; then
  echo "INFO [session-start]: Found pipeline_state.md — resuming from previous session."
else
  echo "INFO [session-start]: No pipeline_state.md found — starting fresh session."
fi

# Verify skill manifest exists
if [ -f "skill-version-manifest.json" ]; then
  echo "INFO [session-start]: skill-version-manifest.json present."
else
  echo "WARN [session-start]: skill-version-manifest.json missing — health check will fail."
fi

exit 0
