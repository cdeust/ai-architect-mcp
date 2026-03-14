#!/usr/bin/env bash
set -euo pipefail

# ── stage-6-tdd.sh ───────────────────────────────────────────────────────────
# Fires: Before any file-write tool call in Stage 6
# Enforces: Test file must exist before implementation file is written.
#   TDD is not optional. The test is written first. The implementation is
#   written to make the test pass. This hook blocks any Write tool call
#   for a source file if the corresponding test file does not already exist.
# ──────────────────────────────────────────────────────────────────────────────

echo "STUB: stage-6-tdd — implement before Stage 6 runs"
exit 0
