# AI Architect — Architecture

## Four-Layer Design

AI Architect separates concerns into four layers. Each layer has a single responsibility and communicates with adjacent layers through defined interfaces.

### Layer 1: Skills (WHAT)

Skills are Markdown documents (`SKILL.md`) that define what each pipeline stage does. They contain no code. Each skill specifies trigger conditions, input/output contracts, operations sequences (referencing MCP tool names), OODA checkpoints, and stop criteria. Skills follow Survival Architecture v2.2.

Claude reads the relevant skill at the start of each stage and uses it as a specification for what to do. Skills are never executed directly — they are instructions for the reasoning layer.

### Layer 2: Tools (HOW)

The MCP server (`mcp/ai_architect_mcp/`) exposes typed, annotated tools that perform discrete operations. Tools are stateless functions: they receive input, produce output, and have no knowledge of which stage called them.

Tool groups: verification algorithms (5 evaluation + 2 consensus), prompting enhancement (5 algorithms + 15 strategies), context management (StageContext, HandoffDocument), and infrastructure adapters (Git, Xcode, GitHub, FileSystem).

All external system interactions go through typed port interfaces (`_adapters/ports.py`). Concrete adapters are injected at the composition root.

### Layer 3: Reasoning (WHY)

Claude is the reasoning layer — the only component that exercises judgment. Claude reads skills, calls tools, evaluates outputs, and decides whether to retry or proceed. Claude orchestrates everything but owns nothing except the decision of what to do next.

The model generates. The system verifies. No LLM judges LLM output.

### Layer 4: Data (StageContext)

StageContext provides per-finding, per-stage artifact storage. Each finding gets a dedicated context that accumulates artifacts as it progresses through the 11-stage pipeline. Context flows forward, never backward — stages read predecessors' output (read-only) and write their own.

Four memory layers: session (current run), project (across runs), experience (with biological decay for pattern relevance), analytics (performance metrics).

Progressive disclosure: config (500 tokens) → summaries (300 tokens) → full docs (3K tokens).

## The 11-Stage Pipeline

The pipeline has 11 stages, numbered 0–10. Each finding gets a dedicated agent that carries full context from Stage 0 through Stage 10 with no handoffs. Multiple findings run in parallel.

| Stage | Name | Effort | Purpose |
|-------|------|--------|---------|
| 0 | HealthCheck | LOW | Pre-flight checks — tools, skills, dependencies |
| 1 | Discovery | MED | Scan 14 source categories for signals |
| 2 | Impact | MED | Compound scoring and propagation mapping |
| 3 | Integration | MED | Hexagonal architecture design (ports/adapters) |
| 4 | PRD | MAX | Machine-verifiable specification contract |
| 5 | Review | HIGH | Hostile review with full verification suite |
| 6 | Implementation | MAX | Orchestrator-worker code generation |
| 7 | Verification | LOW | 64 HOR rules, deterministic — no LLM |
| 8 | Benchmark | MED | Performance gates against NFR targets |
| 9 | Deployment | MED | Full test suite execution (unit + integration + e2e) |
| 10 | PullRequest | LOW | Push, create PR, write audit trail, close finding |

## Capability Routing

The pipeline routes work based on capability requirements:

- **Privacy-sensitive or deterministic** → Local execution (Foundation Models, on-device). HOR rules, scoring, graph analysis — anything that must be reproducible or that handles user data.
- **Cross-domain judgment** → Claude API. PRD generation, implementation orchestration, review — anything requiring reasoning across multiple knowledge domains.

## Verification Engine

10 implemented algorithms: 5 verification (KS Adaptive Stability Consensus, Multi-Agent Debate, Zero-LLM Graph Verification, NLI Entailment Evaluator, Weighted Average Consensus) + 5 prompting (Adaptive Expansion/ToT/GoT, Metacognitive, Collaborative Inference, Signal-Aware Thought Buffer, Confidence Fusion).

64 HOR rules enforce deterministic compliance. 3 pipeline gates control stage progression. Bayesian Consensus and Majority Voting are enum stubs only — not implemented.

## Three-System Overview

1. **Pipeline** — The 11-stage processing engine described above.
2. **Context Memory** — iCloud-backed persistence with four layers and progressive disclosure. Survives across sessions via HandoffDocument.
3. **Self-Improvement** — Experience patterns with biological decay. The system learns from past runs but older patterns decay to prevent stale knowledge from dominating.

## Clients

- **Mac app** (SwiftUI thin client) — spawns Claude CLI, displays results
- **Claude Code** (terminal) — direct pipeline access
- **Xcode MCP bridge** (28 tools) — native Xcode integration
- **GitHub Actions** (headless) — CI/CD pipeline execution

Adapters are protocol-based and swappable at runtime.
