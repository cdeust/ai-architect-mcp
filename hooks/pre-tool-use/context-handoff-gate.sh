#!/usr/bin/env bash
set -euo pipefail

# ── context-handoff-gate.sh ─────────────────────────────────────────────────
# BLOCKS any ai_architect_save_context call for stage N if the required
# upstream stages have not been loaded via ai_architect_load_context.
#
# Enforces the pipeline's core contract: context flows forward.
# Each stage MUST load its upstream artifacts before writing its own.
#
# Tracked via marker files in {data_dir}/context_loads/.
# ai_architect_load_context writes: loaded_stage_{K}_{findingID}
# This hook checks for required markers before allowing save_context.
# ──────────────────────────────────────────────────────────────────────────────

TOOL_NAME="${TOOL_NAME:-}"
CURRENT_STAGE="${CURRENT_STAGE:-0}"
FINDING_ID="${FINDING_ID:-}"
DATA_DIR="${DATA_DIR:-.pipeline}"

# Only gate save_context calls
if [ "$TOOL_NAME" != "ai_architect_save_context" ]; then
  exit 0
fi

# Stage 0 has no upstream requirements
if [ "$CURRENT_STAGE" -eq 0 ]; then
  exit 0
fi

if [ -z "$FINDING_ID" ]; then
  echo "BLOCK [CONTEXT-HANDOFF]: FINDING_ID not set. Cannot verify context handoff."
  exit 1
fi

MARKER_DIR="$DATA_DIR/context_loads"

# Required upstream stages per current stage (POSIX-compatible, no assoc arrays)
get_required() {
  case "$1" in
    1)  echo "0" ;;
    2)  echo "0 1" ;;
    3)  echo "0 1 2" ;;
    4)  echo "1 2 3" ;;
    5)  echo "4" ;;
    6)  echo "3 4 5" ;;
    7)  echo "6" ;;
    8)  echo "4 7" ;;
    9)  echo "4 8" ;;
    10) echo "2 7 9" ;;
    *)  echo "" ;;
  esac
}

REQUIRED=$(get_required "$CURRENT_STAGE")

if [ -z "$REQUIRED" ]; then
  exit 0
fi

MISSING=""
for stage in $REQUIRED; do
  MARKER="$MARKER_DIR/loaded_stage_${stage}_${FINDING_ID}"
  if [ ! -f "$MARKER" ]; then
    MISSING="$MISSING $stage"
  fi
done

if [ -n "$MISSING" ]; then
  echo "BLOCK [CONTEXT-HANDOFF]: Stage $CURRENT_STAGE attempted save_context"
  echo "  without loading required upstream stages:$MISSING"
  echo "  Call ai_architect_load_context(stage_id=K, finding_id=\"$FINDING_ID\")"
  echo "  for each missing stage before proceeding."
  echo "  This is the pipeline's core contract: context flows forward."
  exit 1
fi

echo "PASS [CONTEXT-HANDOFF]: All required upstream stages loaded for stage $CURRENT_STAGE"
exit 0
