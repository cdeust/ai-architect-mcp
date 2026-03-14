# PRD Implementation Roadmap — AI Architect Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**PRD Type:** Full Scope Overview
**Delivery Model:** Solo developer (Clément) + AI Architect pipeline (hybrid velocity)
**Timeline:** Q2–Q4 2026 (phased across 3 quarters)

---

## 1. Roadmap Overview

```
Q2 2026 (Apr–Jun)          Q3 2026 (Jul–Sep)          Q4 2026 (Oct–Dec)
━━━━━━━━━━━━━━━━━━━━━━━   ━━━━━━━━━━━━━━━━━━━━━━━   ━━━━━━━━━━━━━━━━━━━━━━━

[E3: Consensus ████ S ]

[E1: Plan Interview ████████████████ L     ]

[E2: Memory Model ████████████████████████████ XL    ─┐
                                              ████]   │
                                                      │
                   [E4: Hooks ████████ M ]←────────────┘
                                      │
                          [E5: GHA ████████████████ L ]
                                                   │
                                      [E6: Python ████████████████████████ XL ]
```

---

## 2. Phase 1: Foundation (Q2 2026 — April to June)

**Objective:** Build the core missing components that have no dependencies.

### Sprint 0: Prototyping (Weeks 1–2, April 1–14)

| Activity | Epic | Purpose |
|----------|------|---------|
| CloudKit sync prototype | Epic 2 | Validate A-001 (CloudKit works for SwiftData models) |
| v3.0 template draft | Epic 4 | Define ADR-009 before implementation begins |
| Test baseline measurement | All | Establish current test coverage metrics |

### Parallel Track A: Consensus Completion (Weeks 1–3)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1 | Bayesian Consensus implementation | `bayesian_consensus.py` + tests |
| 2 | Majority Voting implementation | `majority_voting.py` + tests |
| 3 | Integration + ALG docs | ALG-011, ALG-012 decision documents |

**Epic 3 Size:** S (1–2 weeks active work)
**Epic 3 Done:** End of April

### Parallel Track B: Plan Interview (Weeks 1–10)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1–2 | Architecture + dimension definitions | `_interview/dimensions.py`, `models.py` |
| 3–4 | Scorer + first 5 dimensions implemented | `scorer.py`, dimension evaluators |
| 5–6 | Remaining 5 dimensions | All 10 dimensions operational |
| 7–8 | Gate logic + MCP tools | `interview_engine.py`, `interview_tools.py` |
| 9 | SKILL.md (v3.0 template) + integration | Stage ordering in orchestrator |
| 10 | Testing + documentation | STG-4.5 decision document, full test suite |

**Epic 1 Size:** L (5–8 weeks active work, spread across 10 calendar weeks)
**Epic 1 Done:** Mid-June

### Parallel Track C: Memory Model Start (Weeks 1–12+)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1–2 | Sprint 0 prototype (CloudKit) | Prototype validates A-001 |
| 3–4 | PipelineState model + local persistence | `pipeline_state.py`, adapter |
| 5–6 | ExperiencePattern model + decay algorithm | `experience_pattern.py`, tests |
| 7–8 | AuditEvent model + immutability enforcement | `audit_event.py`, append-only store |
| 9–10 | CloudKit sync adapter for all 3 models | CloudKit adapters, sync tests |
| 11–12 | Progressive disclosure engine | `progressive_disclosure.py`, budget monitor |

**Epic 2 Size:** XL (9–12 weeks, continues into Q3)
**Epic 2 Done:** Mid-July (continues into Phase 2)

### Phase 1 Exit Criteria

- [ ] Bayesian Consensus + Majority Voting algorithms passing all tests
- [ ] Plan Interview stage operational with all 10 dimensions
- [ ] PipelineState, ExperiencePattern, AuditEvent models implemented
- [ ] CloudKit sync prototype validated
- [ ] Survival Architecture v3.0 template defined (ADR-009)

---

## 3. Phase 2: Enforcement (Q3 2026 — July to September)

**Objective:** Complete memory model, implement hook enforcement, start GitHub Actions.

### Memory Model Finalization (Weeks 1–4, July)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1 | Complete CloudKit sync for all models | Cross-device testing |
| 2 | Progressive disclosure + budget monitor | Full context management |
| 3 | Integration testing | Multi-layer memory e2e tests |
| 4 | Documentation + handoff | Decision documents updated |

**Epic 2 Done:** End of July

### Hook System (Weeks 3–8, July–August)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 3–4 | enforce-doc-read + validate-output-schema | 2 hooks operational |
| 5–6 | security-tier-check (10-tier model) | Tier classification + blocking |
| 7 | update-pipeline-state + save-session-summary + SessionStart | 3 remaining hooks |
| 8 | ADR-009 finalized + all stage SKILL.md updated to v3.0 | Architecture evolution complete |

**Epic 4 Size:** M (3–4 weeks active work)
**Epic 4 Done:** End of August

### GitHub Actions Start (Weeks 7–12+, August–September)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 7–8 | GitHubActionsAdapter: Git + FileSystem ports | Basic headless execution |
| 9–10 | Issue-triggered workflow + artifact collection | `ai-architect-pipeline.yml` |
| 11–12 | Nightly workflow + PR-comment workflow | 2 additional workflow templates |

**Epic 5 Size:** L (continues into Q4)
**Epic 5 Done:** Mid-October (continues into Phase 3)

### Phase 2 Exit Criteria

- [ ] Four-layer memory model complete with CloudKit sync
- [ ] All 6 hooks operational and tested
- [ ] Survival Architecture v3.0 adopted across all 12 stage SKILL.md files
- [ ] GitHub Actions adapter passing basic pipeline execution

---

## 4. Phase 3: Ecosystem (Q4 2026 — October to December)

**Objective:** Complete GitHub Actions, publish Python package.

### GitHub Actions Finalization (Weeks 1–4, October)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1–2 | Status reporting (check runs) + secret management | Full CI/CD integration |
| 3 | End-to-end testing: issue → PR | Automated pipeline validation |
| 4 | Documentation: ADR-010, usage guide | GitHub Actions ready for users |

**Epic 5 Done:** End of October

### Python Package Migration (Weeks 3–14, October–December)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 3–4 | CLI entry point + TOML config loader | `__main__.py`, `_config/loader.py` |
| 5–6 | Package structure + PyPI metadata | `pyproject.toml` for publishing |
| 7–8 | All 32 tools verified in package context | Tool registration tests |
| 9–10 | All algorithms + HOR rules verified | Algorithm test suite in package |
| 11–12 | Migration guide + API reference docs | `migration-from-nodejs.md` |
| 13 | PyPI test publish (TestPyPI) | Test install validation |
| 14 | PyPI production publish | `pip install ai-architect-mcp` works |

**Epic 6 Size:** XL (9–12 weeks)
**Epic 6 Done:** End of December

### Phase 3 Exit Criteria

- [ ] GitHub Actions: issue → PR automated pipeline validated
- [ ] `ai-architect-mcp` published on PyPI
- [ ] `pip install ai-architect-mcp && ai-architect-mcp serve` starts server
- [ ] Migration guide tested by at least 1 external user
- [ ] All 6 epics marked complete

---

## 5. Milestone Summary

| Milestone | Target Date | Epic(s) | Deliverable |
|-----------|-------------|---------|-------------|
| M1: Sprint 0 Complete | April 14, 2026 | All | CloudKit prototype validated, v3.0 template drafted |
| M2: Consensus Complete | April 30, 2026 | Epic 3 | 2 algorithms implemented + tested |
| M3: Plan Interview Complete | June 15, 2026 | Epic 1 | Stage 4.5 operational |
| M4: Memory Model Complete | July 31, 2026 | Epic 2 | Four-layer memory with CloudKit sync |
| M5: Hook System Complete | August 31, 2026 | Epic 4 | 6 hooks + v3.0 adoption |
| M6: GitHub Actions Complete | October 31, 2026 | Epic 5 | Headless CI/CD pipeline |
| M7: Python Package Published | December 15, 2026 | Epic 6 | PyPI release |
| M8: All Gaps Closed | December 31, 2026 | All | 0 documented implementation gaps |

---

## 6. T-Shirt Size to Calendar Duration

| Epic | T-Shirt | Active Weeks | Calendar Weeks | Buffer | Phase |
|------|---------|-------------|----------------|--------|-------|
| Epic 3: Consensus | S | 2 | 3 | 1 week | Phase 1 |
| Epic 1: Plan Interview | L | 7 | 10 | 3 weeks | Phase 1 |
| Epic 2: Memory Model | XL | 10 | 16 | 6 weeks | Phase 1–2 |
| Epic 4: Hooks | M | 4 | 6 | 2 weeks | Phase 2 |
| Epic 5: GitHub Actions | L | 7 | 12 | 5 weeks | Phase 2–3 |
| Epic 6: Python Migration | XL | 10 | 12 | 2 weeks | Phase 3 |
| **Totals** | — | **40** | **~39 calendar** | — | Q2–Q4 |

**Note:** Active weeks overlap due to parallel execution. Calendar weeks account for context switching between tracks (~30% overhead for solo developer + AI assistance).

---

## 7. Risk-Adjusted Timeline

| Risk | Impact on Timeline | Mitigation |
|------|-------------------|------------|
| CloudKit prototype fails (A-001) | +4 weeks to Epic 2 | Start Sprint 0 early, have local-only fallback |
| Security tier model too restrictive (R-002) | +1 week to Epic 4 | Start permissive, tighten iteratively |
| GitHub Actions runner limitations (R-004) | +2 weeks to Epic 5 | Implement stage checkpointing |
| Python packaging conflicts (R-003) | +1 week to Epic 6 | Test across multiple Python versions in CI |

**Best Case:** All epics complete by November 2026
**Expected Case:** All epics complete by December 2026
**Worst Case:** Epics 1–5 complete by December 2026, Epic 6 slips to January 2027
