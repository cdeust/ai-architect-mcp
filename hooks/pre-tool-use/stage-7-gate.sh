#!/usr/bin/env bash
set -euo pipefail

# ── stage-7-gate.sh ──────────────────────────────────────────────────────────
# Fires: Before any tool call in Stage 7
# Enforces: Only deterministic tools are allowed in Stage 7. No LLM calls.
#   Stage 7 runs 64 HOR rules, structural checks, and build gates — all of
#   which must produce binary pass/fail results without interpretation.
#   Any tool call not on the Stage 7 allowlist is blocked.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-7-gate — implement before Stage 7 runs"
exit 0
