# PRD: AI Architect — Full Implementation of Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**Author:** AI Architect PRD Generator v1.0.0
**PRD Type:** Feature (Full Scope Overview)
**Status:** Draft — Pending Stakeholder Review

---

## 1. Executive Summary

AI Architect is an autonomous software engineering platform with an 11-stage pipeline (0–10), 7 verification algorithms, 16 thinking strategies, 5 enhancement algorithms, 64 HOR rules, and 32 MCP tools — all operational today. This PRD covers the **6 remaining implementation gaps** required to complete the platform's full vision as defined in the architecture documentation and decision records.

The gaps span data persistence (four-layer memory model with iCloud sync), pipeline intelligence (Plan Interview stage 4.5), verification completeness (2 consensus algorithm stubs), enforcement infrastructure (6 new hooks with Survival Architecture v3.0), external integration (GitHub Actions headless client), and ecosystem expansion (Python MCP server for the broader developer community).

**Delivery Model:** Solo developer (Clément) + AI Architect pipeline generating implementation code. Phased across Q2–Q4 2026.

---

## 2. Strategic Context

### 2.1 Current State (March 2026)

| Component | Status | Evidence |
|-----------|--------|----------|
| 11-stage pipeline (stages 0–10) | ✅ Complete | 12 SKILL.md files, all Survival Architecture v2.2 |
| 7 verification algorithms | ✅ Complete | ALG-001 through ALG-007, tested |
| 64 HOR rules | ✅ Complete | 65 functions across 7 modules, deterministic |
| 16 thinking strategies | ✅ Complete | 4-tier registry, research-weighted selection |
| 5 enhancement algorithms | ✅ Complete | TRM, Adaptive Expansion, Thought Buffer, Collab Inference, Metacognitive |
| 32 MCP tools | ✅ Complete | 6 modules, all annotated with hints |
| 5 port interfaces + 5 adapters | ✅ Complete | Composition root enforced |
| 42 test files (2,933 LOC) | ✅ Complete | pytest + pytest-asyncio |
| 31 decision documents | ✅ Complete | 8 ADRs + 10 ALGs + 11 STGs + 2 templates |

### 2.2 Target State (Q4 2026)

Complete the platform by implementing the 6 epics described in this PRD, bringing AI Architect to full production readiness for all four target audiences: indie developers, professionals, enterprises, and schools.

### 2.3 What This PRD Is NOT

This is a **Full Scope Overview**. It provides T-shirt sizing (S/M/L/XL), dependency mapping, and phased roadmap for all 6 epics. It does NOT provide sprint-level story points, SQL DDL, detailed API specs, or JIRA-importable tickets. Select an individual epic for implementation-level detail when ready.

---

## 3. Business Goals

| ID | Goal | Baseline | Target | Source |
|----|------|----------|--------|--------|
| BG-001 | Complete platform feature coverage | 6 documented gaps | 0 gaps | Codebase analysis |
| BG-002 | Enable cross-device persistence | Local-only artifacts | Full iCloud sync across Mac/iPhone/iPad | ADR-002 |
| BG-003 | Achieve CI/CD automation | Manual pipeline triggers only | Headless GitHub Actions execution | Project description |
| BG-004 | Expand ecosystem to Python community | Swift/Node.js only | pip-installable Python package | ADR-004 |
| BG-005 | Reduce PRD generation defect rate | 8% with full suite (current) | < 5% with Plan Interview gate | ADR-001 metrics |
| BG-006 | Evolve architecture template | Survival v2.2 | Survival v3.0 with hook enforcement | Clarification Q1 |

---

## 4. Epic Overview — 6 Implementation Gaps

### Epic 1: Plan Interview Stage (Stage 4.5)

**Size:** L (5–8 weeks)
**Priority:** P0 — Critical path for PRD quality improvement
**Dependencies:** None (can start immediately)

**Description:** A mandatory interrogation gate inserted between Stage 4 (PRD Generation) and Stage 5 (PRD Review). Implements 10-dimension analysis (technical feasibility, UI/UX design, risk assessment, tradeoff analysis, edge cases, dependency mapping, test strategy, deployment planning, gap detection, security review) before any PRD is finalized. Blocks pipeline progression until the plan passes all 10 dimensions.

**What It Delivers:**
- New SKILL.md following Survival Architecture v3.0
- 10 interrogation dimension modules (one per dimension)
- Stage context integration (reads Stage 4 output, feeds Stage 5)
- Scoring rubric per dimension with pass/fail thresholds
- MCP tools: `ai_architect_plan_interview`, `ai_architect_plan_score`
- Tests: unit tests per dimension, integration test for stage flow

**Codebase Impact:**
- New directory: `skills/stage-4.5-plan-interview/`
- New module: `mcp/ai_architect_mcp/_interview/`
- Modified: `skills/orchestrator/SKILL.md` (stage ordering)
- Modified: `mcp/ai_architect_mcp/_tools/` (new tool module)
- New tests: `tests/test_interview/`

---

### Epic 2: Four-Layer Memory Model

**Size:** XL (9+ weeks)
**Priority:** P0 — Foundation for cross-device sync and experience learning
**Dependencies:** None (can start immediately, parallel with Epic 1)

**Description:** Implements the four-layer context memory architecture defined in the project description: Session layer (`PipelineState` with CloudKit sync), Project layer (enhanced `Finding` + `StageOutput`), Experience layer (`ExperiencePattern` with biological half-life decay), and Analytics layer (`AuditEvent` with immutable trail). Includes progressive disclosure (L1 config ~500t → L2 summary ~300t → L3 full ~3Kt) and context budget enforcement (70% → summaries, 93% → auto-handoff).

**What It Delivers:**
- SwiftData models: `PipelineState`, `ExperiencePattern`, `AuditEvent`
- CloudKit sync configuration for all persistent models
- Biological decay algorithm for experience patterns (half-life calculation)
- Progressive disclosure engine with 3 loading levels
- Context budget monitor with automatic escalation
- HandoffDocument auto-generation at 93% context usage

**Codebase Impact:**
- New/modified: `mcp/ai_architect_mcp/_models/pipeline_state.py`
- New: `mcp/ai_architect_mcp/_models/experience_pattern.py`
- New: `mcp/ai_architect_mcp/_models/audit_event.py`
- New: `mcp/ai_architect_mcp/_context/progressive_disclosure.py`
- New: `mcp/ai_architect_mcp/_context/budget_monitor.py`
- Modified: `mcp/ai_architect_mcp/_context/artifact_store.py` (CloudKit adapter)
- Modified: `mcp/ai_architect_mcp/_adapters/ports.py` (new ports)
- New tests: `tests/test_memory/`

---

### Epic 3: Consensus Algorithm Completion

**Size:** S (1–2 weeks)
**Priority:** P2 — Nice-to-have, not blocking core functionality
**Dependencies:** None

**Description:** Implement the 2 consensus algorithms that exist as enum stubs in `ConsensusAlgorithm`: Bayesian Consensus (posterior probability aggregation with prior updating) and Majority Voting (simple threshold-based agreement). Both are defined in `_models/consensus.py` but have no implementation in `_verification/algorithms/`.

**What It Delivers:**
- `bayesian_consensus.py` — Full Bayesian posterior calculation with configurable priors
- `majority_voting.py` — Threshold-based majority agreement with tie-breaking rules
- ALG decision documents for both algorithms
- Integration with existing `ConsensusAlgorithm` enum routing
- Tests with deterministic fixtures (bit-for-bit output matching)

**Codebase Impact:**
- New: `mcp/ai_architect_mcp/_verification/algorithms/bayesian_consensus.py`
- New: `mcp/ai_architect_mcp/_verification/algorithms/majority_voting.py`
- Modified: `mcp/ai_architect_mcp/_verification/algorithms/` (routing in engine)
- New: `docs/decisions/algorithmic/ALG-011-bayesian-consensus.md`
- New: `docs/decisions/algorithmic/ALG-012-majority-voting.md`
- New tests: `tests/test_verification/test_bayesian_consensus.py`, `test_majority_voting.py`

---

### Epic 4: Hook System Expansion

**Size:** M (3–4 weeks)
**Priority:** P1 — Required for enforcement of Survival Architecture v3.0
**Dependencies:** Epic 2 (AuditEvent model for `update-pipeline-state` hook)

**Description:** Implement 6 new pipeline enforcement hooks defined in the architecture but not yet built. These hooks enforce the "Skills define WHAT, Tools define HOW, Claude decides WHY" principle at runtime by blocking operations that violate architectural contracts.

**Hooks to Implement:**
1. `SessionStart` — Load `PipelineState`, validate skill versions, check iCloud sync status
2. `enforce-doc-read.sh` — Block write operations until the relevant SKILL.md has been read
3. `validate-output-schema.sh` — Verify stage output matches the declared contract
4. `security-tier-check.sh` — Apply 10-tier threat model assessment to bash commands
5. `update-pipeline-state.sh` — Update `PipelineState` and log `AuditEvent` after each stage
6. `save-session-summary.sh` — Auto-write `HandoffDocument` at session end

**What It Delivers:**
- 6 new hook scripts/modules
- Survival Architecture v3.0 template (ADR-009)
- 10-tier security threat model definition
- Hook dispatch integration with existing `hooks/` infrastructure
- Tests per hook with mock adapters

**Codebase Impact:**
- New: `hooks/pre-tool-use/enforce-doc-read.sh`
- New: `hooks/pre-tool-use/security-tier-check.sh`
- New: `hooks/post-tool-use/validate-output-schema.sh`
- New: `hooks/post-tool-use/update-pipeline-state.sh`
- New: `hooks/session/session-start.sh`
- New: `hooks/session/save-session-summary.sh`
- New: `docs/decisions/architectural/ADR-009-survival-v3.md`
- Modified: `skills/orchestrator/SKILL.md` (hook references)
- New tests: `tests/test_hooks/`

---

### Epic 5: GitHub Actions Client

**Size:** L (5–8 weeks)
**Priority:** P1 — Required for enterprise adoption and CI/CD automation
**Dependencies:** Epic 4 (hooks must work for headless enforcement)

**Description:** A headless client adapter that enables AI Architect to run inside GitHub Actions workflows. The pipeline executes without human intervention: a GitHub event (issue, PR comment, schedule) triggers a full Stage 0–10 run, producing merge-ready PRs with audit trails. The adapter implements the same port interfaces as the interactive client, ensuring identical pipeline behavior.

**What It Delivers:**
- `GitHubActionsAdapter` implementing all 5 port interfaces for CI/CD context
- GitHub Actions workflow YAML templates (issue-triggered, schedule-triggered, PR-comment-triggered)
- Event parsing (webhook payload → `Finding` extraction)
- Artifact collection (stage outputs → GitHub Actions artifacts)
- Status reporting (check runs, PR comments with verification reports)
- Secret management (ANTHROPIC_API_KEY, GitHub token via Actions secrets)

**Codebase Impact:**
- New: `mcp/ai_architect_mcp/_adapters/github_actions_adapter.py`
- New: `.github/workflows/ai-architect-pipeline.yml`
- New: `.github/workflows/ai-architect-nightly.yml`
- New: `scripts/ci/entrypoint.py` (headless pipeline runner)
- Modified: `mcp/ai_architect_mcp/_adapters/composition_root.py` (new adapter wiring)
- New: `docs/decisions/architectural/ADR-010-github-actions-client.md`
- New tests: `tests/test_adapters/test_github_actions_adapter.py`

---

### Epic 6: Python MCP Server Migration

**Size:** XL (9+ weeks)
**Priority:** P1 — Ecosystem expansion, pip-installable package
**Dependencies:** Epics 1–4 (should migrate the complete engine, not a partial one)

**Description:** Full port of the MCP server from the current Node.js implementation (13 basic tools) to the production Python engine (32 tools + all algorithms). The Python server becomes the canonical implementation, pip-installable as `ai-architect-mcp`. This is independent of the MIT capstone, which has its own academic scope. The production PRD covers: FastMCP server setup, all 32 tools registered, all 7 verification algorithms callable, all 16 strategies available, all 5 port interfaces with concrete adapters, PyPI packaging, and documentation.

**What It Delivers:**
- `ai-architect-mcp` PyPI package (pip-installable)
- FastMCP server with all 32 tools
- Full algorithm suite (verification + prompting + HOR)
- CLI entry point: `ai-architect-mcp serve`
- Configuration via environment variables and TOML
- Comprehensive documentation (README, API reference, examples)
- Migration guide from Node.js server

**Codebase Impact:**
- Primary: `mcp/` directory (already Python — this epic completes packaging)
- New: `mcp/pyproject.toml` updates for PyPI publishing
- New: `mcp/ai_architect_mcp/__main__.py` (CLI entry point)
- New: `mcp/ai_architect_mcp/_config/` (TOML configuration loader)
- Modified: `README.md` (installation instructions)
- New: `docs/migration-from-nodejs.md`
- New: `docs/python-api-reference.md`

---

## 5. Epic Dependency Map

```
Epic 3 (Consensus) ──────────────────────────────────────────┐
  [S, No deps]                                                │
                                                              │
Epic 1 (Plan Interview) ─────────────────────────────────────┤
  [L, No deps]                                                │
                                                              ├──→ Epic 6 (Python Migration)
Epic 2 (Memory Model) ──→ Epic 4 (Hooks) ──→ Epic 5 (GHA) ──┤    [XL, depends on 1-4]
  [XL, No deps]            [M, needs E2]      [L, needs E4]  │
                                                              │
```

**Critical Path:** Epic 2 → Epic 4 → Epic 5 → Epic 6
**Parallel Tracks:** Epic 1 and Epic 3 can run in parallel with the critical path.

---

## 6. Phased Roadmap (Q2–Q4 2026)

### Phase 1: Foundation (Q2 2026 — April–June)

| Epic | T-Shirt | Status | Rationale |
|------|---------|--------|-----------|
| Epic 3: Consensus Completion | S | Start April | Quick win, unblocks verification completeness |
| Epic 1: Plan Interview (Stage 4.5) | L | Start April | No dependencies, high PRD quality impact |
| Epic 2: Four-Layer Memory Model | XL | Start April | Critical path foundation, longest lead time |

**Phase 1 Deliverables:**
- Bayesian Consensus + Majority Voting algorithms (with tests)
- Plan Interview stage fully operational (10 dimensions)
- SwiftData models + CloudKit sync + progressive disclosure
- Survival Architecture v3.0 template defined

### Phase 2: Enforcement (Q3 2026 — July–September)

| Epic | T-Shirt | Status | Rationale |
|------|---------|--------|-----------|
| Epic 2: Memory Model (continued) | XL | Complete by July | Experience decay + analytics layer finalization |
| Epic 4: Hook System Expansion | M | Start July | Depends on AuditEvent from Epic 2 |
| Epic 5: GitHub Actions Client | L | Start August | Depends on hooks from Epic 4 |

**Phase 2 Deliverables:**
- 6 new hooks operational with security tier enforcement
- GitHub Actions adapter with 3 workflow templates
- Full hook dispatch integration
- ADR-009 (Survival v3.0) and ADR-010 (GitHub Actions) published

### Phase 3: Ecosystem (Q4 2026 — October–December)

| Epic | T-Shirt | Status | Rationale |
|------|---------|--------|-----------|
| Epic 5: GitHub Actions (continued) | L | Complete by October | Finalize CI/CD automation |
| Epic 6: Python MCP Server Migration | XL | Start October | All components ready for migration |

**Phase 3 Deliverables:**
- `ai-architect-mcp` published on PyPI
- Migration guide from Node.js
- Full API documentation
- Production-ready headless CI/CD pipeline

---

## 7. T-Shirt Sizing Summary

| Epic | Size | Estimated Duration | Estimated SP Range | Risk |
|------|------|-------------------|-------------------|------|
| Epic 1: Plan Interview | L | 5–8 weeks | 34–55 SP | Medium — new stage type, 10 dimensions |
| Epic 2: Memory Model | XL | 9–12 weeks | 55–89 SP | High — CloudKit sync complexity, decay algorithm |
| Epic 3: Consensus Completion | S | 1–2 weeks | 5–8 SP | Low — well-defined algorithm patterns |
| Epic 4: Hook System | M | 3–4 weeks | 13–21 SP | Medium — security tier model is new |
| Epic 5: GitHub Actions | L | 5–8 weeks | 34–55 SP | High — headless execution, secret management |
| Epic 6: Python Migration | XL | 9–12 weeks | 55–89 SP | Medium — engine exists, packaging is incremental |
| **Total** | — | **32–46 weeks** | **196–317 SP** | — |

**Note:** With solo developer + AI agents, assume ~60-70% calendar efficiency (context switches, debugging, documentation). The 3-quarter timeline (Q2–Q4) provides adequate buffer.

---

## 8. Risks & Assumptions

### Assumptions (Require Validation)

| ID | Assumption | Impact if Wrong | Validator |
|----|------------|-----------------|-----------|
| A-001 | CloudKit sync works reliably for SwiftData models with complex relationships | +4 weeks for custom sync engine | Clément (prototype Sprint 0) |
| A-002 | Existing Python MCP engine (32 tools) is stable enough for PyPI packaging | +2 weeks for stabilization | Test suite (42 files) |
| A-003 | GitHub Actions runner has sufficient resources for full pipeline execution | Architecture redesign for distributed execution | CI/CD testing |
| A-004 | Biological decay formula from ADR-007 is correct for experience patterns | Recalibration needed, +1 week | Domain expert review |
| A-005 | AI Architect can generate its own implementation code (self-hosting) | Fall back to manual coding, +30% timeline | Pipeline validation |

### Risks

| ID | Risk | Severity | Probability | Mitigation |
|----|------|----------|-------------|------------|
| R-001 | CloudKit sync conflicts with concurrent devices | HIGH | Medium | Implement conflict resolution strategy in Epic 2 |
| R-002 | 10-tier security model blocks legitimate operations | MEDIUM | Medium | Start with permissive mode, tighten iteratively |
| R-003 | Python package dependency conflicts with user environments | MEDIUM | Low | Minimal dependencies, pin versions, test across Python 3.12+ |
| R-004 | GitHub Actions timeout on complex pipelines | HIGH | Medium | Implement stage checkpointing and resumption |
| R-005 | MIT capstone scope diverges from production needs | LOW | Low | PRD is independent (per clarification) |

---

## 9. Architecture Evolution: Survival v2.2 → v3.0

### What Changes in v3.0

| Aspect | v2.2 (Current) | v3.0 (Target) |
|--------|----------------|---------------|
| Hook enforcement | 3 hooks (optional) | 9 hooks (6 new, mandatory) |
| Context memory | Single-layer (filesystem) | Four-layer (session/project/experience/analytics) |
| Progressive disclosure | Not implemented | L1/L2/L3 with automatic escalation |
| Security model | Not enforced | 10-tier threat model with hook gates |
| Pipeline state | Implicit (file-based) | Explicit `PipelineState` model with CloudKit |
| Audit trail | Not implemented | Immutable `AuditEvent` log |
| Experience learning | Not implemented | Biological decay patterns |

### Backward Compatibility

All existing SKILL.md files (12 stages) remain valid under v3.0. The new template adds sections for hook declarations, context budget, and security tier — but these default to v2.2 behavior when omitted.

---

## 10. Success Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| All 6 epics delivered | Epic completion tracking | 6/6 by Q4 2026 |
| Zero architectural violations | HOR rule 16-22 pass rate | 100% on new code |
| Test coverage maintained | pytest coverage report | ≥ 85% line coverage |
| Pipeline self-hosting | AI Architect generates own code | ≥ 1 epic fully self-generated |
| PyPI package published | `pip install ai-architect-mcp` works | Published by Q4 2026 |
| CloudKit sync operational | Cross-device test | Data visible on 2+ Apple devices |
| GitHub Actions CI/CD | Automated pipeline run | Issue → PR in < 30 minutes |

---

## 11. Recommended Next Steps

1. **Select an epic** for implementation-level PRD (story points, DDL, API specs, JIRA tickets)
2. **Prototype CloudKit sync** in Sprint 0 to validate A-001 before committing to Epic 2 timeline
3. **Define Survival Architecture v3.0 template** (ADR-009) before starting Epic 4
4. **Run existing test suite** to establish current baseline before adding new components

---

**Select an epic when ready for implementation-level PRD.**
