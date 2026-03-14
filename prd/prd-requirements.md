# PRD Requirements — AI Architect Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**PRD Type:** Full Scope Overview

---

## 1. Functional Requirements

**Note:** This is a Full Scope Overview. Requirements are organized by epic with T-shirt sizing. Detailed story points are deferred to per-epic implementation PRDs.

### 1.1 Epic 1: Plan Interview Stage (Stage 4.5)

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|------------|--------|
| FR-001 | Implement Stage 4.5 as a mandatory gate between Stage 4 (PRD Generation) and Stage 5 (PRD Review) | P0 | — | Codebase analysis: `skills/` directory lacks stage-4.5 |
| FR-002 | Implement 10 interrogation dimensions: technical feasibility, UI/UX design, risk assessment, tradeoff analysis, edge cases, dependency mapping, test strategy, deployment planning, gap detection, security review | P0 | FR-001 | Project description: "10-dimension interrogation" |
| FR-003 | Each dimension produces a scored assessment with pass/fail threshold | P0 | FR-002 | User Request |
| FR-004 | Stage 4.5 reads Stage 4 output via StageContextPort and writes enriched context for Stage 5 | P0 | FR-001 | Codebase: `_context/stage_context.py` pattern |
| FR-005 | Pipeline blocks progression to Stage 5 if any critical dimension fails | P0 | FR-003 | User Request |
| FR-006 | Register MCP tools `ai_architect_plan_interview` and `ai_architect_plan_score` | P1 | FR-001 | Codebase: existing tool registration pattern in `_tools/` |
| FR-007 | Create SKILL.md following Survival Architecture v3.0 template | P1 | FR-001, Epic 4 | Clarification Q1: "Evolve to v3.0" |

### 1.2 Epic 2: Four-Layer Memory Model

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|------------|--------|
| FR-008 | Implement `PipelineState` Pydantic model with fields: current_stage, active_finding, agent_id, skill_versions, last_sync_timestamp | P0 | — | Project description: "Session layer" |
| FR-009 | Implement CloudKit sync adapter for `PipelineState` using SwiftData + CloudKit | P0 | FR-008 | Clarification Q3: "Include CloudKit" |
| FR-010 | Implement `ExperiencePattern` model with biological half-life decay calculation | P0 | — | ADR-007: "Experience Pattern Decay" |
| FR-011 | Half-life decay formula: `relevance = initial_relevance × 0.5^(elapsed_days / half_life_days)` with configurable half-life per pattern type | P0 | FR-010 | ADR-007 |
| FR-012 | Implement `AuditEvent` immutable model with fields: who (agent_id), what (action), when (timestamp), where (stage), outcome (success/failure) | P0 | — | Project description: "Analytics layer" |
| FR-013 | AuditEvent log is append-only; no update or delete operations permitted | P0 | FR-012 | User Request |
| FR-014 | Implement progressive disclosure engine with 3 levels: L1 config (~500 tokens, always loaded), L2 summary (~300 tokens, on match), L3 full (~3,000 tokens, on demand) | P1 | — | Project description: "Progressive disclosure" |
| FR-015 | Implement context budget monitor: at 70% context usage switch to L2 summaries, at 93% auto-generate HandoffDocument | P1 | FR-014 | Project description |
| FR-016 | Define new ports: `PipelineStatePort`, `ExperiencePort`, `AuditPort` in `ports.py` | P0 | FR-008, FR-010, FR-012 | Codebase: `_adapters/ports.py` pattern |
| FR-017 | Implement CloudKit-backed adapters for all three new ports | P0 | FR-016 | Clarification Q3 |

### 1.3 Epic 3: Consensus Algorithm Completion

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|------------|--------|
| FR-018 | Implement Bayesian Consensus algorithm with configurable prior distribution (Beta prior) | P2 | — | Codebase: `_models/consensus.py` enum stub |
| FR-019 | Implement Majority Voting algorithm with configurable threshold (default: >50%) and tie-breaking rule | P2 | — | Codebase: `_models/consensus.py` enum stub |
| FR-020 | Integrate both algorithms into existing `ConsensusAlgorithm` routing in verification engine | P2 | FR-018, FR-019 | Codebase: existing routing pattern |
| FR-021 | Create ALG-011 and ALG-012 decision documents following 6-point framework | P2 | FR-018, FR-019 | Project instructions: decision document requirement |

### 1.4 Epic 4: Hook System Expansion

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|------------|--------|
| FR-022 | Implement `SessionStart` hook: load PipelineState, validate skill versions against manifest, check iCloud sync status | P1 | FR-008 (Epic 2) | Project description: "Target Hooks" |
| FR-023 | Implement `enforce-doc-read` PreToolUse hook: block any write tool invocation until the relevant stage SKILL.md has been read in the current session | P0 | — | Project description: "PreToolUse hooks enforce documentation reading" |
| FR-024 | Implement `validate-output-schema` PostToolUse hook: verify stage output matches the declared output contract in SKILL.md | P1 | — | Project description |
| FR-025 | Implement `security-tier-check` PreToolUse hook: assess bash commands against 10-tier threat model, block tiers 8-10 | P1 | — | Project description: "10-tier threat model" |
| FR-026 | Implement `update-pipeline-state` PostToolUse hook: update PipelineState model and log AuditEvent after each stage completion | P1 | FR-008, FR-012 (Epic 2) | Project description |
| FR-027 | Implement `save-session-summary` session-end hook: auto-write HandoffDocument with current session state | P1 | — | Codebase: `_context/handoff.py` pattern |
| FR-028 | Define Survival Architecture v3.0 template in ADR-009 with mandatory hook declarations, context budget section, and security tier specification | P0 | — | Clarification Q1: "Evolve to v3.0" |

### 1.5 Epic 5: GitHub Actions Client

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|------------|--------|
| FR-029 | Implement `GitHubActionsAdapter` implementing all 5 port interfaces (Git, Xcode, GitHub, FileSystem, StageContext) for CI/CD context | P1 | Epic 4 | Project description: "GitHub Actions (headless)" |
| FR-030 | Create issue-triggered workflow: GitHub issue with label `ai-architect` triggers full Stage 0–10 pipeline run | P1 | FR-029 | User Request |
| FR-031 | Create schedule-triggered workflow: nightly pipeline run on configurable cron | P1 | FR-029 | Project description: "nightly improvement" |
| FR-032 | Create PR-comment-triggered workflow: `/ai-architect run` comment triggers pipeline on PR branch | P1 | FR-029 | User Request |
| FR-033 | Implement artifact collection: stage outputs uploaded as GitHub Actions artifacts | P1 | FR-029 | User Request |
| FR-034 | Implement status reporting: GitHub check runs with verification report summary | P1 | FR-029 | User Request |
| FR-035 | Secret management: ANTHROPIC_API_KEY and GITHUB_TOKEN via Actions secrets, no hardcoded values | P0 | FR-029 | Project instructions: "no hardcoded secrets" |

### 1.6 Epic 6: Python MCP Server Migration

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|------------|--------|
| FR-036 | Package existing Python MCP server as `ai-architect-mcp` PyPI package | P1 | Epics 1–4 | ADR-004: "Python MCP Server (Target)" |
| FR-037 | Implement CLI entry point: `ai-architect-mcp serve` starts the FastMCP server | P1 | FR-036 | User Request |
| FR-038 | Implement TOML-based configuration: server port, log level, adapter selection, API keys via env vars | P1 | FR-036 | User Request |
| FR-039 | All 32 MCP tools registered and callable via MCP protocol | P0 | FR-036 | Codebase: existing 32 tools |
| FR-040 | All 7 verification algorithms + 64 HOR rules accessible | P0 | FR-036 | Codebase: existing algorithms |
| FR-041 | All 16 thinking strategies + 5 enhancement algorithms accessible | P0 | FR-036 | Codebase: existing strategies |
| FR-042 | Create migration guide from Node.js server with step-by-step instructions | P1 | FR-036 | User Request |
| FR-043 | Create Python API reference documentation | P1 | FR-036 | User Request |

### Suggested Additions

*These requirements were not explicitly requested but are recommended based on codebase analysis:*

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| [SUGGESTED] FR-044 | Implement health check endpoint for Python MCP server (`/health`) | P2 | Standard for production services; codebase has Stage 0 health check pattern |
| [SUGGESTED] FR-045 | Add OpenTelemetry instrumentation to Python MCP server | P2 | Aligns with HOR rules 58–61 (observability); no current tracing |
| [SUGGESTED] FR-046 | Create Docker container for Python MCP server | P2 | Simplifies GitHub Actions deployment and community adoption |

---

## 2. Non-Functional Requirements

| ID | Requirement | Metric | Target | Source |
|----|-------------|--------|--------|--------|
| NFR-001 | Plan Interview stage execution time | Wall-clock time for 10 dimensions | < 60 seconds per dimension | User Request |
| NFR-002 | Memory model persistence latency | CloudKit round-trip time | < 2 seconds for PipelineState sync | Industry benchmark: CloudKit typical latency |
| NFR-003 | Experience decay calculation performance | Computation time for 10,000 patterns | < 100ms | ADR-007 |
| NFR-004 | Hook execution overhead | Per-hook latency added to pipeline | < 500ms per hook | User Request |
| NFR-005 | GitHub Actions pipeline total execution time | Issue → PR creation | < 30 minutes for standard findings | BG-007 |
| NFR-006 | Python package install time | `pip install ai-architect-mcp` | < 30 seconds on standard connection | Industry benchmark |
| NFR-007 | Python package size | Wheel file size | < 10 MB | Industry benchmark: FastMCP ~2MB |
| NFR-008 | Context budget enforcement accuracy | Budget calculation precision | ±5% of actual token usage | User Request |
| NFR-009 | Audit event write throughput | Events per second | ≥ 100 events/sec (append-only) | User Request |
| NFR-010 | CloudKit conflict resolution | Conflict detection rate | 100% conflicts detected, 95% auto-resolved | Industry benchmark |
| NFR-011 | Backward compatibility | Existing SKILL.md files under v3.0 | 100% compatible (no breaking changes) | User Request |
| NFR-012 | Security tier assessment latency | Per-command security classification | < 200ms | User Request |
| NFR-013 | Test coverage for new code | Line coverage | ≥ 85% | Codebase: existing coverage standard |
| NFR-014 | Zero framework imports in new domain models | Domain layer purity | 0 external imports in `_models/` | Codebase: `_adapters/ports.py` pattern |
