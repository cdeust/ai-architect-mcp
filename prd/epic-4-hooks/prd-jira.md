# Epic 4: Hook System Expansion - JIRA Tickets

**Document:** prd-jira.md
**Version:** 1.0
**Date:** 2026-03-14

---

## Overview

This document defines 9 JIRA tickets corresponding to the 9 user stories in Epic 4. Each ticket includes story points, acceptance criteria references, dependencies, and CSV format for bulk import.

---

## Ticket Definitions

### TASK-E4-001: ADR-009 Survival Architecture v3.0 Template

**Story:** STORY-E4-001
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 3
**Assignee:** TBD
**Sprint:** Sprint 1 (Week 1)

**Description:**

Define and document Survival Architecture v3.0 (ADR-009) with new SKILL.md sections for hook declarations, context budgets, security tiers, and output schemas. Update SKILL.md parser to support v3.0 fields while maintaining v2.2 backward compatibility.

**Acceptance Criteria:**

- AC-E4-001: v3.0 template defined in ADR-009 with new sections
- AC-E4-002: SKILL.md parser updated to support v3.0 sections
- AC-E4-003: v3.0 default template file created
- AC-E4-004: Migration plan documented

**Tasks:**

1. Write ADR-009 document (architecture rationale, examples)
2. Design v3.0 template structure with all new sections
3. Update `skills/parser.py` to parse v3.0 fields
4. Create `templates/skill-template-v3.0.md` with inline documentation
5. Document migration plan from v2.2 to v3.0
6. Write parser tests (v2.2 + v3.0 compatibility)
7. Architecture team review + approval

**Related Links:**

- [prd-user-stories.md#STORY-E4-001](prd-user-stories.md#story-story-e4-001-adr-009-survival-architecture-v30-template)
- [prd-requirements.md#FR-E4-011](prd-requirements.md#fr-e4-011-survival-architecture-v30-template)
- [prd-technical.md#5.1](prd-technical.md#51-v30-template-structure)

**Dependencies:**

- None (foundational)

**Blocks:**

- TASK-E4-002 (enforce-doc-read)
- TASK-E4-003 (validate-output-schema)
- TASK-E4-004 (security-tier-check)
- TASK-E4-008 (migrate 12 SKILL.md)

---

### TASK-E4-002: enforce-doc-read Hook Implementation

**Story:** STORY-E4-002
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 3
**Assignee:** TBD
**Sprint:** Sprint 2 (Week 2)

**Description:**

Implement the enforce-doc-read pre-tool-use hook to block tool execution until SKILL.md has been read in the current session. Track reading state in session.doc_read_tracker. Support user override with confirmation.

**Acceptance Criteria:**

- AC-E4-001: enforce-doc-read hook blocks unread SKILL.md
- AC-E4-002: User override flow implemented
- AC-E4-003: Session state persists across tool executions
- AC-E4-004: SKILL.md formatting and display

**Tasks:**

1. Implement `hooks/pre_tool_use/enforce_doc_read.py`
2. Load + format SKILL.md for terminal display
3. Track reading state in session.doc_read_tracker
4. Implement user override flow (prompt + confirm)
5. Latency optimization (<100ms)
6. Unit tests: block/allow/override flows
7. Session state persistence tests
8. Integration tests with SessionStart

**Related Links:**

- [prd-user-stories.md#STORY-E4-002](prd-user-stories.md#story-story-e4-002-enforce-doc-read-hook-implementation)
- [prd-requirements.md#FR-E4-002](prd-requirements.md#fr-e4-002-enforce-doc-read-hook-activation)
- [prd-technical.md#4.2](prd-technical.md#42-hook-2-enforce-doc-read)

**Dependencies:**

- TASK-E4-001 (ADR-009 + v3.0 template)
- TASK-E4-006 (SessionStart hook + doc_read_tracker init)

**Blocks:**

- TASK-E4-009 (test suite integration)

---

### TASK-E4-003: validate-output-schema Hook Implementation

**Story:** STORY-E4-003
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 3
**Assignee:** TBD
**Sprint:** Sprint 3 (Week 3)

**Description:**

Implement the validate-output-schema post-tool-use hook to validate stage output against JSON Schema declared in SKILL.md. Support blocking vs warning modes. Validate JSON, YAML, and plain text formats.

**Acceptance Criteria:**

- AC-E4-019: validate-output-schema hook activation
- AC-E4-020: Type checking
- AC-E4-021: Required fields
- AC-E4-022: Nested objects + arrays
- AC-E4-023: Pattern + enum validation
- AC-E4-024: Blocking vs warning modes
- AC-E4-025: Integration with stage output
- AC-E4-026: Output schema configuration in SKILL.md
- AC-E4-027: Error message formatting
- AC-E4-028: Support for different output formats

**Tasks:**

1. Implement `hooks/post_tool_use/validate_output_schema.py`
2. JSON schema validation (Draft 7) using jsonschema library
3. Type checking (string, int, object, array, boolean, number)
4. Required field validation
5. Nested object + array validation
6. Pattern + enum validation
7. YAML + text format support
8. Blocking vs warning mode (enforce-schema flag)
9. Error message formatting with paths
10. Latency optimization (<300ms)
11. Comprehensive unit tests (all validation features)
12. Integration with SKILL.md output-schema parsing

**Related Links:**

- [prd-user-stories.md#STORY-E4-003](prd-user-stories.md#story-story-e4-003-validate-output-schema-hook-implementation)
- [prd-requirements.md#FR-E4-006](prd-requirements.md#fr-e4-006-validate-output-schema-hook-activation)
- [prd-technical.md#4.3](prd-technical.md#43-hook-3-validate-output-schema)

**Dependencies:**

- TASK-E4-001 (ADR-009 + output-schema section)
- TASK-E4-005 (update-pipeline-state + AuditEvent logging)

**Blocks:**

- TASK-E4-009 (test suite integration)

---

### TASK-E4-004: security-tier-check Hook with 10-Tier Model

**Story:** STORY-E4-004
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 5
**Assignee:** TBD
**Sprint:** Sprint 2 (Week 2) + Sprint 3 (Week 3)

**Description:**

Implement the security-tier-check pre-tool-use hook with comprehensive 10-tier security classification model. Parse bash commands, classify by threat level, and decide: allow, allow+log, block+ask, or block unconditionally. Test with 30+ real-world commands.

**Acceptance Criteria:**

- AC-E4-009: Hook activates before bash execution
- AC-E4-010: Tier 1 (safe reads) classification
- AC-E4-011: Tier 2 (environment) classification
- AC-E4-012: Tier 3 (package queries) classification
- AC-E4-013: Tiers 4-5 (write/publish) allow+log
- AC-E4-014: Tiers 6-7 (docker/permissions) block+ask
- AC-E4-015: Tiers 8-10 (process kill/system/destructive) block unconditionally
- AC-E4-016: Latency <200ms (p95)
- AC-E4-017: Classification accuracy (30+ commands)
- AC-E4-018: Edge case handling (pipes, redirects, quotes)

**Tasks:**

1. Define SECURITY_TIERS config with all 10 tiers (JSON)
2. Implement `security_classifier.py` CommandClassifier class
3. Regex patterns for command parsing + tier classification
4. Compile + cache regex patterns at startup
5. Binary extraction from full command
6. Support Tier 1-5: allow / allow+log verdicts
7. Support Tier 6-7: block+ask with user override
8. Support Tier 8-10: block unconditionally (no override)
9. Implement `hooks/pre_tool_use/security_tier_check.py`
10. Command parsing with edge cases (pipes, redirects, shells, aliases)
11. Comprehensive test fixtures (30+ command examples)
12. Test all 10 tiers with real-world commands
13. Latency benchmark (<200ms p95)
14. Security team review + approval

**Related Links:**

- [prd-user-stories.md#STORY-E4-004](prd-user-stories.md#story-story-e4-004-security-tier-check-hook-with-10-tier-model)
- [prd-requirements.md#FR-E4-004](prd-requirements.md#fr-e4-004-security-tier-check-hook-activation)
- [prd-requirements.md#FR-E4-005](prd-requirements.md#fr-e4-005-10-tier-security-classification-model)
- [prd-technical.md#3](prd-technical.md#3-security-tier-classifier)

**Dependencies:**

- TASK-E4-006 (SessionStart hook + hook infrastructure)

**Blocks:**

- TASK-E4-009 (test suite integration)

---

### TASK-E4-005: update-pipeline-state Hook Implementation

**Story:** STORY-E4-005
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 3
**Assignee:** TBD
**Sprint:** Sprint 3 (Week 3)

**Description:**

Implement the update-pipeline-state post-tool-use hook to update PipelineState after tool execution and create AuditEvent entries. Persist state to memory + iCloud with retry logic and fallback.

**Acceptance Criteria:**

- AC-E4-029: PipelineState fields updated
- AC-E4-030: AuditEvent creation + logging

**Tasks:**

1. Implement `hooks/post_tool_use/update_pipeline_state.py`
2. Update PipelineState fields: last_tool_executed, last_stage_completed, tool_execution_count, stage_completion_timestamp, last_execution_status
3. Field validation before persistence
4. Atomic state updates
5. Create AuditEvent entries with all required fields
6. Persist AuditEvent to session log (memory + disk)
7. Trigger iCloud sync after each update
8. Implement iCloud sync with exponential backoff (max 3 retries)
9. Fallback to local storage if iCloud unavailable
10. Query interface: AuditLog.query(hook_name, skill_name, result)
11. Latency optimization (<150ms)
12. Unit tests: state field updates, atomic updates, AuditEvent creation
13. iCloud sync + retry tests
14. Fallback tests

**Related Links:**

- [prd-user-stories.md#STORY-E4-005](prd-user-stories.md#story-story-e4-005-update-pipeline-state-hook-implementation)
- [prd-requirements.md#FR-E4-008](prd-requirements.md#fr-e4-008-update-pipeline-state-hook-activation)
- [prd-requirements.md#FR-E4-009](prd-requirements.md#fr-e4-009-pipeline-state-persistence)
- [prd-technical.md#4.5](prd-technical.md#45-hook-5-update-pipeline-state)

**Dependencies:**

- TASK-E4-006 (SessionStart hook + hook infrastructure)
- Epic 2 (PipelineState, AuditEvent models)

**Blocks:**

- TASK-E4-007 (save-session-summary uses AuditEvent)
- TASK-E4-009 (test suite integration)

---

### TASK-E4-006: SessionStart Hook Implementation

**Story:** STORY-E4-006
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 2
**Assignee:** TBD
**Sprint:** Sprint 1 (Week 1)

**Description:**

Implement the SessionStart lifecycle hook to initialize session state at startup. Load PipelineState from iCloud, validate SKILL.md versions, check sync status, and initialize session-scoped tracking structures.

**Acceptance Criteria:**

- AC-E4-005: SessionStart hook initialization logic
- AC-E4-006: Error handling + fallback
- AC-E4-007: iCloud sync status checking
- AC-E4-008: AuditEvent log initialization

**Tasks:**

1. Implement `hooks/session_start/session_start_hook.py`
2. Load PipelineState from iCloud with retry logic (3x exponential backoff)
3. Validate all SKILL.md files are >= v2.2
4. Check iCloud sync status (log warning if >5 min stale)
5. Initialize session.doc_read_tracker to empty dict
6. Initialize AuditEvent log with session_id + timestamp
7. Error handling: iCloud fallback, version validation, sync status logging
8. Latency optimization (<500ms total)
9. Unit tests: initialization, version validation, iCloud fallback
10. Integration tests: session state availability to downstream hooks

**Related Links:**

- [prd-user-stories.md#STORY-E4-006](prd-user-stories.md#story-story-e4-006-sessionstart-hook-implementation)
- [prd-requirements.md#FR-E4-001](prd-requirements.md#fr-e4-001-sessionstart-hook-initialization)
- [prd-technical.md#4.1](prd-technical.md#41-hook-1-sessionstart)

**Dependencies:**

- Epic 2 (PipelineState, AuditEvent)

**Blocks:**

- TASK-E4-002 (enforce-doc-read uses doc_read_tracker)
- TASK-E4-004 (security-tier-check)
- TASK-E4-005 (update-pipeline-state)
- TASK-E4-009 (test suite integration)

---

### TASK-E4-007: save-session-summary Hook Implementation

**Story:** STORY-E4-007
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 2
**Assignee:** TBD
**Sprint:** Sprint 4 (Week 4)

**Description:**

Implement the save-session-summary SessionEnd lifecycle hook to auto-generate HandoffDocument from AuditEvents and persist to iCloud. Creates complete session artifacts for handoff between sessions.

**Acceptance Criteria:**

- AC-E4-031: HandoffDocument generation
- AC-E4-032: Session artifact persistence

**Tasks:**

1. Implement `hooks/session_end/save_session_summary.py`
2. Collect all AuditEvents from session log
3. Generate HandoffDocument with sections:
   - Session metadata (ID, start/end time, duration)
   - Tool execution summary (tools, status)
   - State snapshot (PipelineState at session end)
   - Security events (tier 6+ commands, overrides)
   - Audit trail (30 most recent events)
   - Recommendations (violations, failures)
4. Format: markdown, human-readable + machine-parseable
5. Write to `sessions/{session_id}/handoff.md`
6. Compress session directory (tar.gz)
7. Upload to iCloud with conflict resolution (last-write-wins)
8. Fallback to local storage if iCloud unavailable
9. Retry logic: exponential backoff, max 3 retries
10. Unit tests: handoff generation, compression, iCloud upload
11. Manual review: handoff content quality
12. Integration tests: full session lifecycle (start → tools → end)

**Related Links:**

- [prd-user-stories.md#STORY-E4-007](prd-user-stories.md#story-story-e4-007-save-session-summary-hook-implementation)
- [prd-requirements.md#FR-E4-010](prd-requirements.md#fr-e4-010-save-session-summary-hook-implementation)
- [prd-technical.md#4.6](prd-technical.md#46-hook-6-save-session-summary)

**Dependencies:**

- TASK-E4-005 (update-pipeline-state creates AuditEvents)

**Blocks:**

- TASK-E4-009 (test suite integration)

---

### TASK-E4-008: Migrate 12 SKILL.md Files to v3.0

**Story:** STORY-E4-008
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** Medium
**Story Points:** 3
**Assignee:** TBD
**Sprint:** Sprint 4 (Week 4)

**Description:**

Upgrade all 12 existing SKILL.md files from v2.2 to v3.0. Run automated upgrade script, manually review security tiers + hook declarations, and verify backward compatibility.

**Acceptance Criteria:**

- AC-E4-036: SKILL.md v2.2 → v3.0 migration script
- AC-E4-039: Backward compatibility with v2.2

**Tasks:**

1. Implement `./scripts/upgrade-skill-v2-to-v3.py` upgrade script
2. Script processes all 12 SKILL.md files
3. Automatic generation: v3.0 sections with defaults
4. Backup originals: `SKILL.md.v2.2.bak`
5. Manual review of each upgraded file:
   - Classify security tier (1-10)
   - Add hook declarations (enforce-doc-read, etc.)
   - Define output schema (if applicable)
   - Set context budget
6. Generate upgrade report (per-file changes, required reviews)
7. Pre-upgrade testing: all 12 v2.2 SKILL.md files
8. Post-upgrade testing: all 12 v3.0 SKILL.md files
9. Regression testing: verify behavior unchanged
10. Documentation: upgrade guide for skill authors

**Related Links:**

- [prd-user-stories.md#STORY-E4-008](prd-user-stories.md#story-story-e4-008-migrate-12-skillmd-files-to-v30)
- [prd-requirements.md#FR-E4-012](prd-requirements.md#fr-e4-012-skillmd-v3-0-upgrade-path)
- [prd-technical.md#5.2](prd-technical.md#52-v2-2--v3-0-upgrade-script)

**Dependencies:**

- TASK-E4-001 (ADR-009 + upgrade script + migration plan)
- All other hook tasks (completed for upgrade context)

**Blocks:**

- None (final migration task)

---

### TASK-E4-009: Comprehensive Hook System Test Suite

**Story:** STORY-E4-009
**Epic:** E4 (Hook System Expansion)
**Issue Type:** Story
**Status:** New
**Priority:** High
**Story Points:** 3
**Assignee:** TBD
**Sprint:** Sprints 2-4 (continuous)

**Description:**

Develop comprehensive pytest suite covering all 6 hooks, 10 security tiers, schema validation, state persistence, and session lifecycle. Achieve ≥95% code coverage with real-world command fixtures. Full suite runs in <60s.

**Acceptance Criteria:**

- AC-E4-040: Test coverage ≥95%
- AC-E4-041: Test suite execution <60s

**Tasks:**

1. Create 5 test modules:
   - `tests/test_enforce_doc_read.py`: block/allow/override flows
   - `tests/test_security_tier.py`: 10 tiers + 30+ commands
   - `tests/test_validate_schema.py`: type/required/nested/pattern/enum
   - `tests/test_update_state.py`: state updates + AuditEvent
   - `tests/test_session_hooks.py`: SessionStart + SessionEnd lifecycle
2. Create test fixtures:
   - `tests/fixtures/security_tiers.json`: 30+ command examples
   - `tests/fixtures/skill_configs.yaml`: SKILL.md fixtures
   - `tests/fixtures/audit_events.json`: sample AuditEvents
3. Create `tests/conftest.py`: pytest configuration + mock objects
4. Unit tests:
   - All hook activation conditions
   - All hook decision logic (allow/block/ask)
   - All error paths + fallbacks
   - All configuration options
   - All edge cases
5. Integration tests:
   - Full session lifecycle (start → tools → end)
   - Hook sequencing + context passing
   - State persistence + iCloud sync
   - Backward compatibility with v2.2
6. Performance tests:
   - Per-hook latency benchmarks
   - Memory usage profiling
7. Code coverage:
   - pytest-cov integration
   - Target ≥95% coverage
   - Coverage report: HTML + console
8. CI/CD integration:
   - GitHub Actions workflow
   - Automated test execution on PR
   - Coverage reports
9. Test documentation:
   - Fixture data schema
   - Test case naming conventions
   - Adding new tests

**Related Links:**

- [prd-user-stories.md#STORY-E4-009](prd-user-stories.md#story-story-e4-009-comprehensive-hook-system-test-suite)
- [prd-requirements.md#FR-E4-020](prd-requirements.md#fr-e4-020-comprehensive-test-coverage)
- [prd-tests.md](prd-tests.md)

**Dependencies:**

- TASK-E4-001 (ADR-009 + templates)
- TASK-E4-002 (enforce-doc-read implementation)
- TASK-E4-003 (validate-output-schema implementation)
- TASK-E4-004 (security-tier-check implementation)
- TASK-E4-005 (update-pipeline-state implementation)
- TASK-E4-006 (SessionStart implementation)
- TASK-E4-007 (save-session-summary implementation)
- TASK-E4-008 (SKILL.md migration)

**Blocks:**

- None (testing wraps up epic)

---

## JIRA Bulk Import CSV

Copy the following CSV into JIRA for bulk import:

```csv
Issue Type,Key,Summary,Story Points,Epic Link,Status,Priority,Component,Sprint,Description,Acceptance Criteria,Dependencies,Related Documents
Story,TASK-E4-001,ADR-009 Survival Architecture v3.0 Template,3,E4,New,High,Architecture,Sprint 1,"Define and document Survival Architecture v3.0 with new SKILL.md sections (hook declarations, context budgets, security tiers, output schemas). Update SKILL.md parser for v3.0 while maintaining v2.2 backward compatibility.","AC-E4-001: v3.0 template defined in ADR-009 with new sections; AC-E4-002: SKILL.md parser updated to support v3.0 sections; AC-E4-003: v3.0 default template file created; AC-E4-004: Migration plan documented","None",prd-user-stories.md#STORY-E4-001; prd-requirements.md#FR-E4-011; prd-technical.md#5.1
Story,TASK-E4-002,enforce-doc-read Hook Implementation,3,E4,New,High,Hooks,Sprint 2,"Implement enforce-doc-read pre-tool-use hook to block tool execution until SKILL.md is read in current session. Track reading state in session.doc_read_tracker. Support user override with confirmation.","AC-E4-001: Hook blocks unread SKILL.md; AC-E4-002: User override flow; AC-E4-003: Session state persistence; AC-E4-004: SKILL.md formatting","TASK-E4-001; TASK-E4-006",prd-user-stories.md#STORY-E4-002; prd-requirements.md#FR-E4-002; prd-technical.md#4.2
Story,TASK-E4-003,validate-output-schema Hook Implementation,3,E4,New,High,Hooks,Sprint 3,"Implement validate-output-schema post-tool-use hook to validate stage output against JSON Schema declared in SKILL.md. Support blocking vs warning modes. Support JSON, YAML, and plain text formats.","AC-E4-019 through AC-E4-028: Schema validation features (type checking, required fields, nested objects, patterns, enums, format support, error messages, blocking vs warning modes)","TASK-E4-001; TASK-E4-005",prd-user-stories.md#STORY-E4-003; prd-requirements.md#FR-E4-006; prd-technical.md#4.3
Story,TASK-E4-004,security-tier-check Hook with 10-Tier Model,5,E4,New,High,Hooks,Sprint 2-3,"Implement security-tier-check pre-tool-use hook with comprehensive 10-tier security model. Parse bash commands, classify by threat level (Tier 1-10), decide: allow, allow+log, block+ask, or block unconditionally. Test with 30+ real-world commands.","AC-E4-009: Hook activation; AC-E4-010-015: Tier classifications (1-10); AC-E4-016: Latency <200ms; AC-E4-017: Classification accuracy (30+ commands); AC-E4-018: Edge case handling","TASK-E4-006",prd-user-stories.md#STORY-E4-004; prd-requirements.md#FR-E4-004; prd-requirements.md#FR-E4-005; prd-technical.md#3
Story,TASK-E4-005,update-pipeline-state Hook Implementation,3,E4,New,High,Hooks,Sprint 3,"Implement update-pipeline-state post-tool-use hook to update PipelineState after tool execution and create AuditEvent entries. Persist state to memory + iCloud with retry logic and fallback.","AC-E4-029: PipelineState fields updated; AC-E4-030: AuditEvent creation + logging","TASK-E4-006; Epic 2",prd-user-stories.md#STORY-E4-005; prd-requirements.md#FR-E4-008; prd-technical.md#4.5
Story,TASK-E4-006,SessionStart Hook Implementation,2,E4,New,High,Hooks,Sprint 1,"Implement SessionStart lifecycle hook to initialize session state. Load PipelineState from iCloud, validate SKILL.md versions, check iCloud sync status, initialize session-scoped tracking (doc_read_tracker, AuditEvent log).","AC-E4-005: SessionStart initialization logic; AC-E4-006: Error handling + fallback; AC-E4-007: iCloud sync status; AC-E4-008: AuditEvent log initialization","Epic 2",prd-user-stories.md#STORY-E4-006; prd-requirements.md#FR-E4-001; prd-technical.md#4.1
Story,TASK-E4-007,save-session-summary Hook Implementation,2,E4,New,High,Hooks,Sprint 4,"Implement save-session-summary SessionEnd lifecycle hook to auto-generate HandoffDocument from AuditEvents. Persist session artifacts (compressed + uploaded to iCloud) with fallback to local storage.","AC-E4-031: HandoffDocument generation; AC-E4-032: Session artifact persistence","TASK-E4-005",prd-user-stories.md#STORY-E4-007; prd-requirements.md#FR-E4-010; prd-technical.md#4.6
Story,TASK-E4-008,Migrate 12 SKILL.md Files to v3.0,3,E4,New,Medium,Infrastructure,Sprint 4,"Upgrade all 12 existing SKILL.md files from v2.2 to v3.0. Run automated upgrade script, manually review security tiers + hook declarations, verify backward compatibility.","AC-E4-036: Migration script; AC-E4-039: Backward compatibility","TASK-E4-001",prd-user-stories.md#STORY-E4-008; prd-requirements.md#FR-E4-012; prd-technical.md#5.2
Story,TASK-E4-009,Comprehensive Hook System Test Suite,3,E4,New,High,Testing,Sprint 2-4,"Develop comprehensive pytest suite covering all 6 hooks, 10 security tiers, schema validation, state persistence, session lifecycle. Achieve ≥95% code coverage with real-world fixtures. Full suite runs in <60s.","AC-E4-040: Test coverage ≥95%; AC-E4-041: Test suite execution <60s","TASK-E4-001 through TASK-E4-008",prd-user-stories.md#STORY-E4-009; prd-requirements.md#FR-E4-020; prd-tests.md
```

---

## Quick Reference: Dependencies Graph

```
TASK-E4-001 (ADR-009)
  ├─ TASK-E4-002 (enforce-doc-read)
  │  └─ TASK-E4-006 (SessionStart: doc_read_tracker)
  ├─ TASK-E4-003 (validate-output-schema)
  │  └─ TASK-E4-005 (update-pipeline-state)
  ├─ TASK-E4-004 (security-tier-check)
  │  └─ TASK-E4-006 (SessionStart)
  ├─ TASK-E4-005 (update-pipeline-state)
  │  └─ TASK-E4-007 (save-session-summary)
  ├─ TASK-E4-006 (SessionStart)
  ├─ TASK-E4-007 (save-session-summary)
  ├─ TASK-E4-008 (Migrate SKILL.md)
  │  └─ TASK-E4-001 (ADR-009)
  └─ TASK-E4-009 (Test suite)
     └─ All other tasks

Epic 2 Dependency: All tasks require PipelineState + AuditEvent models
```

---

## Assignment Guidelines

**Recommended Team Structure:**

| Task | Recommended Engineer | Skill Level | Sprint |
|------|----------------------|-----------|--------|
| TASK-E4-001 | Senior (Lead) | Expert (ADR authoring) | 1 |
| TASK-E4-002 | Mid-level | Intermediate | 2 |
| TASK-E4-003 | Senior | Intermediate | 3 |
| TASK-E4-004 | Senior | Expert (security model) | 2-3 |
| TASK-E4-005 | Mid-level | Intermediate (state management) | 3 |
| TASK-E4-006 | Mid-level | Intermediate | 1 |
| TASK-E4-007 | Mid-level | Intermediate | 4 |
| TASK-E4-008 | Junior | Beginner (script-driven) | 4 |
| TASK-E4-009 | QA Lead | Expert (testing) | 2-4 |

---

**Document Owner:** Product Manager
**Last Updated:** 2026-03-14
**Version:** 1.0
