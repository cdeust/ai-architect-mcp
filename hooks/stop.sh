#!/usr/bin/env bash
set -euo pipefail

# ── stop.sh ───────────────────────────────────────────────────────────────────
# Fires at the end of every Claude session.
# Responsibilities:
#   1. Write HandoffDocument with session summary
#   2. Update pipeline_state.md with current state
#   3. Log session end event
#   4. Flush any pending trace events
# ──────────────────────────────────────────────────────────────────────────────

SESSION_DATE="$(date +%Y%m%d)"
TRACE_DIR="traces"

# Log session end
echo "{\"t\":\"$(date -u +%s)\",\"event\":\"session_end\",\"date\":\"$SESSION_DATE\"}" \
  >> "$TRACE_DIR/session-$SESSION_DATE.jsonl" 2>/dev/null || true

echo "INFO [stop]: Session ended. HandoffDocument update delegated to Claude."

exit 0
