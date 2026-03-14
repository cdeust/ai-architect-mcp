#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-domain-purity.sh ─────────────────────────────────────────────────
# Fires: After every file-write tool call in Stage 6
# Enforces: Source files must not import concrete adapters directly.
#   Domain logic must depend only on port interfaces. This check scans
#   the written file for imports of adapter modules and blocks if found.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-domain-purity — implement before Stage 6 runs"
exit 0
