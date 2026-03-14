#!/usr/bin/env bash
set -euo pipefail

# ── pre-tool-use.sh ──────────────────────────────────────────────────────────
# Root dispatcher for pre-tool-use hooks.
# Runs BEFORE every tool call in every stage.
#
# Execution order:
#   1. MANDATORY .env protection (runs first, always, no bypass)
#   2. Stage-specific hooks (dispatched by CURRENT_STAGE)
# ──────────────────────────────────────────────────────────────────────────────

# ── MANDATORY: .env protection ────────────────────────────────────────────────
# This check runs on EVERY tool call in EVERY stage. No bypass.
ENV_PATTERNS=(
  "\.env$"
  "\.env\."
  "\.env\.local"
  "\.env\.production"
  "\.env\.staging"
  "secrets/"
  "credentials/"
  "\.pem$"
  "\.key$"
)

TOOL_INPUT="${TOOL_INPUT_PATH:-}"
TOOL_CMD="${TOOL_COMMAND:-}"
TOOL_CONTENT="${TOOL_INPUT_CONTENT:-}"

for pattern in "${ENV_PATTERNS[@]}"; do
  if echo "$TOOL_INPUT" | grep -qE "$pattern"; then
    echo "BLOCK [SECURITY-ENV]: Attempted access to protected path: $TOOL_INPUT"
    echo "  .env files and credential files are never read by this pipeline."
    echo "  Use environment variables set before session start instead."
    exit 1
  fi
  if echo "$TOOL_CMD" | grep -qE "cat|read|open|source" && \
     echo "$TOOL_CMD" | grep -qE "$pattern"; then
    echo "BLOCK [SECURITY-ENV]: Attempted .env read via command: $TOOL_CMD"
    exit 1
  fi
done

# Block cat/read of any file containing 'secret', 'credential', 'token', 'password'
# in its path (outside of docs/ which may discuss these conceptually)
if echo "$TOOL_CMD" | grep -qE "^(cat|head|tail|less|more|read|source)\s"; then
  if echo "$TOOL_INPUT" | grep -qiE "secret|credential|password|token|api.key" && \
     ! echo "$TOOL_INPUT" | grep -q "docs/"; then
    echo "BLOCK [SECURITY-SECRET]: Attempted read of likely secret file: $TOOL_INPUT"
    exit 1
  fi
fi
# ── END MANDATORY .env protection ─────────────────────────────────────────────

# ── Stage dispatch ────────────────────────────────────────────────────────────
CURRENT_STAGE="${CURRENT_STAGE:-0}"
HOOK_DIR="$(dirname "$0")/pre-tool-use"

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
    # No stage-specific pre-tool-use hooks for other stages yet
    ;;
esac

exit 0
