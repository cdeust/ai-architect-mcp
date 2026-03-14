#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-manifest-guard.sh ────────────────────────────────────────────────
# Fires: Before any file-write tool call in Stage 6
# Enforces: Every file written must be listed in the implementation manifest.
#   The manifest is generated from the PRD's file list. Any file not in the
#   manifest is rejected — no surprise files, no scope creep.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-manifest-guard — implement before Stage 6 runs"
exit 0
