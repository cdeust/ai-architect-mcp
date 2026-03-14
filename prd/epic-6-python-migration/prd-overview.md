# Epic 6: Python MCP Server Migration — Overview

**Epic ID:** E6
**Title:** Package Python MCP Engine as PyPI Package with CLI & Config
**Status:** Planned
**Timeline:** 9–12 weeks (XL: 55–89 SP)
**Dependencies:** Epics 1, 2, 3, 4 (complete engine with new components)
**Type:** Packaging, Configuration, Documentation

---

## Executive Summary

Epic 6 packages the **existing, mature Python MCP engine** (`mcp/ai_architect_mcp/`) as a production-grade PyPI package (`ai-architect-mcp`), complete with a CLI entry point, TOML configuration system, migration documentation, and comprehensive testing.

**This is NOT a rewrite.** The Python engine is already built with 32 tools, 7 verification algorithms, 64 HOR rules, 16 strategies, and 5 enhancements. Epic 6 focuses on:

1. **Packaging** — Prepare PyPI metadata, build system, and entry points
2. **CLI** — `ai-architect-mcp serve`, `ai-architect-mcp version`, `ai-architect-mcp health`
3. **Configuration** — TOML-based config with environment variable overrides
4. **Verification** — Test all 32 tools, algorithms, HOR rules, and strategies in package context
5. **Migration** — Complete guide from Node.js MCP server to Python engine
6. **Documentation** — API reference, developer guide, troubleshooting

The Python engine is **independent** of the MIT capstone project (Epic 7); it stands alone as a production tool.

---

## Objectives

| Objective | Success Criteria |
|-----------|-----------------|
| **Package Ready** | `pip install ai-architect-mcp` succeeds; version published to TestPyPI and PyPI |
| **CLI Functional** | `serve` command starts MCP server; `version` and `health` commands work |
| **Config System** | TOML config loads; env vars override; defaults apply; validation passes |
| **Tools Verified** | All 32 tools registered, callable, respond with correct schema in package context |
| **Algorithms Verified** | All 7 verification algorithms accessible and functional |
| **HOR Rules Verified** | All 64 HOR rules execute without error |
| **Strategies Verified** | All 16 prompting strategies callable; 5 enhancements apply |
| **Migration Guide** | Step-by-step Node.js → Python transition documented with examples |
| **API Docs** | Complete reference for all tools, config options, and CLI commands |
| **Cross-Python** | Tested on Python 3.12 and 3.13; install time <30s; package size <10MB |

---

## User Personas

1. **AI Architect Core Team**
   - Deploy Python engine as standalone MCP server in production pipelines
   - Configure via TOML files in CI/CD environments
   - Monitor health via CLI and endpoint

2. **Migration Lead (Node.js → Python)**
   - Follow migration guide to retire Node.js server
   - Map old Node.js tool calls to new Python equivalents
   - Validate tool responses match expected schemas

3. **AI Architect Integrator**
   - Install `ai-architect-mcp` via pip in Docker or local env
   - Reference API docs to build custom prompts and verification pipelines
   - Extend with custom HOR rules or strategies

---

## Scope

### In-Scope

- PyPI packaging with hatchling build system
- CLI entry point with `click` (or equivalent)
- TOML configuration loader with env var override hierarchy
- Verification of all 32 tools in packaged context
- Verification of all 7 algorithms, 64 HOR rules, 16 strategies, 5 enhancements
- Migration guide (Node.js → Python with tool mapping)
- Complete API reference documentation
- Health check endpoint (CLI and HTTP-like interface)
- TestPyPI publish workflow
- Production PyPI publish workflow
- pytest-based test suite for package installation and tool invocation
- Optional: Docker Dockerfile for containerized deployment

### Out-of-Scope

- Rewrite of Python engine components (already built)
- MIT capstone integration (Epic 7)
- Web dashboard or UI
- RBAC or authentication layers (handled by deployment)
- Performance optimization of algorithms (already optimized)
- New tools or algorithms beyond existing 32 + 7

---

## Architecture Overview

```
mcp/ai_architect_mcp/
├── __main__.py                 # NEW: CLI entry point (click commands)
├── _config/                    # NEW: Configuration system
│   ├── __init__.py
│   ├── loader.py               # TOML parser + env override
│   └── defaults.toml           # Default config values
├── _tools/                     # EXISTING: 32 tools (6 modules)
│   ├── verification_tools.py   # 5 tools
│   ├── hor_tools.py            # 8 tools
│   ├── prompting_tools.py      # 6 tools
│   ├── context_tools.py        # 5 tools
│   ├── adapter_tools.py        # 5 tools
│   └── scoring_tools.py        # 3 tools
├── _verification/              # EXISTING: 7 algorithms + 64 HOR rules
├── _prompting/                 # EXISTING: 16 strategies + 5 enhancements
├── _adapters/                  # EXISTING: Git, Xcode, GitHub, FileSystem
├── _models/                    # EXISTING: 20+ Pydantic v2 models
├── _context/                   # EXISTING: StageContext, HandoffDocument
├── _scoring/                   # EXISTING: Compound scoring
└── server.py                   # EXISTING: FastMCP entry point

pyproject.toml                  # UPDATED: PyPI metadata + entry_points
```

**What's New:**
- `__main__.py` — CLI with serve, version, health, config-validate commands
- `_config/loader.py` — TOML parser with schema validation
- `_config/defaults.toml` — All configurable options (server port, log level, timeout, etc.)
- Updated `pyproject.toml` with entry_points, PyPI classifiers, optional Docker

**What Stays:**
- All 32 tools, 7 algorithms, 64 HOR rules, 16 strategies, 5 enhancements (unchanged)

---

## Node.js → Python Tool Mapping

The Node.js MCP server (13 tools) maps to Python tools as follows:

| Node.js Tool | Python Equivalent | Notes |
|--------------|-------------------|-------|
| `verify_claim` | `ai_architect_verify_claim` | Chain of Verification |
| `decompose_claim` | `ai_architect_decompose_claim` | Atomic decomposition |
| `consensus_debate` | `ai_architect_consensus_debate` | Multi-agent debate |
| `nli_eval` | `ai_architect_nli_evaluate` | Entailment evaluation |
| `weighted_consensus` | `ai_architect_weighted_consensus` | Consensus aggregation |
| `adaptive_consensus` | `ai_architect_adaptive_consensus` | Stability-based consensus |
| `graph_constrain` | `ai_architect_graph_constrain` | Dependency constraints |
| `prompt_enhance` | `ai_architect_prompt_enhance` | Enhancement pipeline |
| `thinking_strategy_select` | `ai_architect_thinking_strategy_select` | Strategy selection |
| `context_load` | `ai_architect_context_load` | Stage context loading |
| `context_query` | `ai_architect_context_query` | Context querying |
| `git_status` | `ai_architect_git_status` | Git adapter |
| `github_search` | `ai_architect_github_search` | GitHub adapter |

**Additional Python Tools (19 new):**
- Handoff document management (3 tools)
- Artifact store operations (4 tools)
- HOR rule execution (8 tools)
- Scoring and propagation (4 tools)

---

## Key Features

### 1. **CLI Interface**

```bash
# Start MCP server with default config
ai-architect-mcp serve

# Start with custom config file
ai-architect-mcp serve --config /etc/ai-architect/config.toml

# Override via environment
AI_ARCHITECT_PORT=3001 ai-architect-mcp serve

# Query version
ai-architect-mcp version

# Health check
ai-architect-mcp health

# Validate config without starting server
ai-architect-mcp config-validate /etc/ai-architect/config.toml
```

### 2. **TOML Configuration**

```toml
[server]
name = "ai-architect"
port = 3000
log_level = "info"

[verification]
timeout_seconds = 30
consensus_algorithm = "adaptive_stability"

[prompting]
enhancement_enabled = true
thinking_strategy = "tree_of_thought"

[context]
stage_context_dir = "./stage_contexts"
artifact_storage = "local"
```

### 3. **Environment Variable Overrides**

```bash
AI_ARCHITECT_PORT=3001
AI_ARCHITECT_LOG_LEVEL=debug
AI_ARCHITECT_VERIFICATION_TIMEOUT=60
AI_ARCHITECT_PROMPTING_ENHANCEMENT_ENABLED=false
```

### 4. **Health Check Endpoint**

```bash
ai-architect-mcp health
# Output:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "tools_registered": 32,
#   "algorithms_available": 7,
#   "hor_rules_loaded": 64,
#   "uptime_seconds": 1234.5
# }
```

### 5. **Migration Guide**

Complete step-by-step documentation:
- Pre-migration checklist
- Node.js tool → Python tool mapping with examples
- Configuration translation (Node.js env vars → TOML/Python env)
- Validation and testing procedures
- Rollback plan

---

## Quality Criteria

| Criterion | Target |
|-----------|--------|
| **Install Time** | <30 seconds on standard hardware |
| **Package Size** | <10 MB (compressed) |
| **Python Support** | 3.12, 3.13 (minimum 3.12) |
| **Tool Response Time** | <5s per tool (p95) |
| **Test Coverage** | >85% of new code (CLI, config, package structure) |
| **Documentation** | 100% API coverage, examples for all tools |
| **Backward Compatibility** | All Node.js tool calls map 1:1 to Python tools |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| PyPI publish fails | Low | High | TestPyPI integration test, dry-run publish |
| Config parsing breaks tools | Low | High | Comprehensive config validation tests |
| Cross-Python version issues | Medium | Medium | Test matrix (3.12, 3.13); CI automation |
| Tool response schema mismatch | Low | Medium | Tool registration verification; schema tests |
| Performance degradation in package | Low | Medium | Benchmark baseline from existing engine |
| Migration tool mapping incomplete | Medium | High | Tool mapping audit before release |

---

## Timeline & Milestones

| Milestone | Timing | Deliverables |
|-----------|--------|--------------|
| Sprint 1–2 | Weeks 1–3 | CLI + TOML config loader (10 SP) |
| Sprint 3 | Week 4–5 | Package structure + PyPI metadata (8 SP) |
| Sprint 4 | Week 6–7 | Tool & algorithm verification (13 SP) |
| Sprint 5 | Week 8 | HOR rules & strategies verification (10 SP) |
| Sprint 6 | Week 9–10 | Docs + migration guide (10 SP) |
| Sprint 7 | Week 11–12 | TestPyPI + production publish (8 SP) |

**Total: 59 SP over 12 weeks**

---

## Dependencies

**Hard Dependencies:**
- Epic 1: Plan & Interview (context framework)
- Epic 2: Memory Model (HOR rules + artifact store)
- Epic 3: Consensus Algorithms (verification algorithms)
- Epic 4: Hooks & Adapters (adapter framework)

**Soft Dependencies:**
- GitHub Actions (Epic 5) — optional CI/CD automation

---

## Acceptance Criteria (High-Level)

1. `pip install ai-architect-mcp` succeeds on Python 3.12 and 3.13
2. `ai-architect-mcp serve` starts MCP server without errors
3. All 32 tools are registered and callable
4. All 7 algorithms are accessible in package context
5. All 64 HOR rules execute without errors
6. TOML config loads and validates
7. Environment variable overrides work correctly
8. Migration guide provides complete Node.js → Python mapping
9. API reference covers all tools, config options, and commands
10. Health check endpoint returns correct status
11. Package published to TestPyPI and PyPI
12. Installation time is <30 seconds; package size <10 MB

---

## Success Metrics

- **Adoption:** Core team deploys Python engine in ≥2 production pipelines
- **Reliability:** Zero critical bugs in first month; <0.1% tool failure rate
- **Performance:** Tool response time p95 <5s (matching existing engine)
- **Documentation:** 100% API coverage; zero unanswered questions in first deployment
- **Testing:** 85%+ test coverage; all cross-version tests pass

---

## References

- AI Architect Main PRD (Epics 1–7)
- Epic 1: Plan & Interview PRD
- Epic 2: Memory Model PRD
- Epic 3: Consensus Algorithms PRD
- Epic 4: Hooks & Adapters PRD
- Epic 5: GitHub Actions PRD
- MCP Protocol Specification (Anthropic)
- PyPI Publishing Guidelines
- FastMCP Documentation

