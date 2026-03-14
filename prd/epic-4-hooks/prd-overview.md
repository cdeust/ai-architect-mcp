# Epic 4: Hook System Expansion - Overview

**Status:** Implementation-level PRD
**Version:** 1.0
**Date:** 2026-03-14
**Epic ID:** E4
**Size:** M (27 SP / 3-4 weeks)

---

## Executive Summary

Epic 4 expands the AI Architect hook system from 2 hook types (pre-tool-use, post-tool-use) to 8 hook types, adding **6 new hooks** that enforce architectural contracts at runtime. This work introduces **Survival Architecture v3.0** (ADR-009), a refined skill template that codifies hook declarations, context budgets, and security tier classification.

The hook expansion creates a multi-layer runtime contract system:
1. **Document enforcement** — Prevent tool execution until documentation is read
2. **Security classification** — Real-time threat modeling on bash commands (10-tier model)
3. **Output validation** — Schema validation against SKILL.md contracts
4. **State management** — PipelineState + AuditEvent tracking across tool invocations
5. **Session lifecycle** — SessionStart + SessionEnd hooks for initialization and handoff

---

## Problem Statement

Current system limitations:
- **No doc verification**: Tools can execute without SKILL.md being read
- **No security pre-checks**: Bash commands classified post-execution only
- **No runtime contracts**: Output schemas not validated before stage completion
- **Fragmented state**: PipelineState updates scattered across tool execution
- **No session lifecycle**: No unified initialization or handoff logic
- **No audit trail**: Hard to reconstruct decision flows and architectural violations

Result: Architecture invariants cannot be enforced at runtime. Security decisions are made blind.

---

## Solution Overview

### Six New Hooks

| Hook | Type | Timing | Responsibility |
|------|------|--------|-----------------|
| **SessionStart** | Lifecycle | Session init | Load PipelineState, validate skill versions, check iCloud sync |
| **enforce-doc-read** | Pre-tool-use | Before tool | Block writes until SKILL.md read in current session |
| **validate-output-schema** | Post-tool-use | After tool | Verify stage output matches SKILL.md contract |
| **security-tier-check** | Pre-tool-use | Before bash | 10-tier threat model on bash commands |
| **update-pipeline-state** | Post-tool-use | After tool | Update PipelineState + log AuditEvent |
| **save-session-summary** | SessionEnd | Session close | Auto-write HandoffDocument |

### Survival Architecture v3.0 (ADR-009)

Evolution of SKILL.md template:

**New Sections:**
- **Hook Declarations** — List of hooks applicable to this skill (e.g., `enforce-doc-read`, `security-tier-check`)
- **Context Budget** — Token limits per stage, timeout thresholds
- **Security Tier** — Classification of skill's bash commands (1-10)
- **Output Schema** — JSON Schema defining expected stage outputs

**Backward Compatibility:**
- v2.2 SKILL.md files remain valid (hooks default-allow)
- v3.0 optional; SKILL.md without explicit hooks assume no enforcement
- Migration path: 12 existing SKILL.md files incrementally upgraded to v3.0

---

## 10-Tier Security Model

Applied by `security-tier-check` hook to classify bash commands:

| Tier | Category | Risk | Examples | Action |
|------|----------|------|----------|--------|
| **1** | Safe reads | None | `cat`, `ls`, `grep`, `head` | Allow |
| **2** | Environment | Low | `echo`, `pwd`, `env` | Allow |
| **3** | Package queries | Low | `pip list`, `npm ls`, `brew list` | Allow |
| **4** | Write/create | Moderate | `touch`, `mkdir`, `cp` | Allow + log |
| **5** | Publish | Moderate | `git push`, `npm publish`, `aws s3 cp` | Allow + log |
| **6** | Docker ops | High | `docker run`, `docker build` | Block + ask user |
| **7** | Permissions | High | `chmod 777`, `chown`, `sudo` | Block + ask user |
| **8** | Process kill | Very high | `kill -9`, `killall` | Block unconditionally |
| **9** | System files | Critical | `rm /etc/*`, `/usr/bin/*` | Block unconditionally |
| **10** | Destructive | Catastrophic | `rm -rf /`, `dd if=/dev/zero` | Block unconditionally |

Classification: Regex-based command analysis + tier lookup table.

---

## Architectural Fit

**Depends on:** Epic 2 (PipelineState, AuditEvent models)
**Enables:** Epic 5 (LLM-driven tool orchestration with security guardrails)

**Integration points:**
- Tool execution pipeline (hooks called before/after tool dispatch)
- SKILL.md parsing (extract Hook Declarations, Output Schema, Security Tier)
- Session state (PipelineState, AuditEvent in memory + iCloud sync)
- Audit logging (all hook violations + state changes)

---

## Deliverables

| File | Purpose | Audience |
|------|---------|----------|
| **prd-overview.md** | This document: problem, solution, model overview | Everyone |
| **prd-requirements.md** | Functional + non-functional requirements (FR-E4-001 to FR-E4-025) | PM, Eng, QA |
| **prd-user-stories.md** | 9 user stories, ACs, SP estimates (Fibonacci) | Eng, PM |
| **prd-technical.md** | Full technical spec, code examples, hook architecture | Eng |
| **prd-acceptance.md** | AC-E4-001 to AC-E4-030+, detailed validation criteria | QA, Eng |
| **prd-roadmap.md** | 4 sprints over 4-5 weeks, uneven SP distribution | PM, Eng |
| **prd-jira.md** | 9 JIRA tickets, SP, dependencies, CSV format | PM, Eng |
| **prd-tests.md** | Full pytest code: 5 test modules, fixture data, security tier JSON | Eng, QA |
| **prd-verification.md** | Structural checks, honest verdicts, cross-references | PM, Eng |

---

## Success Criteria

1. **Security enforcement**: All 10 tiers classified in <200ms; unsafe commands blocked before execution
2. **Doc read verification**: SKILL.md read forced before write operations; session state persists
3. **Contract validation**: 100% of stage outputs validated against schema; failures logged + reported
4. **State consistency**: PipelineState + AuditEvent synchronized across tool invocations; iCloud sync verified
5. **Backward compatibility**: All v2.2 SKILL.md files execute unchanged; optional v3.0 features non-breaking
6. **Audit trail**: All hook violations + security decisions + state changes logged in AuditEvent
7. **Test coverage**: ≥95% code coverage; all 10 security tiers tested with real-world commands

---

## Timeline

**Duration:** 3-4 weeks
**Team:** 2-3 engineers
**Sprints:** 4 (1-week iterations)

See **prd-roadmap.md** for detailed sprint breakdown.

---

## Dependencies & Risks

**Hard dependencies:**
- Epic 2 delivered and stabilized (PipelineState, AuditEvent models)
- SKILL.md v2.2 parsing working (baseline for v3.0 upgrade)

**Risks:**
- **Security tier classification**: Regex-based approach may miss edge cases (mitigation: comprehensive fixture data, user override flow)
- **Performance**: Hook latency >500ms kills UX (mitigation: async hooks, caching)
- **SKILL.md migration**: 12 files to upgrade (mitigation: automatic v3.0 generation from v2.2 + manual review)

---

## Glossary

| Term | Definition |
|------|-----------|
| **Hook** | Executable (script or module) triggered at defined points in tool execution |
| **Survival Architecture** | SKILL.md template defining skill metadata, contracts, and runtime enforcement |
| **ADR** | Architecture Decision Record |
| **PipelineState** | In-memory state tracking tool execution, stage completion, decisions |
| **AuditEvent** | Immutable log entry: timestamp, actor, action, result, context |
| **Hook Declaration** | Section in SKILL.md listing hooks applicable to this skill |
| **Context Budget** | Token limits per stage, timeout thresholds |
| **Output Schema** | JSON Schema defining expected stage output structure |
| **Security Tier** | Classification 1-10 of command risk level |

---

## Next Steps

1. **Review & approve** this PRD
2. **Create JIRA tickets** (9 total) from prd-jira.md
3. **Sprint planning** using prd-roadmap.md
4. **Development kickoff** with prd-technical.md
5. **QA prep** using prd-tests.md + prd-acceptance.md

---

**Owner:** AI Architect Product Team
**Last Updated:** 2026-03-14
