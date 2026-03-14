#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-human-review-gate.sh ─────────────────────────────────────────────
# Fires: Before Stage 6 begins if human review was requested
# Enforces: If the PRD was flagged for human review during Stage 5,
#   implementation must not begin until a human has approved the PRD.
#   This hook checks for the human_review_required flag in StageContext
#   and blocks if approval has not been recorded.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-human-review-gate — implement before Stage 6 runs"
exit 0
