#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-sendable-compile.sh ──────────────────────────────────────────────
# Fires: After every Swift file-write tool call in Stage 6
# Enforces: Types used across concurrency boundaries must conform to
#   Sendable. This hook checks for @Sendable annotations and Sendable
#   conformance on types that cross actor boundaries.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-sendable-compile — implement before Stage 6 runs"
exit 0
