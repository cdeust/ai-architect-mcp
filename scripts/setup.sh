#!/usr/bin/env bash
set -euo pipefail

# AI Architect MCP — One-Command Setup
# Installs the MCP server, skills, and commands into Claude Code.
# Run from repo root:  ./scripts/setup.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Colors (disabled when not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; BOLD='\033[1m'; NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; BOLD=''; NC=''
fi

info()  { printf "${GREEN}[OK]${NC}  %s\n" "$1"; }
warn()  { printf "${YELLOW}[!!]${NC}  %s\n" "$1"; }
fail()  { printf "${RED}[ERR]${NC} %s\n" "$1"; exit 1; }

# ── 1. Check Python >= 3.12 ────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
  fail "Python 3 is not installed. Install Python 3.12+ and re-run."
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 12 ]); then
  fail "Python $PY_VERSION found — version 3.12+ required."
fi
info "Python $PY_VERSION detected"

# ── 2. Verify repo structure ───────────────────────────────────────────────

[ -f "$REPO_ROOT/mcp/pyproject.toml" ] \
  || fail "Missing mcp/pyproject.toml — run from the ai-architect repo root."
[ -d "$REPO_ROOT/skills" ] \
  || fail "Missing skills/ directory — run from the ai-architect repo root."
[ -f "$REPO_ROOT/CLAUDE.md" ] \
  || fail "Missing CLAUDE.md — run from the ai-architect repo root."
info "Repository structure verified"

# ── 3. Install MCP servers (editable, isolated venvs via uv) ──────────────

# `uv tool install --editable` is the failsafe for source-tree development:
# the tool's venv links the live source via .pth, so any edit to ./mcp/ or
# ./ai-codebase-intelligence/ is picked up on the next MCP server launch
# with no rebuild, no cache invalidation, no --refresh / --reinstall dance.
# Each tool gets its own venv that respects the package's pyproject.toml
# constraints (e.g. tree-sitter<0.25), unlike `pip install -e` against the
# system Python.

if ! command -v uv &>/dev/null; then
  fail "uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/"
fi
info "uv $(uv --version | awk '{print $2}') detected"

uv tool install --editable "$REPO_ROOT/mcp" --force --quiet 2>/dev/null \
  || uv tool install --editable "$REPO_ROOT/mcp" --force 2>&1
info "ai-architect MCP server installed (editable)"

if command -v ai_architect_mcp &>/dev/null; then
  info "Entry point 'ai_architect_mcp' available on PATH"
else
  warn "Entry point not on PATH — ensure ~/.local/bin is in \$PATH"
fi

if [ -f "$REPO_ROOT/ai-codebase-intelligence/pyproject.toml" ]; then
  uv tool install --editable "$REPO_ROOT/ai-codebase-intelligence" --force --quiet 2>/dev/null \
    || uv tool install --editable "$REPO_ROOT/ai-codebase-intelligence" --force 2>&1
  info "ai-codebase-intelligence MCP server installed (editable, 17 tools)"
else
  warn "ai-codebase-intelligence/ not found — codebase tools will be unavailable"
fi

# ── 4. Install skills into Claude Code ─────────────────────────────────────

CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
mkdir -p "$SKILLS_DIR"

# Link each skill directory
for skill_dir in "$REPO_ROOT/skills/"*/; do
  skill_name=$(basename "$skill_dir")
  # Remove stale link/dir
  if [ -L "$SKILLS_DIR/$skill_name" ] || [ -d "$SKILLS_DIR/$skill_name" ]; then
    rm -rf "$SKILLS_DIR/$skill_name"
  fi
  ln -sf "$skill_dir" "$SKILLS_DIR/$skill_name"
done
info "Skills installed → ~/.claude/skills/ (13 stages)"

# ── 5. Install commands into Claude Code ───────────────────────────────────

COMMANDS_DIR="$CLAUDE_DIR/commands/ai-architect"
mkdir -p "$COMMANDS_DIR"

for cmd_file in "$REPO_ROOT/commands/"*.md; do
  [ -f "$cmd_file" ] || continue
  cmd_name=$(basename "$cmd_file")
  ln -sf "$cmd_file" "$COMMANDS_DIR/$cmd_name"
done
info "Commands installed → ~/.claude/commands/ai-architect/"

# ── 6. Set up .mcp.json for Claude Code ────────────────────────────────────

PROJECT_MCP="$REPO_ROOT/.mcp.json"
if [ -f "$PROJECT_MCP" ]; then
  info "Project .mcp.json found — MCP server auto-discovered"
else
  warn "No .mcp.json found — create one or run: claude mcp add ai-architect -- ai_architect_mcp"
fi

# ── 7. Run tests to verify installation ────────────────────────────────────

if python3 -m pytest "$REPO_ROOT/tests/" -x -q --tb=no 2>/dev/null | tail -1 | grep -q "passed"; then
  PASS_COUNT=$(python3 -m pytest "$REPO_ROOT/tests/" -x -q --tb=no 2>/dev/null | tail -1 | grep -oE '[0-9]+ passed' || echo "tests passed")
  info "Test suite: $PASS_COUNT"
else
  warn "Some tests may have failed — run 'python3 -m pytest tests/' to check"
fi

# ── Done ───────────────────────────────────────────────────────────────────

printf "\n${BOLD}${GREEN}Setup complete!${NC}\n\n"

printf "  ${BOLD}Usage:${NC}\n"
printf "    Start ${BOLD}claude${NC} from any directory, then:\n\n"
printf "      ${BOLD}/ai-architect:run-pipeline${NC}           — run the full 11-stage pipeline\n"
printf "      ${BOLD}/ai-architect:generate-prd${NC}           — generate a 9-file PRD package\n"
printf "      ${BOLD}/ai-architect:verify-architecture${NC}    — run 64 HOR rules\n"
printf "      ${BOLD}/ai-architect:check-status${NC}           — check pipeline state\n\n"

printf "  ${BOLD}MCP Server:${NC}\n"
printf "    The MCP server starts automatically via .mcp.json when Claude Code opens this project.\n"
printf "    Manual start: ${BOLD}ai_architect_mcp${NC} or ${BOLD}python3 -m ai_architect_mcp.server${NC}\n\n"

printf "  ${BOLD}49 MCP Tools:${NC} verification, prompting, context, scoring, adapters, interview, memory, HOR, build/test\n"
printf "  ${BOLD}64 HOR Rules:${NC} deterministic verification across 10 categories\n"
printf "  ${BOLD}11 Stages:${NC} health → discovery → impact → integration → PRD → interview → review → implement → verify → benchmark → deploy → PR\n\n"
