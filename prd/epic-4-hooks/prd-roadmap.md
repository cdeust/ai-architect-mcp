# Epic 4: Hook System Expansion - Roadmap

**Document:** prd-roadmap.md
**Version:** 1.0
**Date:** 2026-03-14
**Duration:** 4 weeks (4 sprints)
**Total SP:** 27

---

## Overview

This roadmap breaks down Epic 4 into 4 weekly sprints with uneven story point (SP) distribution. Sprint velocity varies 5-9 SP per sprint to account for setup work, testing, and integration complexity.

---

## Sprint Schedule

| Sprint | Dates | Focus | SP | Stories |
|--------|-------|-------|----|----|
| **Sprint 1** | W1 (3 weeks in) | Foundation + templates | 5 | E4-001, E4-006 |
| **Sprint 2** | W2 | Doc enforcement + security model | 9 | E4-002, E4-004 (part 1) |
| **Sprint 3** | W3 | Security completion + state management | 8 | E4-004 (part 2), E4-005, E4-003 |
| **Sprint 4** | W4 | Session lifecycle + migration + testing | 5 | E4-007, E4-008, E4-009 |

---

## Sprint 1: Foundation & Templates (5 SP)

**Week:** March 17-21, 2026
**Goal:** Establish v3.0 template, ADR, and session infrastructure
**Dependencies:** Epic 2 completed

### Stories & Tasks

#### STORY-E4-001: ADR-009 Survival v3.0 (3 SP)

**Week 1 Breakdown:**
- **Day 1-2:** ADR-009 document draft + template design (1.5 SP)
  - [ ] Write ADR-009 markdown (architecture, rationale, examples)
  - [ ] Design v3.0 template structure (new sections)
  - [ ] Document backward compatibility guarantees

- **Day 3-5:** SKILL.md parser updates + template file (1.5 SP)
  - [ ] Update parser to read v3.0 fields (hooks-declared, context-budget, security-tier, output-schema)
  - [ ] Create `templates/skill-template-v3.0.md`
  - [ ] Parser tests: v2.2 + v3.0 compatibility
  - [ ] ADR approval by architecture team

**AC Verification:**
- AC-E4-001: v3.0 template defined in ADR-009
- AC-E4-002: Parser updated
- AC-E4-003: Template file created
- AC-E4-004: Migration plan documented

**Deliverables:**
- `adr/adr-009.md` (ADR document)
- `templates/skill-template-v3.0.md` (template file)
- Parser updates in `skills/parser.py`
- Migration plan document

---

#### STORY-E4-006: SessionStart Hook (2 SP)

**Week 1 Breakdown:**
- **Day 3-5:** SessionStart implementation + tests (2 SP)
  - [ ] Implement `hooks/session_start/session_start_hook.py`
  - [ ] Load PipelineState from iCloud with retry logic
  - [ ] Validate SKILL.md versions
  - [ ] Initialize doc_read_tracker
  - [ ] Unit tests + error handling

**AC Verification:**
- AC-E4-005: SessionStart initialization
- AC-E4-006: Error handling
- AC-E4-007: iCloud sync check
- AC-E4-008: AuditEvent log initialization

**Deliverables:**
- `hooks/session_start/session_start_hook.py`
- Unit tests: `tests/test_session_hooks.py` (SessionStart suite)
- Integration tests: session state initialization

---

### Sprint 1 Review

**Completion Criteria:**
- [ ] ADR-009 approved by architecture team
- [ ] v3.0 parser working with both v2.2 + v3.0 SKILL.md
- [ ] SessionStart hook initialized + tested
- [ ] doc_read_tracker working end-to-end
- [ ] Sprint retrospective: identify blockers

---

## Sprint 2: Doc Enforcement & Security Model Pt.1 (9 SP)

**Week:** March 24-28, 2026
**Goal:** Implement enforce-doc-read hook + security tier classification (Tiers 1-7)
**Dependencies:** Sprint 1 completed

### Stories & Tasks

#### STORY-E4-002: enforce-doc-read Hook (3 SP)

**Week 2 Breakdown:**
- **Day 1-3:** enforce-doc-read implementation (2 SP)
  - [ ] Implement `hooks/pre_tool_use/enforce_doc_read.py`
  - [ ] Load + format SKILL.md for display
  - [ ] Session state tracking (doc_read_tracker)
  - [ ] User override flow (prompt + confirm)
  - [ ] Latency optimization (<100ms)

- **Day 4-5:** Testing + user override flow (1 SP)
  - [ ] Unit tests: block/allow logic
  - [ ] User override tests
  - [ ] Session state persistence tests
  - [ ] SKILL.md formatting tests

**AC Verification:**
- AC-E4-001: Hook blocks unread SKILL.md
- AC-E4-002: User override flow
- AC-E4-003: Session state tracking
- AC-E4-004: SKILL.md formatting

**Deliverables:**
- `hooks/pre_tool_use/enforce_doc_read.py`
- Tests: `tests/test_enforce_doc_read.py`

---

#### STORY-E4-004: security-tier-check Hook Pt.1 (6 SP)

**Week 2 Breakdown:**
- **Day 1-3:** Security model + tiers 1-7 (4 SP)
  - [ ] Define SECURITY_TIERS config (JSON)
  - [ ] Implement `security_classifier.py` (regex patterns + lookup)
  - [ ] Classify tiers 1-5: allow / allow+log
  - [ ] Classify tiers 6-7: block+ask
  - [ ] Regex compilation + caching
  - [ ] Command parsing (binary extraction)

- **Day 4-5:** Tiers 1-7 testing + edge cases (2 SP)
  - [ ] Test fixtures: 20+ command examples
  - [ ] Test tiers 1-5 (safe + moderate)
  - [ ] Test tiers 6-7 (block+ask)
  - [ ] Edge cases: pipes, redirects, quotes
  - [ ] Latency benchmark (<200ms)

**AC Verification:**
- AC-E4-009: Hook activates
- AC-E4-010: Tier 1 classification
- AC-E4-011: Tier 2 classification
- AC-E4-012: Tier 3 classification
- AC-E4-013: Tiers 4-5 allow+log
- AC-E4-014: Tiers 6-7 block+ask
- AC-E4-016: Latency <200ms
- AC-E4-017: Classification accuracy
- AC-E4-018: Edge cases

**Deliverables:**
- `hooks/pre_tool_use/security_tier_check.py`
- `security_classifier.py` (CommandClassifier)
- `config/security_tiers.json`
- Tests: `tests/test_security_tier.py` (partial)
- Fixture: `tests/fixtures/security_tiers.json` (20 commands)

---

### Sprint 2 Review

**Completion Criteria:**
- [ ] enforce-doc-read hook fully functional + tested
- [ ] security-tier-check implemented for tiers 1-7
- [ ] Command parsing working with edge cases
- [ ] Latency targets met (<200ms for security-tier-check)
- [ ] Sprint retrospective

---

## Sprint 3: Security Completion & Output Validation (8 SP)

**Week:** March 31 - April 4, 2026
**Goal:** Complete security model (tiers 8-10) + implement schema validation + state tracking
**Dependencies:** Sprint 2 completed

### Stories & Tasks

#### STORY-E4-004: security-tier-check Pt.2 (2 SP)

**Week 3 Breakdown:**
- **Day 1-2:** Tiers 8-10 + user override (1.5 SP)
  - [ ] Classify tiers 8-10: block unconditionally
  - [ ] User override suppression for tier 8-10
  - [ ] Test fixtures: 10 destructive commands
  - [ ] Security review: tier classification accuracy

- **Day 3:** Complete test coverage (0.5 SP)
  - [ ] Test tiers 8-10 (kill, system files, destructive)
  - [ ] Final security tier latency benchmark
  - [ ] 30+ command examples verified

**AC Verification:**
- AC-E4-015: Tiers 8-10 block unconditionally
- AC-E4-016: Latency <200ms (final verification)
- AC-E4-017: Classification accuracy (30+ commands)

**Deliverables:**
- Updated `security_tier_check.py` (tiers 8-10)
- Tests: `tests/test_security_tier.py` (complete)
- Fixture: `tests/fixtures/security_tiers.json` (30 commands)

---

#### STORY-E4-003: validate-output-schema Hook (3 SP)

**Week 3 Breakdown:**
- **Day 2-4:** Schema validation implementation (2 SP)
  - [ ] Implement `hooks/post_tool_use/validate_output_schema.py`
  - [ ] JSON schema validation (Draft 7)
  - [ ] YAML + text format support
  - [ ] Blocking vs warning modes (enforce-schema flag)
  - [ ] Error message formatting
  - [ ] Latency optimization (<300ms)

- **Day 5:** Testing + SKILL.md integration (1 SP)
  - [ ] Unit tests: type checking, required fields, nested objects
  - [ ] Pattern + enum validation tests
  - [ ] Blocking vs warning mode tests
  - [ ] Integration with SKILL.md output-schema

**AC Verification:**
- AC-E4-019: Hook activation
- AC-E4-020: Type checking
- AC-E4-021: Required fields
- AC-E4-022: Nested objects + arrays
- AC-E4-023: Pattern + enum
- AC-E4-024: Blocking vs warning
- AC-E4-025: Integration
- AC-E4-026: SKILL.md config
- AC-E4-027: Error messages
- AC-E4-028: Format support

**Deliverables:**
- `hooks/post_tool_use/validate_output_schema.py`
- Tests: `tests/test_validate_schema.py`

---

#### STORY-E4-005: update-pipeline-state Hook (3 SP)

**Week 3 Breakdown:**
- **Day 1-4:** State tracking + audit logging (2.5 SP)
  - [ ] Implement `hooks/post_tool_use/update_pipeline_state.py`
  - [ ] Update PipelineState fields (last_tool_executed, etc.)
  - [ ] Create AuditEvent entries
  - [ ] Persist to memory + iCloud
  - [ ] iCloud sync with retry logic (exponential backoff, max 3 retries)
  - [ ] Fallback to local storage if unavailable

- **Day 5:** Testing + state verification (0.5 SP)
  - [ ] Unit tests: state field updates
  - [ ] AuditEvent creation + logging
  - [ ] iCloud sync + retry tests
  - [ ] Latency <150ms

**AC Verification:**
- AC-E4-029: PipelineState fields updated
- AC-E4-030: AuditEvent creation + persistence

**Deliverables:**
- `hooks/post_tool_use/update_pipeline_state.py`
- Tests: `tests/test_update_state.py`

---

### Sprint 3 Review

**Completion Criteria:**
- [ ] All 10 tiers of security model complete + tested
- [ ] Schema validation hook fully functional
- [ ] State tracking + AuditEvent logging working
- [ ] iCloud sync + fallback tested
- [ ] Latency targets met for all hooks
- [ ] Sprint retrospective

---

## Sprint 4: Session Lifecycle & Migration & Testing (5 SP)

**Week:** April 7-11, 2026
**Goal:** Session lifecycle hooks + SKILL.md migration + comprehensive test suite
**Dependencies:** Sprints 1-3 completed

### Stories & Tasks

#### STORY-E4-007: save-session-summary Hook (2 SP)

**Week 4 Breakdown:**
- **Day 1-2:** HandoffDocument generation + persistence (1.5 SP)
  - [ ] Implement `hooks/session_end/save_session_summary.py`
  - [ ] Generate HandoffDocument from AuditEvents
  - [ ] Format: session metadata, tool summary, state snapshot, security events, audit trail
  - [ ] Write to `sessions/{session_id}/handoff.md`
  - [ ] Compress + upload to iCloud

- **Day 3:** Testing + artifact verification (0.5 SP)
  - [ ] Unit tests: handoff generation
  - [ ] iCloud upload tests
  - [ ] Manual review: handoff content quality
  - [ ] Integration: full session lifecycle (start → tools → end)

**AC Verification:**
- AC-E4-031: HandoffDocument generation
- AC-E4-032: Artifact persistence

**Deliverables:**
- `hooks/session_end/save_session_summary.py`
- Tests: `tests/test_session_hooks.py` (SessionEnd suite)

---

#### STORY-E4-008: Migrate 12 SKILL.md Files to v3.0 (3 SP)

**Week 4 Breakdown:**
- **Day 1-2:** Automated upgrade + manual review (2 SP)
  - [ ] Run `./scripts/upgrade-skill-v2-to-v3.py` on all 12 SKILL.md files
  - [ ] Manual review of each upgrade:
    - Classify security tier (1-10)
    - Add hook declarations
    - Define output schema (if applicable)
    - Set context budget
  - [ ] Generate upgrade report

- **Day 3:** Backward compatibility testing (1 SP)
  - [ ] Test all 12 v2.2 SKILL.md files (pre-upgrade)
  - [ ] Test all 12 v3.0 SKILL.md files (post-upgrade)
  - [ ] Verify behavior unchanged
  - [ ] Regression test results

**AC Verification:**
- AC-E4-036: Migration script
- AC-E4-039: Backward compatibility

**Deliverables:**
- Updated: `skills/*/SKILL.md` (12 files)
- `scripts/upgrade-skill-v2-to-v3.py` (upgrade script)
- Upgrade report: `docs/upgrade-report.md`
- Tests: `tests/test_compatibility.py`

---

#### STORY-E4-009: Comprehensive Test Suite (5 SP - partial)

**Week 4 Breakdown:**
- **Day 1-5:** Full test suite finalization (1 SP final push)
  - [ ] Consolidate all test modules (5 total)
  - [ ] Verify 95%+ code coverage
  - [ ] Final latency benchmarks
  - [ ] CI/CD integration
  - [ ] Test documentation + fixtures

  *Note: Most testing done across sprints 1-4; Sprint 4 is final verification*

**AC Verification:**
- AC-E4-040: Test coverage ≥95%
- AC-E4-041: Test suite <60s execution

**Deliverables:**
- Complete: `tests/test_*.py` (5 modules)
- `tests/fixtures/` (all fixture data)
- Coverage report: `htmlcov/index.html`
- CI/CD: GitHub Actions workflow

---

### Sprint 4 Review & Epic Completion

**Completion Criteria:**
- [ ] save-session-summary hook functional + tested
- [ ] All 12 SKILL.md files upgraded to v3.0
- [ ] Backward compatibility verified
- [ ] Full test suite passing with 95%+ coverage
- [ ] All latency targets met
- [ ] All ACs verified
- [ ] Epic retrospective
- [ ] Release readiness

---

## Cumulative Progress

| Sprint | SP | Cumulative | % Complete |
|--------|----|----|------------|
| 1 | 5 | 5 | 19% |
| 2 | 9 | 14 | 52% |
| 3 | 8 | 22 | 81% |
| 4 | 5 | 27 | 100% |

---

## Dependencies & Risks

### Hard Dependencies

- **Epic 2:** PipelineState, AuditEvent models must be delivered + stable
- **Hook Infrastructure:** Hook registry, HookContext, HookResult classes
- **SKILL.md v2.2 Parser:** Must be working for baseline

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Epic 2 delays | Blocks entire epic | Daily sync; fallback to mock models if needed |
| Security tier edge cases | Misclassifications | 30+ command fixture tests; security review |
| iCloud sync unreliability | State loss | Local fallback; comprehensive error handling |
| SKILL.md migration issues | 12 files need manual review | Automated upgrade script; lightweight review process |
| Hook latency >500ms | Poor UX | Caching strategy; async/await support; benchmarking |

---

## Resource Allocation

**Recommended Team:**
- **2-3 engineers** total
- **1 QA engineer** (sprints 2-4)
- **1 security reviewer** (sprint 2)
- **Partial architecture review** (sprint 1)

**Time Commitment:**
- Sprint 1: 5 SP (one engineer, part-time support)
- Sprint 2: 9 SP (two engineers, full-time)
- Sprint 3: 8 SP (two engineers, full-time)
- Sprint 4: 5 SP (one-two engineers, final push)

---

## Definition of Done (DoD)

Each story is done when:
1. All acceptance criteria met
2. Code reviewed + approved
3. ≥95% test coverage
4. Latency targets verified
5. Documentation complete
6. ACs verified by QA
7. No open blockers

---

**Owner:** Product Manager
**Last Updated:** 2026-03-14
**Version:** 1.0
