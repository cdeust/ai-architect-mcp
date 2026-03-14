#!/usr/bin/env bash
set -euo pipefail

# ── stage-7-tsan.sh ──────────────────────────────────────────────────────────
# Fires: After test execution tool calls in Stage 7
# Enforces: Thread Sanitizer (TSan) must report zero data races.
#   Any TSan warning is a hard failure. Concurrency bugs are not
#   "warnings to investigate later" — they are blocking defects.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-7-tsan — implement before Stage 7 runs"
exit 0
