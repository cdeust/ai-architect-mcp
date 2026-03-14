#!/usr/bin/env bash
set -euo pipefail

# ── verify-security.sh ───────────────────────────────────────────────────────
# Security verification script. Runs on every commit attempt.
# This is NOT a stub — it must be functional from day one.
#
# Checks:
#   1. Scan .py and .sh files for hardcoded secret patterns
#   2. Verify no .env files exist outside .gitignore
#   3. Verify .gitignore contains .env entry
#   4. Warn on direct os.environ.get usage without typed wrapper
# ──────────────────────────────────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAILED=0
WARNINGS=0

echo "Security scan: $REPO_ROOT"
echo ""

# ── Check 1: Scan for hardcoded secret patterns ─────────────────────────────
echo "── Check 1: Hardcoded secret patterns ──"

SECRET_PATTERNS=(
  'sk-ant-[A-Za-z0-9]{20,}'
  'AIza[A-Za-z0-9_-]{35}'
  'AKIA[A-Z0-9]{16}'
  'ghp_[A-Za-z0-9]{36}'
  'xox[baprs]-[A-Za-z0-9-]+'
)

# Also check for long hex/base64 strings that look like API keys
GENERIC_KEY_PATTERN='["\x27][A-Za-z0-9+/]{40,}["\x27]'

found_secrets=0

for pattern in "${SECRET_PATTERNS[@]}"; do
  # Search .py and .sh files, excluding .git and __pycache__
  matches=$(grep -rn --include="*.py" --include="*.sh" -E "$pattern" "$REPO_ROOT" \
    --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv 2>/dev/null || true)
  if [ -n "$matches" ]; then
    echo "FAIL: Found potential secret matching pattern '$pattern':"
    echo "$matches" | head -5
    found_secrets=1
  fi
done

# Check for generic long key-like strings in Python files
generic_matches=$(grep -rn --include="*.py" -E "$GENERIC_KEY_PATTERN" "$REPO_ROOT" \
  --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv \
  --exclude="*test*" --exclude="*fixture*" 2>/dev/null || true)
if [ -n "$generic_matches" ]; then
  echo "WARN: Found potential hardcoded keys (long quoted strings):"
  echo "$generic_matches" | head -5
  WARNINGS=$((WARNINGS + 1))
fi

if [ "$found_secrets" -eq 0 ]; then
  echo "PASS: No hardcoded secret patterns found."
else
  FAILED=1
fi
echo ""

# ── Check 2: No .env files in the repo ──────────────────────────────────────
echo "── Check 2: .env files ──"

env_files=$(find "$REPO_ROOT" -name ".env" -o -name ".env.*" \
  -not -path "$REPO_ROOT/.git/*" \
  -not -path "$REPO_ROOT/.gitignore" 2>/dev/null || true)

if [ -n "$env_files" ]; then
  echo "FAIL: Found .env files that should not exist in the repo:"
  echo "$env_files"
  FAILED=1
else
  echo "PASS: No .env files found in repository."
fi
echo ""

# ── Check 3: .gitignore contains .env ────────────────────────────────────────
echo "── Check 3: .gitignore coverage ──"

GITIGNORE="$REPO_ROOT/.gitignore"
if [ ! -f "$GITIGNORE" ]; then
  echo "FAIL: .gitignore does not exist."
  FAILED=1
elif ! grep -q "^\.env$" "$GITIGNORE" && ! grep -q "^\.env " "$GITIGNORE"; then
  echo "FAIL: .gitignore does not contain '.env' as an entry."
  FAILED=1
else
  echo "PASS: .gitignore contains .env entry."
fi
echo ""

# ── Check 4: Direct os.environ.get usage warning ────────────────────────────
echo "── Check 4: os.environ.get usage ──"

environ_usage=$(grep -rn --include="*.py" "os\.environ\.get\|os\.environ\[" "$REPO_ROOT" \
  --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv 2>/dev/null || true)

if [ -n "$environ_usage" ]; then
  echo "WARN: Direct os.environ usage found. Prefer typed configuration functions:"
  echo "$environ_usage" | head -10
  WARNINGS=$((WARNINGS + 1))
else
  echo "PASS: No direct os.environ usage found."
fi
echo ""

# ── Summary ──────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════"
echo " Security scan complete."
echo " Failures: $FAILED"
echo " Warnings: $WARNINGS"
echo "═══════════════════════════════════════════════════════════"

if [ "$FAILED" -gt 0 ]; then
  echo "BLOCKED: Security verification failed. Fix issues before proceeding."
  exit 1
fi

exit 0
