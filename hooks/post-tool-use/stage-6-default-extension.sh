#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-default-extension.sh ─────────────────────────────────────────────
# Fires: After every file-write tool call in Stage 6
# Enforces: Swift protocol extensions must not provide default
#   implementations that hide missing conformances. Default extensions
#   are a common source of silent failures in Swift and must be explicitly
#   approved per-protocol.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-default-extension — implement before Stage 6 runs"
exit 0
