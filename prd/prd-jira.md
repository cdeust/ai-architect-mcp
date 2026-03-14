# PRD JIRA Tickets — AI Architect Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**PRD Type:** Full Scope Overview (T-Shirt Sizing, No Sprint-Level SP)
**Total Epics:** 6
**Estimated Total SP Range:** 196–317 SP

---

## Note on T-Shirt Sizing

This is a Full Scope Overview. JIRA tickets use **T-shirt sizing** (S/M/L/XL) rather than Fibonacci story points. When an epic is selected for implementation-level PRD, tickets will be refined with exact SP estimates, sprint assignments, and task breakdowns.

---

## Epic 1: Plan Interview Stage (Stage 4.5)

**Epic Size:** L (34–55 SP estimated range)
**Priority:** P0
**Labels:** `pipeline`, `quality-gate`, `stage-4.5`

| Ticket | Type | Title | Size | Priority | Depends On | AC Reference |
|--------|------|-------|------|----------|------------|-------------|
| AIA-001 | Story | Define InterviewResult and DimensionScore domain models | S | P0 | — | AC-004 |
| AIA-002 | Story | Implement 10 interrogation dimension definitions | M | P0 | AIA-001 | AC-001, AC-004 |
| AIA-003 | Story | Implement dimension scorer with configurable thresholds | M | P0 | AIA-001 | AC-004, AC-005 |
| AIA-004 | Story | Implement interview gate logic (block/proceed decision) | M | P0 | AIA-002, AIA-003 | AC-002, AC-003 |
| AIA-005 | Story | Implement StageContext integration (read Stage 4, write for Stage 5) | M | P0 | AIA-004 | AC-003 |
| AIA-006 | Story | Register MCP tools: plan_interview, plan_score | S | P1 | AIA-004 | AC-001 |
| AIA-007 | Story | Create Stage 4.5 SKILL.md (Survival v3.0 template) | S | P1 | AIA-004 | AC-001 |
| AIA-008 | Story | Update orchestrator stage ordering (4 → 4.5 → 5) | S | P0 | AIA-004, AIA-005 | AC-002 |
| AIA-009 | Story | Write STG-4.5 decision document | S | P2 | AIA-004 | — |
| AIA-010 | Story | Full test suite for Plan Interview stage | M | P0 | AIA-001–AIA-008 | AC-001–AC-005 |

---

## Epic 2: Four-Layer Memory Model

**Epic Size:** XL (55–89 SP estimated range)
**Priority:** P0
**Labels:** `data-layer`, `persistence`, `cloudkit`, `memory`

| Ticket | Type | Title | Size | Priority | Depends On | AC Reference |
|--------|------|-------|------|----------|------------|-------------|
| AIA-011 | Story | Implement PipelineState Pydantic model | S | P0 | — | AC-006 |
| AIA-012 | Story | Implement ExperiencePattern model with decay formula | M | P0 | — | AC-008, AC-009 |
| AIA-013 | Story | Implement AuditEvent immutable model | S | P0 | — | AC-012, AC-013 |
| AIA-014 | Story | Define PipelineStatePort, ExperiencePort, AuditPort | S | P0 | AIA-011, AIA-012, AIA-013 | — |
| AIA-015 | Story | Implement CloudKit sync adapter for PipelineState | L | P0 | AIA-014 | AC-006, AC-007 |
| AIA-016 | Story | Implement CloudKit sync adapter for ExperiencePattern | L | P0 | AIA-014 | AC-008 |
| AIA-017 | Story | Implement CloudKit sync adapter for AuditEvent | M | P0 | AIA-014 | AC-012 |
| AIA-018 | Story | Implement conflict resolution strategy (last-writer-wins) | M | P0 | AIA-015 | AC-007 |
| AIA-019 | Story | Implement progressive disclosure engine (L1/L2/L3) | L | P1 | AIA-011 | AC-010 |
| AIA-020 | Story | Implement context budget monitor (70%/93% thresholds) | M | P1 | AIA-019 | AC-010, AC-011 |
| AIA-021 | Story | Implement auto-HandoffDocument generation at 93% | M | P1 | AIA-020 | AC-011 |
| AIA-022 | Story | Update composition root with new ports and adapters | S | P0 | AIA-015–AIA-017 | — |
| AIA-023 | Story | Cross-device integration testing | L | P0 | AIA-015–AIA-018 | AC-006, AC-007 |
| AIA-024 | Story | Full test suite for memory model | M | P0 | AIA-011–AIA-021 | AC-006–AC-013 |

---

## Epic 3: Consensus Algorithm Completion

**Epic Size:** S (5–8 SP estimated range)
**Priority:** P2
**Labels:** `verification`, `algorithm`, `consensus`

| Ticket | Type | Title | Size | Priority | Depends On | AC Reference |
|--------|------|-------|------|----------|------------|-------------|
| AIA-025 | Story | Implement Bayesian Consensus algorithm | S | P2 | — | AC-014, AC-015 |
| AIA-026 | Story | Implement Majority Voting algorithm | S | P2 | — | AC-016, AC-017 |
| AIA-027 | Story | Integrate both into ConsensusAlgorithm routing | S | P2 | AIA-025, AIA-026 | AC-015, AC-017 (routing) |
| AIA-028 | Story | Create ALG-011 and ALG-012 decision documents | S | P2 | AIA-025, AIA-026 | — |
| AIA-029 | Story | Tests with deterministic fixtures | S | P2 | AIA-025–AIA-027 | AC-014–AC-017 |

---

## Epic 4: Hook System Expansion

**Epic Size:** M (13–21 SP estimated range)
**Priority:** P1
**Labels:** `enforcement`, `hooks`, `security`, `survival-v3`

| Ticket | Type | Title | Size | Priority | Depends On | AC Reference |
|--------|------|-------|------|----------|------------|-------------|
| AIA-030 | Story | Define Survival Architecture v3.0 template (ADR-009) | M | P0 | — | — |
| AIA-031 | Story | Implement enforce-doc-read PreToolUse hook | M | P0 | — | AC-018, AC-019 |
| AIA-032 | Story | Implement validate-output-schema PostToolUse hook | M | P1 | AIA-030 | — |
| AIA-033 | Story | Implement security-tier-check PreToolUse hook (10-tier model) | L | P1 | — | AC-020, AC-021 |
| AIA-034 | Story | Implement update-pipeline-state PostToolUse hook | M | P1 | AIA-013 (Epic 2) | AC-012 |
| AIA-035 | Story | Implement SessionStart hook | S | P1 | AIA-011 (Epic 2) | AC-023 |
| AIA-036 | Story | Implement save-session-summary session-end hook | S | P1 | — | AC-022 |
| AIA-037 | Story | Update all 12 SKILL.md files to v3.0 template | M | P1 | AIA-030 | — |
| AIA-038 | Story | Full test suite for hooks | M | P0 | AIA-031–AIA-036 | AC-018–AC-023 |

---

## Epic 5: GitHub Actions Client

**Epic Size:** L (34–55 SP estimated range)
**Priority:** P1
**Labels:** `ci-cd`, `github-actions`, `adapter`, `headless`

| Ticket | Type | Title | Size | Priority | Depends On | AC Reference |
|--------|------|-------|------|----------|------------|-------------|
| AIA-039 | Story | Implement GitHubActionsAdapter: GitOps port | M | P1 | — | AC-024 |
| AIA-040 | Story | Implement GitHubActionsAdapter: FileSystemOps port | S | P1 | — | AC-024 |
| AIA-041 | Story | Implement GitHubActionsAdapter: GitHubOps port | M | P1 | — | AC-025 |
| AIA-042 | Story | Implement GitHubActionsAdapter: ContextOps port | M | P1 | — | AC-024 |
| AIA-043 | Story | Create issue-triggered workflow YAML | M | P1 | AIA-039–AIA-042 | AC-024, AC-025 |
| AIA-044 | Story | Create nightly schedule workflow YAML | M | P1 | AIA-039–AIA-042 | AC-026, AC-027 |
| AIA-045 | Story | Create PR-comment-triggered workflow YAML | M | P1 | AIA-039–AIA-042 | — |
| AIA-046 | Story | Implement artifact collection (stage outputs → GHA artifacts) | M | P1 | AIA-042 | — |
| AIA-047 | Story | Implement status reporting (GitHub check runs) | M | P1 | AIA-041 | AC-028, AC-029 |
| AIA-048 | Story | Secret management: API keys via Actions secrets | S | P0 | — | — |
| AIA-049 | Story | Create ADR-010 + headless pipeline entrypoint | M | P1 | AIA-039–AIA-042 | — |
| AIA-050 | Story | End-to-end test: issue → PR | L | P0 | AIA-043, AIA-047 | AC-024, AC-025 |

---

## Epic 6: Python MCP Server Migration

**Epic Size:** XL (55–89 SP estimated range)
**Priority:** P1
**Labels:** `packaging`, `pypi`, `python`, `migration`

| Ticket | Type | Title | Size | Priority | Depends On | AC Reference |
|--------|------|-------|------|----------|------------|-------------|
| AIA-051 | Story | Implement CLI entry point (`ai-architect-mcp serve`) | M | P1 | — | AC-031 |
| AIA-052 | Story | Implement TOML configuration loader with env var override | M | P1 | — | AC-032, AC-033 |
| AIA-053 | Story | Configure pyproject.toml for PyPI publishing | S | P1 | — | AC-030 |
| AIA-054 | Story | Verify all 32 MCP tools register in package context | L | P0 | AIA-053 | AC-031 |
| AIA-055 | Story | Verify all 7 verification algorithms in package context | M | P0 | AIA-053 | — |
| AIA-056 | Story | Verify all 16 strategies + 5 enhancements in package | M | P0 | AIA-053 | — |
| AIA-057 | Story | Verify 64 HOR rules in package context | M | P0 | AIA-053 | — |
| AIA-058 | Story | Create migration guide from Node.js | M | P1 | AIA-054 | AC-034 |
| AIA-059 | Story | Create Python API reference documentation | M | P1 | AIA-054 | — |
| AIA-060 | Story | TestPyPI publish + cross-version testing (Python 3.12, 3.13) | M | P1 | AIA-053–AIA-057 | AC-030 |
| AIA-061 | Story | Production PyPI publish | S | P0 | AIA-060 | AC-030, AC-031 |
| AIA-062 | Story | Verify MCP protocol compatibility with Node.js server | M | P1 | AIA-054 | AC-035 |

---

## Summary Table

| Ticket Range | Epic | Tickets | Epic Size | Priority |
|-------------|------|---------|-----------|----------|
| AIA-001 to AIA-010 | Epic 1: Plan Interview | 10 | L | P0 |
| AIA-011 to AIA-024 | Epic 2: Memory Model | 14 | XL | P0 |
| AIA-025 to AIA-029 | Epic 3: Consensus | 5 | S | P2 |
| AIA-030 to AIA-038 | Epic 4: Hook System | 9 | M | P1 |
| AIA-039 to AIA-050 | Epic 5: GitHub Actions | 12 | L | P1 |
| AIA-051 to AIA-062 | Epic 6: Python Migration | 12 | XL | P1 |
| **Total** | **6 Epics** | **62 tickets** | — | — |

---

## CSV Export (for JIRA import)

```csv
Summary,Issue Type,Priority,Epic,Labels,Size,Depends On,AC Reference
"Define InterviewResult and DimensionScore domain models",Story,P0,Plan Interview,"pipeline quality-gate stage-4.5",S,,AC-004
"Implement 10 interrogation dimension definitions",Story,P0,Plan Interview,"pipeline quality-gate stage-4.5",M,AIA-001,AC-001 AC-004
"Implement dimension scorer with configurable thresholds",Story,P0,Plan Interview,"pipeline quality-gate stage-4.5",M,AIA-001,AC-004 AC-005
"Implement interview gate logic",Story,P0,Plan Interview,"pipeline quality-gate stage-4.5",M,AIA-002 AIA-003,AC-002 AC-003
"Implement StageContext integration for Stage 4.5",Story,P0,Plan Interview,"pipeline quality-gate stage-4.5",M,AIA-004,AC-003
"Register MCP tools: plan_interview plan_score",Story,P1,Plan Interview,"pipeline quality-gate stage-4.5",S,AIA-004,AC-001
"Create Stage 4.5 SKILL.md (v3.0)",Story,P1,Plan Interview,"pipeline quality-gate stage-4.5",S,AIA-004,AC-001
"Update orchestrator stage ordering",Story,P0,Plan Interview,"pipeline quality-gate stage-4.5",S,AIA-004 AIA-005,AC-002
"Write STG-4.5 decision document",Story,P2,Plan Interview,"pipeline quality-gate stage-4.5",S,AIA-004,
"Full test suite for Plan Interview",Story,P0,Plan Interview,"pipeline quality-gate stage-4.5",M,AIA-001-AIA-008,AC-001-AC-005
"Implement PipelineState model",Story,P0,Memory Model,"data-layer persistence cloudkit memory",S,,AC-006
"Implement ExperiencePattern with decay",Story,P0,Memory Model,"data-layer persistence cloudkit memory",M,,AC-008 AC-009
"Implement AuditEvent immutable model",Story,P0,Memory Model,"data-layer persistence cloudkit memory",S,,AC-012 AC-013
"Define new ports (PipelineState Experience Audit)",Story,P0,Memory Model,"data-layer persistence cloudkit memory",S,AIA-011 AIA-012 AIA-013,
"CloudKit adapter for PipelineState",Story,P0,Memory Model,"data-layer persistence cloudkit memory",L,AIA-014,AC-006 AC-007
"CloudKit adapter for ExperiencePattern",Story,P0,Memory Model,"data-layer persistence cloudkit memory",L,AIA-014,AC-008
"CloudKit adapter for AuditEvent",Story,P0,Memory Model,"data-layer persistence cloudkit memory",M,AIA-014,AC-012
"Conflict resolution (last-writer-wins)",Story,P0,Memory Model,"data-layer persistence cloudkit memory",M,AIA-015,AC-007
"Progressive disclosure engine (L1/L2/L3)",Story,P1,Memory Model,"data-layer persistence cloudkit memory",L,AIA-011,AC-010
"Context budget monitor (70%/93%)",Story,P1,Memory Model,"data-layer persistence cloudkit memory",M,AIA-019,AC-010 AC-011
"Auto-HandoffDocument at 93%",Story,P1,Memory Model,"data-layer persistence cloudkit memory",M,AIA-020,AC-011
"Update composition root",Story,P0,Memory Model,"data-layer persistence cloudkit memory",S,AIA-015-AIA-017,
"Cross-device integration testing",Story,P0,Memory Model,"data-layer persistence cloudkit memory",L,AIA-015-AIA-018,AC-006 AC-007
"Full test suite for memory model",Story,P0,Memory Model,"data-layer persistence cloudkit memory",M,AIA-011-AIA-021,AC-006-AC-013
"Implement Bayesian Consensus",Story,P2,Consensus,"verification algorithm consensus",S,,AC-014 AC-015
"Implement Majority Voting",Story,P2,Consensus,"verification algorithm consensus",S,,AC-016 AC-017
"Integrate into ConsensusAlgorithm routing",Story,P2,Consensus,"verification algorithm consensus",S,AIA-025 AIA-026,AC-015 AC-017
"Create ALG-011 and ALG-012 docs",Story,P2,Consensus,"verification algorithm consensus",S,AIA-025 AIA-026,
"Tests with deterministic fixtures",Story,P2,Consensus,"verification algorithm consensus",S,AIA-025-AIA-027,AC-014-AC-017
"Define Survival Architecture v3.0 (ADR-009)",Story,P0,Hook System,"enforcement hooks security survival-v3",M,,
"Implement enforce-doc-read hook",Story,P0,Hook System,"enforcement hooks security survival-v3",M,,AC-018 AC-019
"Implement validate-output-schema hook",Story,P1,Hook System,"enforcement hooks security survival-v3",M,AIA-030,
"Implement security-tier-check hook",Story,P1,Hook System,"enforcement hooks security survival-v3",L,,AC-020 AC-021
"Implement update-pipeline-state hook",Story,P1,Hook System,"enforcement hooks security survival-v3",M,AIA-013,AC-012
"Implement SessionStart hook",Story,P1,Hook System,"enforcement hooks security survival-v3",S,AIA-011,AC-023
"Implement save-session-summary hook",Story,P1,Hook System,"enforcement hooks security survival-v3",S,,AC-022
"Update 12 SKILL.md files to v3.0",Story,P1,Hook System,"enforcement hooks security survival-v3",M,AIA-030,
"Full test suite for hooks",Story,P0,Hook System,"enforcement hooks security survival-v3",M,AIA-031-AIA-036,AC-018-AC-023
"GitHubActionsAdapter: GitOps",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,,AC-024
"GitHubActionsAdapter: FileSystemOps",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",S,,AC-024
"GitHubActionsAdapter: GitHubOps",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,,AC-025
"GitHubActionsAdapter: ContextOps",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,,AC-024
"Issue-triggered workflow YAML",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,AIA-039-AIA-042,AC-024 AC-025
"Nightly schedule workflow YAML",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,AIA-039-AIA-042,AC-026 AC-027
"PR-comment-triggered workflow YAML",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,AIA-039-AIA-042,
"Artifact collection",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,AIA-042,
"Status reporting (check runs)",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,AIA-041,AC-028 AC-029
"Secret management via Actions secrets",Story,P0,GitHub Actions,"ci-cd github-actions adapter headless",S,,
"ADR-010 + headless entrypoint",Story,P1,GitHub Actions,"ci-cd github-actions adapter headless",M,AIA-039-AIA-042,
"E2E test: issue to PR",Story,P0,GitHub Actions,"ci-cd github-actions adapter headless",L,AIA-043 AIA-047,AC-024 AC-025
"CLI entry point",Story,P1,Python Migration,"packaging pypi python migration",M,,AC-031
"TOML config loader",Story,P1,Python Migration,"packaging pypi python migration",M,,AC-032 AC-033
"PyPI pyproject.toml config",Story,P1,Python Migration,"packaging pypi python migration",S,,AC-030
"Verify 32 tools in package",Story,P0,Python Migration,"packaging pypi python migration",L,AIA-053,AC-031
"Verify verification algorithms in package",Story,P0,Python Migration,"packaging pypi python migration",M,AIA-053,
"Verify strategies + enhancements in package",Story,P0,Python Migration,"packaging pypi python migration",M,AIA-053,
"Verify 64 HOR rules in package",Story,P0,Python Migration,"packaging pypi python migration",M,AIA-053,
"Migration guide from Node.js",Story,P1,Python Migration,"packaging pypi python migration",M,AIA-054,AC-034
"Python API reference docs",Story,P1,Python Migration,"packaging pypi python migration",M,AIA-054,
"TestPyPI publish + cross-version test",Story,P1,Python Migration,"packaging pypi python migration",M,AIA-053-AIA-057,AC-030
"Production PyPI publish",Story,P0,Python Migration,"packaging pypi python migration",S,AIA-060,AC-030 AC-031
"MCP protocol compatibility check",Story,P1,Python Migration,"packaging pypi python migration",M,AIA-054,AC-035
```
