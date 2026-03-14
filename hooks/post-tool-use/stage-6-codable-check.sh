#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-codable-check.sh ─────────────────────────────────────────────────
# Fires: After every Swift file-write tool call in Stage 6
# Enforces: Every Codable struct must have explicit CodingKeys.
#   Implicit CodingKeys cause silent breakage when property names change.
#   This hook scans for Codable conformance and verifies CodingKeys exist.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-codable-check — implement before Stage 6 runs"
exit 0
