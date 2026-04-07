# AI Architect

> **Findings → PRD → verified PR.** An autonomous software-engineering pipeline for Claude Code that runs on real evidence: 17 codebase intelligence tools, 5 science-backed git analytics, 64 deterministic verification rules, and zero LLM-judges-LLM. Every claim traces to a paper. Every PR passes its own gates.

```bash
/plugin marketplace add cdeust/ai-architect-mcp
/plugin install ai-architect
```

Then run `/ai-architect:run-pipeline` from any project. Open source. MIT licensed.

[![Tests](https://img.shields.io/badge/tests-544%20passing-brightgreen.svg)](#tests)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)

---

## What you get

Three MCP servers, one pipeline, one philosophy.

### `ai-architect` — pipeline orchestration (49 MCP tools)

- **11 stages, 0–10**: health → discovery → impact → integration → PRD → interview → review → implementation → verification → benchmark → PR
- **64 deterministic HOR rules** across 10 categories (structural, security, resilience, observability, …)
- **5 verification algorithms** — Chain of Verification, KS Adaptive Stability, Multi-Agent Debate, NLI Entailment, Zero-LLM Graph Verification
- **5 prompting algorithms** — TRM Self-Refine, Adaptive Expansion (ToT/GoT), Metacognitive Monitor, Signal-Aware Thought Buffer, Collaborative Inference
- **10-dimension Plan Interview gate** — deterministic PRD quality check with zero LLM calls

### `ai-codebase-intelligence` — typed graph engine (17 MCP tools)

- **Tree-sitter parsing** for 13 languages (Python, TS, Swift, Go, Rust, Java, Kotlin, C#, Ruby, PHP, C, C++, JavaScript)
- **Typed Pydantic API** — `GraphNode`, `GraphRelationship`, 29 node labels, 19 relationship types, no raw dicts
- **Hybrid search** — BM25 full-text + Reciprocal Rank Fusion + process-aware ranking
- **5 science-backed git analytics**:

  | Tool | Paper | What it does |
  |---|---|---|
  | `ownership` | Bird et al. 2011 (ESEC/FSE) | per-file ownership ratio + minor contributor count |
  | `bus_factor` | Avelino et al. 2016 (ICPC) | iterative top-contributor removal until orphan threshold |
  | `churn` | Nagappan & Ball 2005 (ICSE) | relative code churn metrics, defect predictor |
  | `cochange` | Gall 1998 + Zimmermann 2005 | hidden coupling via association rule mining on commits |
  | `dead_code` | Grove 1997 + Tip 1999 | conservative CHA-based reachability with confidence levels |

### `cortex` (optional) — persistent cognitive memory

Recall past findings before each pipeline run. Remember decisions after. The pipeline learns across sessions instead of starting fresh every time. See [Cortex](https://github.com/cdeust/cortex).

---

## 30-second start

```bash
git clone https://github.com/cdeust/ai-architect-mcp.git
cd ai-architect-mcp
./scripts/setup.sh
```

That installs both MCP servers, symlinks the 13 stage skills into `~/.claude/skills/`, and registers the slash commands. Restart Claude Code, then:

```
/ai-architect:run-pipeline
```

That's it. The pipeline detects findings, scores them, generates PRDs, implements them, verifies, and opens PRs.

---

## Real example — verified end-to-end

This repo dogfoods itself. PR [#2](https://github.com/cdeust/ai-architect-mcp/pull/2) was produced entirely through MCP tools:

| Stage | Tool | Result |
|---|---|---|
| 1. Discovery | `ai_architect_codebase_query("generator")` | Found `core/wiki/generator.py` (355 lines, violates 300 limit) |
| 2. Score | `ai_architect_compound_score` | **0.735** (relevance 0.95, uniqueness 0.4, impact 0.6, confidence 0.95) |
| 3. Verify | `ai_architect_run_hor_rules` | **61/64 passed**, adjusted_score **0.75** |
| 4. Recall | `cortex:recall` | No prior fix on this file — proceed |
| 5. Decide | `ai_architect_emit_ooda_checkpoint(phase=decide)` | PROCEED |
| 6. Implement | manual edit → `phases.py` extracted | 7 functions extracted, 211+278 lines |
| 7. Test | `pytest tests/unit/` | **544/544 passing** |
| 8. Branch + commit + push + PR | `gh pr create` | [PR #2](https://github.com/cdeust/ai-architect-mcp/pull/2) green ✓ |
| 9. Remember | `cortex:remember` | memory persisted for next session |

CI runs the same 544-test suite on every PR. **No PR ships without green tests.**

---

## How it works

```
Findings (research papers, bug reports, ideas)
   │
   ▼
Stage 0  Health        Validate all 49 + 17 MCP tools
Stage 1  Discovery     Query codebase intelligence + churn/cochange + cortex recall
Stage 2  Impact        Compound scoring + ownership + bus_factor risk
Stage 3  Integration   Cochange coupling + dead_code cleanup + port design
Stage 4  PRD           Generate via ai-prd-generator (delegated)
Stage 4.5 Interview    10-dimension deterministic gate
Stage 5  Review        7 verification algorithms, loop on score < 0.85
Stage 6  Implementation One worker per file, dependency-ordered
Stage 7  Verification  64 HOR rules + build gate, loop on failure
Stage 8  Benchmark     Performance gates from prd-tests.md
Stage 9  Deployment    Full test suite, zero failures required
Stage 10 PR            Push, open PR with audit trail, save lessons to cortex
```

Three layers, strictly separated:

- **Skills** (`skills/*/SKILL.md`) define **WHAT** each stage does. Markdown only, zero code.
- **Tools** (`mcp/`, `ai-codebase-intelligence/`) define **HOW**. Python only, zero markdown logic.
- **Claude** decides **WHY**. Reads the skill, calls tools, evaluates output, retries or proceeds.

---

## Installation

### Plugin (Claude Code)

```
/plugin marketplace add cdeust/ai-architect-mcp
/plugin install ai-architect
```

### Manual (Claude Code, Cursor, VS Code, Claude Desktop)

```bash
git clone https://github.com/cdeust/ai-architect-mcp.git
cd ai-architect-mcp
./scripts/setup.sh
```

`setup.sh` installs both MCP servers via `pip install -e`, symlinks all stage skills into `~/.claude/skills/`, and writes the slash commands. Restart your editor.

### Claude Desktop config

```json
{
  "mcpServers": {
    "ai-architect": { "command": "ai_architect_mcp" },
    "codebase-intelligence": {
      "command": "python3",
      "args": ["-m", "ai_codebase_intelligence"]
    }
  }
}
```

<details>
<summary>Config file location</summary>

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

</details>

---

## Usage

### Slash commands

| Command | What it does |
|---|---|
| `/ai-architect:run-pipeline` | Full 11-stage pipeline — findings to pull requests |
| `/ai-architect:generate-prd` | Generate a 9-file PRD package with verification |
| `/ai-architect:verify-architecture` | Run 64 HOR rules on your codebase |
| `/ai-architect:check-status` | Check pipeline state, active finding, retry counts |

### Direct tool calls

The MCP tools are discoverable from any Claude Code session. No slash command needed for one-off use:

```
Use ai_architect_codebase_query to find the OrchestrationEngine class
Use ai_architect_codebase_dead_code with min_confidence 0.9
Use ai_architect_run_hor_rules on this PRD
Use ai_architect_compound_score with relevance 0.8 uniqueness 0.6 impact 0.7 confidence 0.85
```

### Index a codebase

```
ai_architect_codebase_analyze --repo-path /path/to/your/repo
```

This runs the 6-phase ingestion (scan → structure → parse → resolve → community → process) and persists everything to `~/.codebase-intelligence/registry.json`. Subsequent queries are instant.

---

## Architecture principles

1. **Skills define WHAT. Tools define HOW. Claude decides WHY.** Never mix layers.
2. **The model generates. The system verifies.** No LLM judges LLM output. Stage 7 is fully deterministic.
3. **Adapters implement Ports.** No hardcoded infrastructure calls in stage logic.
4. **Context flows forward, never backward.** Each stage reads upstream, writes to its own slot.
5. **Every algorithm traces to a paper.** No invented constants. No "industry common sense."
6. **Full engine on every run.** No license gates, no tier checks, no feature flags.

---

## Tests

```bash
cd ai-codebase-intelligence
PYTHONPATH=src python3 -m pytest tests/unit/ -q
# 544 passed in ~6s
```

The CI workflow at `.github/workflows/test.yml` runs this on every PR plus a 300-line file-size guard. No PR merges without both checks green.

---

## Project structure

```
ai-architect-mcp/
├── README.md
├── CLAUDE.md                     # Project instructions for Claude
├── .github/workflows/test.yml    # CI: 544 tests + file-size guard
├── .mcp.json                     # MCP server auto-discovery
├── commands/                     # Slash commands (4)
├── skills/                       # Stage skills (13 — orchestrator + 12 stages)
│   ├── orchestrator/SKILL.md
│   ├── stage-0-health/SKILL.md
│   ├── stage-1-discovery/SKILL.md
│   └── …
├── mcp/                          # ai-architect MCP server (49 tools)
│   ├── ai_architect_mcp/
│   │   ├── _tools/               # Tool definitions
│   │   ├── _verification/        # 64 HOR rules + 5 verification algorithms
│   │   ├── _prompting/           # 5 prompting algorithms
│   │   ├── _interview/           # 10 dimension scorers
│   │   ├── _adapters/            # Git, fs, xcode ports
│   │   └── server.py
│   └── pyproject.toml
├── ai-codebase-intelligence/     # codebase-intelligence MCP server (17 tools)
│   ├── src/ai_codebase_intelligence/
│   │   ├── _models/              # Typed Pydantic graph models
│   │   ├── _analysis/            # Community + process detection
│   │   ├── _extraction/          # Call routing, heritage, type extractors
│   │   ├── _resolution/          # Per-language import resolvers
│   │   ├── _search/              # BM25 + RRF hybrid search
│   │   ├── _wiki/                # LLM-driven wiki generator
│   │   └── core/
│   │       ├── ingestion/        # 6-phase pipeline (incl. ownership, cochange)
│   │       ├── analysis/         # Bus factor, churn, dead code
│   │       └── storage/          # SQLite + in-memory graph index
│   └── tests/unit/               # 544 tests
└── scripts/setup.sh              # One-command install
```

---

## System requirements

- Python 3.12+
- Git
- Claude Code, Cursor, VS Code, or Claude Desktop with MCP support

---

## Part of a bigger system

- **PRD generation** is delegated to [ai-prd-generator](https://github.com/cdeust/ai-prd-generator-plugin) — same author, same methodology, free.
- **Cognitive memory** is delegated to [Cortex](https://github.com/cdeust/cortex) — persistent learning across sessions.
- **Specialized agents** are available via [zetetic-team-subagents](https://github.com/cdeust/zetetic-team-subagents) — orchestrator, engineer, code-reviewer, test-engineer, etc.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Troubleshooting

**Commands not found** — Run `./scripts/setup.sh` again. Check that `~/.claude/skills/orchestrator/` exists and is a symlink.

**MCP server not connecting** — Verify Python 3.12+ is installed. Run `python3 -m ai_architect_mcp.server` to test directly. For codebase intelligence: `python3 -m ai_codebase_intelligence`.

**Tests failing locally** — Run `cd ai-codebase-intelligence && PYTHONPATH=src python3 -m pytest tests/unit/ -x -v` for verbose output.

**MCP daemon caches stale state after `analyze`** — Restart Claude Code after the first index of a new repo. The daemon re-reads the registry on startup.

---

Built by [Clement Deust](https://ai-architect.tools) — methodology over tooling. The pipeline is the vehicle, the verification is the value.
