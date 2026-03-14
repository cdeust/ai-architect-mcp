#!/usr/bin/env bash
set -euo pipefail

# ── post-tool-use.sh ─────────────────────────────────────────────────────────
# Root dispatcher for post-tool-use hooks.
# Runs AFTER every tool call in every stage.
#
# Execution order:
#   1. Stage-specific hooks (dispatched by CURRENT_STAGE)
#   2. Universal audit log (always runs, append-only)
# ──────────────────────────────────────────────────────────────────────────────

CURRENT_STAGE="${CURRENT_STAGE:-0}"
HOOK_DIR="$(dirname "$0")/post-tool-use"

# ── Stage dispatch ────────────────────────────────────────────────────────────
case "$CURRENT_STAGE" in
  6)
    for hook in "$HOOK_DIR"/stage-6-*.sh; do
      [ -f "$hook" ] && bash "$hook"
    done
    ;;
  7)
    for hook in "$HOOK_DIR"/stage-7-*.sh; do
      [ -f "$hook" ] && bash "$hook"
    done
    ;;
  *)
    # No stage-specific post-tool-use hooks for other stages yet
    ;;
esac

# ── Universal audit log (append-only, always runs) ───────────────────────────
mkdir -p traces
echo "{\"t\":\"$(date -u +%s)\",\"tool\":\"${TOOL_NAME:-unknown}\",\"stage\":\"${CURRENT_STAGE:-0}\",\"outcome\":\"${TOOL_OUTCOME:-unknown}\"}" \
  >> "traces/session-$(date +%Y%m%d).jsonl" 2>/dev/null || true

exit 0
