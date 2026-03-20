#!/usr/bin/env bash
set -euo pipefail

# ── context-load-marker.sh ──────────────────────────────────────────────────
# After a successful ai_architect_load_context call, writes a marker file
# so the pre-tool-use context-handoff-gate can verify upstream loads.
# ──────────────────────────────────────────────────────────────────────────────

TOOL_NAME="${TOOL_NAME:-}"
TOOL_EXIT_CODE="${TOOL_EXIT_CODE:-1}"
FINDING_ID="${FINDING_ID:-}"
LOADED_STAGE_ID="${LOADED_STAGE_ID:-}"
DATA_DIR="${DATA_DIR:-.pipeline}"

# Only track load_context calls
if [[ "$TOOL_NAME" != "ai_architect_load_context" ]]; then
  exit 0
fi

# Only track successful calls
if [[ "$TOOL_EXIT_CODE" -ne 0 ]]; then
  exit 0
fi

if [[ -z "$FINDING_ID" || -z "$LOADED_STAGE_ID" ]]; then
  exit 0
fi

MARKER_DIR="$DATA_DIR/context_loads"
mkdir -p "$MARKER_DIR"

MARKER="$MARKER_DIR/loaded_stage_${LOADED_STAGE_ID}_${FINDING_ID}"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$MARKER"

echo "PASS [CONTEXT-LOAD-MARKER]: Recorded load of stage $LOADED_STAGE_ID for finding $FINDING_ID"
exit 0
