#!/usr/bin/env bash
set -euo pipefail

# ── verify-all.sh ────────────────────────────────────────────────────────────
# Orchestrator script that runs all verification scripts in sequence.
# Any failure in a sub-script fails the entire verification.
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FAILED=0

echo "═══════════════════════════════════════════════════════════"
echo " AI Architect — Full Verification Suite"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 1. Security verification (always runs first)
echo "── verify-security.sh ──────────────────────────────────────"
if bash "$SCRIPT_DIR/verify-security.sh"; then
  echo "PASS: Security verification"
else
  echo "FAIL: Security verification"
  FAILED=1
fi
echo ""

# 2. Python verification (mypy, ruff, pytest)
echo "── verify-python.sh ────────────────────────────────────────"
if bash "$SCRIPT_DIR/verify-python.sh"; then
  echo "PASS: Python verification"
else
  echo "FAIL: Python verification"
  FAILED=1
fi
echo ""

# 3. Swift layer verification (when app/ is implemented)
echo "── verify-swift-layer.sh ───────────────────────────────────"
if bash "$SCRIPT_DIR/verify-swift-layer.sh"; then
  echo "PASS: Swift layer verification"
else
  echo "FAIL: Swift layer verification"
  FAILED=1
fi
echo ""

echo "═══════════════════════════════════════════════════════════"
if [ "$FAILED" -eq 0 ]; then
  echo " All verifications passed."
else
  echo " One or more verifications failed."
  exit 1
fi
