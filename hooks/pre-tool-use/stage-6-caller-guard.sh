#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-caller-guard.sh ──────────────────────────────────────────────────
# Fires: Before any tool call in Stage 6
# Enforces: Only the Stage 6 implementation orchestrator may call
#   implementation tools. Worker agents spawned by Stage 6 have a restricted
#   tool allowlist. This prevents scope creep where workers call tools
#   outside their mandate.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-caller-guard — implement before Stage 6 runs"
exit 0
