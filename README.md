# AI Architect

**Stop writing code without a spec.** This Claude Code plugin runs an 11-stage autonomous pipeline — from research findings to merge-ready pull requests — with 64 deterministic verification rules and zero LLM judges.

```
/plugin marketplace add cdeust/ai-architect-mcp
/plugin install ai-architect
```

Then run `/ai-architect:run-pipeline` from any project. Open source, MIT licensed.

---

## What You Get

Four commands:

| Command | What it does |
|---------|-------------|
| `/ai-architect:run-pipeline` | Full 11-stage pipeline — findings to pull requests |
| `/ai-architect:generate-prd` | Generate a 9-file PRD package with verification |
| `/ai-architect:verify-architecture` | Run 64 HOR rules on your codebase |
| `/ai-architect:check-status` | Check pipeline state, active finding, retry counts |

**49 MCP tools** across 9 categories. **64 deterministic verification rules**. **10 algorithms** (5 verification + 5 prompting). **11 pipeline stages**.

Built on Anthropic's [Model Context Protocol](https://modelcontextprotocol.io). Three layers, strictly separated: **Skills** define WHAT. **Tools** define HOW. **Claude** decides WHY.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)

---

## How It Works

1. **You describe a finding or feature** — research paper, bug report, or feature idea
2. **Discovery** — scans 14 source categories, scores for relevance
3. **Impact analysis** — compound scoring, dependency propagation, blast radius mapping
4. **Integration design** — hexagonal architecture, affected ports and adapters
5. **PRD generation** — 9-file machine-verifiable specification via [ai-prd-generator](https://github.com/cdeust/ai-prd-generator-plugin)
6. **Plan interview** — 10-dimension deterministic quality gate
7. **PRD review** — 7 verification algorithms, loops back if score < 0.85
8. **Implementation** — one worker per file, dependency-ordered commits
9. **Verification** — 64 HOR rules + build gate, loops back on failure
10. **Benchmark + tests** — performance gates, full test suite
11. **Delivery** — push branch, create PR with audit trail, distil experience patterns

---

## Quick Start

### Install (2 commands)

```
/plugin marketplace add cdeust/ai-architect-mcp
/plugin install ai-architect
```

### Run the pipeline

```
/ai-architect:run-pipeline
```

Or just describe what you need — the plugin detects intent.

### Generate a PRD only

```
/ai-architect:generate-prd
```

### Manual setup (alternative)

```bash
git clone https://github.com/cdeust/ai-architect-mcp.git
cd ai-architect-mcp
./scripts/setup.sh
```

This installs the MCP server (`pip install -e mcp/`), symlinks skills to `~/.claude/skills/`, and installs slash commands to `~/.claude/commands/ai-architect/`.

---

## Configuration

### Claude Code (automatic)

The `.mcp.json` at the repo root auto-configures the MCP server when Claude Code opens the project. No manual setup needed after `./scripts/setup.sh`.

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-architect": {
      "command": "ai_architect_mcp",
      "env": {}
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

### Claude Code (manual)

```bash
claude mcp add ai-architect -- ai_architect_mcp
```

### Cursor / VS Code

```json
{
  "mcpServers": {
    "ai-architect": {
      "command": "ai_architect_mcp"
    }
  }
}
```

---

## Tools

49 tools across 9 categories, all prefixed with `ai_architect_`:

### Verification (6 tools)

| Tool | Description |
|------|-------------|
| `verify_claim` | Chain-of-Verification on requirement claims |
| `verify_graph` | Zero-LLM acyclic graph verification |
| `evaluate_nli` | Natural Language Inference entailment check |
| `debate_claim` | Multi-Agent Debate (Tool-MAD, A-HMAD, FREE-MAD) |
| `consensus` | KS Adaptive Stability with Beta-Binomial early stopping |
| `decompose_claim` | Break complex claims into atomic verifiable units |

### HOR Rules (3 tools)

| Tool | Description |
|------|-------------|
| `run_hor_rules` | Run all 64 deterministic rules |
| `run_hor_category` | Run rules by category (10 categories) |
| `run_hor_single` | Run a single rule by ID |

### Prompting (7 tools)

| Tool | Description |
|------|-------------|
| `enhance_prompt` | TRM recursive refinement (Self-Refine) |
| `select_strategy` | Auto-select strategy by task type |
| `expand_thought` | Adaptive Expansion with ToT/GoT |
| `fuse_confidence` | Confidence Fusion across sources |
| `metacognitive_monitor` | Self-aware reasoning with intervention triggers |
| `thought_buffer` | Signal-aware template-based enhancement |
| `collaborative_infer` | Multi-path reasoning with consensus detection |

### Context (8 tools)

| Tool | Description |
|------|-------------|
| `load_context` | Load stage context for a finding |
| `save_context` | Write stage artifact to context |
| `query_context` | Semantic search across stage contexts |
| `create_handoff` | Generate handoff document for session continuity |
| `load_handoff` | Resume from a previous handoff |
| `emit_ooda_checkpoint` | Record OODA loop checkpoint |
| `emit_thinking_step` | Record reasoning trace step |
| `emit_decision` | Record pipeline decision |

### Scoring (2 tools)

| Tool | Description |
|------|-------------|
| `compound_score` | Weighted multi-dimension compound scoring |
| `trace_propagation` | Dependency propagation path tracing |

### Interview (3 tools)

| Tool | Description |
|------|-------------|
| `score_dimension` | Score PRD against one of 10 interview dimensions |
| `run_interview_gate` | Run all 10 scorers with gate decision |
| `query_interview_results` | Retrieve past interview results |

### Memory (8 tools)

| Tool | Description |
|------|-------------|
| `load_session_state` | Load pipeline state |
| `save_session_state` | Persist pipeline state |
| `save_experience_pattern` | Store learned pattern with biological decay |
| `list_experience_patterns` | Retrieve non-decayed patterns |
| `reinforce_pattern` | Reset decay on pattern access |
| `append_audit_event` | Append to immutable audit trail |
| `query_audit_events` | Query audit history |
| `check_context_budget` | Monitor context window usage |

### Adapters (11 tools)

| Tool | Description |
|------|-------------|
| `git_branch` | Create implementation branch |
| `git_commit` | Commit with traceability message |
| `git_push` | Push branch to remote |
| `git_diff` | Compare refs |
| `git_worktree_add` | Create isolated worktree per finding |
| `git_worktree_remove` | Clean up worktree |
| `github_create_pr` | Create pull request with audit body |
| `fs_read` | Read file via filesystem port |
| `fs_write` | Write file via filesystem port |
| `fs_list` | List directory contents |

### Build & Test (2 tools)

| Tool | Description |
|------|-------------|
| `run_build` | Trigger project build |
| `run_tests` | Run test suite |

---

## Pipeline Stages

| Stage | Name | Pattern | What It Does |
|-------|------|---------|-------------|
| 0 | Health Check | Single pass | Validate all tools, skills, and dependencies |
| 1 | Discovery | Parallel fan-out | Scan 14 source categories, score for relevance |
| 2 | Impact | Prompt chaining | Compound scoring + propagation mapping |
| 3 | Integration | Single LLM call | Design ports, adapters, composition root changes |
| 4 | PRD Generation | Evaluator-optimizer | Generate 9-file PRD via ai-prd-generator plugin |
| 4.5 | Plan Interview | Deterministic gate | 10-dimension quality gate (zero LLM) |
| 5 | PRD Review | Evaluator-optimizer | 7 verification algorithms, loops to Stage 4 |
| 6 | Implementation | Orchestrator-workers | One worker per file, dependency-ordered |
| 7 | Verification | Deterministic | 64 HOR rules + build gate, loops to Stage 6 |
| 8 | Benchmark | Single pass | Performance gates from prd-tests.md |
| 9 | Deployment | Single pass | Full test suite, zero failures required |
| 10 | Pull Request | Single pass | Push, create PR, write audit trail |

---

## 64 HOR Rules

Deterministic rules organized into 10 categories:

| Category | Rules | Criticality |
|----------|-------|-------------|
| Core PRD Structural | 23 | 48 critical (-0.15 per violation) |
| Architecture & Code Quality | 7 | 16 warnings (-0.05 per violation) |
| Security | 8 | |
| Data Protection & Compliance | 6 | |
| Error Handling & Resilience | 5 | |
| Concurrency & State Management | 3 | |
| Senior Code Quality Standards | 6 | |
| Comprehensive Testing | 6 | |
| Observability & Monitoring | 4 | |
| Dependency & Supply Chain | 2 | |

All rules are pure functions. No LLM calls in verification. A universal PASS across all claims is itself a violation — NEEDS-RUNTIME verdicts are required.

---

## Under the Hood

| | |
|---|---|
| **MCP Tools** | 49 — verification, prompting, context, scoring, adapters, interview, memory, HOR, build/test |
| **HOR Rules** | 64 deterministic rules across 10 categories |
| **Algorithms** | 10 — 5 verification (CoV, Graph, NLI, MAD, KS Consensus) + 5 prompting (Expansion, Metacognitive, Collaborative, Signal Buffer, Confidence Fusion) |
| **Pipeline Stages** | 11 (0-10) — health, discovery, impact, integration, PRD, interview, review, implementation, verification, benchmark, deployment, PR |
| **Thinking Strategies** | 16 — from MIT, Stanford, Harvard, Anthropic, OpenAI, DeepSeek research |

## Part of a Bigger System

This plugin is the pipeline engine. It delegates PRD generation (Stage 4) to **[ai-prd-generator](https://github.com/cdeust/ai-prd-generator-plugin)** — the free, open-source PRD generator.

If you only need PRDs without the full pipeline, use ai-prd-generator directly.

## Project Structure

```
ai-architect-mcp/
├── .mcp.json                     # MCP server auto-discovery
├── commands/                     # Slash commands for Claude Code
│   ├── run-pipeline.md
│   ├── generate-prd.md
│   ├── verify-architecture.md
│   └── check-status.md
├── mcp/                          # MCP server (pip-installable)
│   ├── ai_architect_mcp/
│   │   ├── _tools/               # 49 MCP tool definitions
│   │   ├── _verification/        # HOR rules engine + algorithms
│   │   ├── _prompting/           # 15 thinking strategies
│   │   ├── _context/             # StageContext + RAG
│   │   ├── _scoring/             # Compound scoring
│   │   ├── _adapters/            # Port implementations (git, fs, xcode)
│   │   ├── _observability/       # JSONL + SSE event streaming
│   │   └── server.py             # FastMCP entry point
│   └── pyproject.toml
├── skills/                       # Stage skill definitions (Markdown)
│   ├── orchestrator/SKILL.md
│   ├── stage-0-health/SKILL.md
│   ├── stage-1-discovery/SKILL.md
│   ├── stage-2-impact/SKILL.md
│   ├── stage-3-integration/SKILL.md
│   ├── stage-4-prd/SKILL.md
│   ├── stage-4-5-interview/SKILL.md
│   ├── stage-5-review/SKILL.md
│   ├── stage-6-implementation/SKILL.md
│   ├── stage-7-verification/SKILL.md
│   ├── stage-8-benchmark/SKILL.md
│   ├── stage-9-deployment/SKILL.md
│   └── stage-10-pr/SKILL.md
├── hooks/                        # Pipeline enforcement (shell)
├── scripts/                      # Setup + verification scripts
├── tests/                        # 592 tests with fixtures
├── docs/                         # Architecture + decision documents
└── CLAUDE.md                     # Project instructions for Claude
```

---

## System Requirements

- Python 3.12+
- Git
- Claude Code (Anthropic)

## Development

```bash
git clone https://github.com/cdeust/ai-architect-mcp.git
cd ai-architect-mcp
./scripts/setup.sh    # installs MCP server, skills, commands
python3 -m pytest tests/ -q   # 592 tests
```

---

## Architecture Principles

1. **Skills define WHAT. Tools define HOW. Claude decides WHY.** Never mix layers.
2. **The model generates. The system verifies.** No LLM judges LLM output.
3. **Adapters implement Ports.** No hardcoded infrastructure calls in stage logic.
4. **Context flows forward, never backward.** Each stage reads upstream, writes to its own slot.
5. **Stage 7 is deterministic.** No LLM calls in a verification stage. Closed tool allowlist.
6. **Full engine on every run.** No license gates, no tier checks, no feature flags.

---

## Key Invariants

- 11 stages numbered 0-10. Never reference "10 stages."
- 10 implemented algorithms: 5 verification + 5 prompting. Never inflate the count.
- 64 HOR rules + 3 pipeline gates. Gates are gates, not HOR rules.
- 100% PASS in verification is a violation. NEEDS-RUNTIME required.
- ClarificationReport from Stage 4 is permanent — not re-generated on retry.

---

## License

MIT

---

## Troubleshooting

**Commands not found** — Run `./scripts/setup.sh` again. Check that `~/.claude/skills/orchestrator/` exists.

**MCP server not connecting** — Verify Python 3.12+ is installed. Run `python3 -m ai_architect_mcp.server` to test directly.

**Tests failing** — Run `python3 -m pytest tests/ -x -v` for verbose output on the first failure.

---

Built by [Clement Deust](https://ai-architect.tools)
