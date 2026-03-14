# Epic 4: Hook System Expansion - User Stories

**Document:** prd-user-stories.md
**Version:** 1.0
**Date:** 2026-03-14
**Total SP:** 27 (Fibonacci: 2, 3, 5)

---

## Story STORY-E4-001: ADR-009 Survival Architecture v3.0 Template

**Story ID:** STORY-E4-001
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As an **architecture team member**, I want to define and document **Survival Architecture v3.0** so that **SKILL.md files can declare hooks, context budgets, and security tiers at the skill level**.

### Description

Update the SKILL.md template from v2.2 to v3.0. This story adds 4 new optional sections while maintaining backward compatibility. The new sections enable skills to declare hook applicability, token budgets, security classification, and output contracts.

### Acceptance Criteria

**AC-E4-001:** v3.0 template defined in ADR-009 with new sections
- [ ] ADR-009 document created (markdown format)
- [ ] Defines v3.0 template structure with all sections listed
- [ ] Includes examples for each new section (hook declarations, context budget, security tier, output schema)
- [ ] Specifies backward compatibility guarantees with v2.2
- [ ] Approved by architecture team

**AC-E4-002:** SKILL.md parser updated to support v3.0 sections
- [ ] Parser reads `survival-architecture-version: 3.0` field
- [ ] Parser extracts `hooks-declared`, `context-budget`, `security-tier`, `output-schema`
- [ ] Parser defaults missing v3.0 sections to safe values (hooks disabled, no schema validation)
- [ ] v2.2 files remain parseable without modification
- [ ] Test coverage: ≥95% of parser code

**AC-E4-003:** v3.0 default template file created
- [ ] Template file: `templates/skill-template-v3.0.md`
- [ ] Contains all v3.0 sections with inline documentation
- [ ] Includes example values (commented)
- [ ] Ready for use in skill generation

**AC-E4-004:** Migration plan documented
- [ ] Document describes v2.2 → v3.0 upgrade process
- [ ] Lists 12 existing SKILL.md files requiring review
- [ ] Provides automated upgrade script (prd-requirements.md FR-E4-012)
- [ ] No breaking changes; v2.2 files work as-is

### Related Requirements

- FR-E4-011: Survival Architecture v3.0 Template
- FR-E4-019: Backward Compatibility

### Related Stories

None (foundational story)

### Dependencies

- ADR-008 (hook dispatch model) finalized
- Epic 2 (PipelineState, AuditEvent) merged

### Effort Breakdown

- ADR-009 documentation: 1 SP
- Parser implementation: 1.5 SP
- Template + examples: 0.5 SP
- **Total: 3 SP**

---

## Story STORY-E4-002: enforce-doc-read Hook Implementation

**Story ID:** STORY-E4-002
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **skill author**, I want to **require users to read SKILL.md** before executing my skill so that **users understand context, requirements, and warnings before proceeding**.

### Description

Implement the `enforce-doc-read` pre-tool-use hook. This hook blocks tool execution if the skill's SKILL.md has not been read in the current session. Session state tracks which SKILL.md files have been read. Users can confirm reading the document to bypass the block.

### Acceptance Criteria

**AC-E4-001:** enforce-doc-read hook blocks unread SKILL.md
- [ ] Hook activates if `enforce-doc-read: true` in SKILL.md
- [ ] Hook checks session state: `session.doc_read_tracker[skill_name]`
- [ ] If not read: tool execution blocked, formatted SKILL.md returned to user
- [ ] If read: tool execution allowed, no blocking
- [ ] Latency: <100ms (dict lookup only)

**AC-E4-002:** User override flow implemented
- [ ] When blocked, user sees: "SKILL.md not read. Override? (yes/no)"
- [ ] If confirmed: update `doc_read_tracker`, retry tool execution
- [ ] If declined: abort tool execution
- [ ] Override logged to AuditEvent with user context

**AC-E4-003:** Session state persists across tool executions
- [ ] `session.doc_read_tracker` initialized in SessionStart hook
- [ ] Persisted in PipelineState (memory + iCloud)
- [ ] Survives tool invocation boundaries
- [ ] Cleared on SessionEnd

**AC-E4-004:** Documentation formatting
- [ ] SKILL.md displayed with proper markdown rendering
- [ ] Sections clearly labeled
- [ ] Readability optimized for terminal display
- [ ] Links/references preserved

### Related Requirements

- FR-E4-002: enforce-doc-read Hook Activation
- FR-E4-003: Document Read Tracking
- FR-E4-017: User Override for Pre-tool Hooks

### Related Stories

- STORY-E4-001 (v3.0 template with hook declarations)
- STORY-E4-006 (SessionStart initializes doc_read_tracker)

### Dependencies

- STORY-E4-001 (ADR-009, hook declarations)
- STORY-E4-006 (SessionStart hook)
- Epic 2 (PipelineState)

### Effort Breakdown

- Hook implementation: 1.5 SP
- Session state tracking: 0.8 SP
- User override flow: 0.7 SP
- **Total: 3 SP**

---

## Story STORY-E4-003: validate-output-schema Hook Implementation

**Story ID:** STORY-E4-003
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline architect**, I want to **validate tool outputs against declared schemas** so that **downstream stages receive data in expected format**.

### Description

Implement the `validate-output-schema` post-tool-use hook. This hook validates stage output against JSON Schema declared in SKILL.md `output-schema` section. Validation can be enforcing (blocking) or warning-only.

### Acceptance Criteria

**AC-E4-025:** validate-output-schema hook validates output
- [ ] Hook activates if `output-schema: {...}` in SKILL.md
- [ ] Parses tool output (JSON, YAML, plain text as specified)
- [ ] Validates against JSON Schema Draft 7
- [ ] Returns: `{valid: bool, errors: list[str], output: object}`
- [ ] Latency: <300ms for schemas <5KB

**AC-E4-026:** Blocking vs warning mode
- [ ] If `enforce-schema: true`: validation failure blocks stage completion
- [ ] If `enforce-schema: false`: validation failure logs warning only
- [ ] Both modes log validation errors to AuditEvent
- [ ] Error messages suggest schema correction

**AC-E4-027:** Schema validation features
- [ ] Required field validation
- [ ] Type checking (string, int, object, array, etc.)
- [ ] Pattern matching (regex)
- [ ] Enum validation
- [ ] Nested object validation
- [ ] Array validation (minItems, maxItems, uniqueItems)

**AC-E4-028:** Integration with stage output
- [ ] Hook called automatically after tool completion
- [ ] Tool output captured + passed to validator
- [ ] Validation errors logged but tool result preserved
- [ ] Invalid output available for debugging

### Related Requirements

- FR-E4-006: validate-output-schema Hook Activation
- FR-E4-007: Schema Validation Rules

### Related Stories

- STORY-E4-001 (v3.0 template with output-schema)
- STORY-E4-005 (update-pipeline-state hook)

### Dependencies

- STORY-E4-001 (ADR-009, output-schema section)
- Epic 2 (AuditEvent)

### Effort Breakdown

- Schema validation engine: 1.8 SP
- Blocking vs warning logic: 0.7 SP
- Error messaging: 0.5 SP
- **Total: 3 SP**

---

## Story STORY-E4-004: security-tier-check Hook with 10-Tier Model

**Story ID:** STORY-E4-004
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **security architect**, I want to **classify bash commands by threat level** so that **dangerous commands can be blocked or flagged before execution**.

### Description

Implement the `security-tier-check` pre-tool-use hook with a comprehensive 10-tier security model. The hook parses bash commands, classifies them into 1 of 10 tiers, and decides: allow, allow+log, block+ask, or block unconditionally.

### Acceptance Criteria

**AC-E4-009:** 10-tier model defined and implemented
- [ ] All 10 tiers defined (see prd-overview.md security model table)
- [ ] Tier 1-3: Safe operations (allow)
- [ ] Tier 4-5: Moderate (allow + log)
- [ ] Tier 6-7: High risk (block + ask user)
- [ ] Tier 8-10: Critical/catastrophic (block unconditionally)
- [ ] Tiers documented with examples

**AC-E4-010:** Command classification via regex + lookup
- [ ] Parse bash command: extract binary name, flags, arguments
- [ ] Regex patterns for each tier (modular, maintainable)
- [ ] Tier lookup table (JSON config, reloadable)
- [ ] Classification latency: <200ms

**AC-E4-011:** Tier 1-5 allow flow
- [ ] Commands classified as tier 1-5 allowed unconditionally
- [ ] Tier 4-5 logged to AuditEvent
- [ ] Return: `{tier: int, verdict: allow, reason: str}`

**AC-E4-012:** Tier 6-7 block+ask flow
- [ ] Commands classified as tier 6-7 blocked with reason
- [ ] User prompted: "This command is classified tier X (reason). Override? (yes/no)"
- [ ] Override logged as security decision + user context
- [ ] If confirmed: execute command; if declined: abort

**AC-E4-013:** Tier 8-10 block unconditionally
- [ ] Commands classified as tier 8-10 blocked without user option
- [ ] Logged as critical violation
- [ ] Return: `{tier: int, verdict: block, reason: str}`

**AC-E4-014:** Classification test coverage
- [ ] ≥30 real-world command examples tested per tier
- [ ] Edge cases: flags with values, pipes, redirects, etc.
- [ ] False positive rate <1%
- [ ] Security review + approval

### Related Requirements

- FR-E4-004: security-tier-check Hook Activation
- FR-E4-005: 10-Tier Security Classification Model

### Related Stories

- STORY-E4-009 (comprehensive test suite)

### Dependencies

- STORY-E4-006 (SessionStart hook, hook infrastructure)
- Epic 2 (AuditEvent)

### Effort Breakdown

- 10-tier model definition + docs: 1.2 SP
- Command parsing (regex + lookup): 1.5 SP
- Block+ask flow + user override: 1.3 SP
- Test coverage (30+ commands): 1 SP
- **Total: 5 SP**

---

## Story STORY-E4-005: update-pipeline-state Hook Implementation

**Story ID:** STORY-E4-005
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline operator**, I want to **automatically track tool execution state** so that **the system maintains accurate PipelineState across tool invocations and audits all decisions**.

### Description

Implement the `update-pipeline-state` post-tool-use hook. This hook runs after tool completion to update PipelineState fields and create AuditEvent entries. State is persisted to memory + iCloud with sync/retry logic.

### Acceptance Criteria

**AC-E4-029:** PipelineState updated with tool metadata
- [ ] Fields updated: last_tool_executed, last_stage_completed, tool_execution_count, stage_completion_timestamp, last_execution_status
- [ ] All fields validated before persistence
- [ ] Atomic updates (no partial states)
- [ ] Latency: <150ms

**AC-E4-030:** AuditEvent logged for all tool executions
- [ ] AuditEvent entry created: timestamp, event_type, actor, action, resource, result, context
- [ ] Persisted to session log (in-memory + disk)
- [ ] iCloud sync triggered after each update
- [ ] Sync retry logic: exponential backoff, max 3 retries
- [ ] Fallback to local storage if iCloud unavailable
- [ ] Query interface: `AuditLog.query(hook_name=..., skill_name=..., result=...)`

### Related Requirements

- FR-E4-008: update-pipeline-state Hook Activation
- FR-E4-009: Pipeline State Persistence
- FR-E4-016: Hook Logging & Audit Trail

### Related Stories

- STORY-E4-001 (ADR-009)
- STORY-E4-006 (SessionStart)

### Dependencies

- STORY-E4-006 (SessionStart hook, infrastructure)
- Epic 2 (PipelineState, AuditEvent models)

### Effort Breakdown

- PipelineState update logic: 1 SP
- AuditEvent creation + logging: 1 SP
- iCloud sync + retry logic: 1 SP
- **Total: 3 SP**

---

## Story STORY-E4-006: SessionStart Hook Implementation

**Story ID:** STORY-E4-006
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 2
**Status:** New
**Owner:** TBD

### User Story

As a **system architect**, I want to **initialize session state at startup** so that **all downstream hooks have consistent, validated state to work with**.

### Description

Implement the `SessionStart` lifecycle hook. This hook executes once per session before any tool execution. It loads PipelineState from iCloud, validates skill versions, checks iCloud sync status, and initializes the doc_read_tracker.

### Acceptance Criteria

**AC-E4-005:** SessionStart hook initialization logic
- [ ] Hook triggers once per session on first tool dispatch request
- [ ] Load PipelineState from iCloud (or local fallback if unavailable)
- [ ] Validate all SKILL.md files are ≥v2.2
- [ ] Check iCloud sync status; log warning if stale (>5 min) but continue
- [ ] Initialize `session.doc_read_tracker` (empty dict)
- [ ] Initialize AuditEvent log with session_id + start timestamp
- [ ] Latency: <500ms total

**AC-E4-006:** Error handling + fallback
- [ ] iCloud unavailable: use local cache + continue
- [ ] Missing SKILL.md: log error, list affected skills
- [ ] Stale sync: log warning, continue (non-blocking)
- [ ] Hook failure blocks session initialization

**AC-E4-007:** Session state validation
- [ ] PipelineState schema validated
- [ ] All required fields present
- [ ] Skill versions checked against minimum (v2.2)

**AC-E4-008:** Integration with downstream hooks
- [ ] SessionStart output feeds all downstream hooks
- [ ] session.doc_read_tracker available to enforce-doc-read
- [ ] PipelineState available to all hooks

### Related Requirements

- FR-E4-001: SessionStart Hook Initialization

### Related Stories

- STORY-E4-002 (enforce-doc-read uses doc_read_tracker)
- STORY-E4-005 (update-pipeline-state)

### Dependencies

- Epic 2 (PipelineState, AuditEvent)
- SKILL.md v2.2 parser implemented

### Effort Breakdown

- Hook initialization logic: 0.8 SP
- iCloud sync + fallback: 0.7 SP
- Error handling + validation: 0.5 SP
- **Total: 2 SP**

---

## Story STORY-E4-007: save-session-summary Hook Implementation

**Story ID:** STORY-E4-007
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 2
**Status:** New
**Owner:** TBD

### User Story

As a **session operator**, I want to **auto-generate session summaries** so that **handoff between sessions is complete and audit trail is preserved**.

### Description

Implement the `save-session-summary` SessionEnd lifecycle hook. This hook executes once per session when the session closes. It collects all AuditEvents, generates a HandoffDocument, and uploads to iCloud.

### Acceptance Criteria

**AC-E4-031:** HandoffDocument generation
- [ ] Collect all AuditEvents from session log
- [ ] Summarize: tools executed, stages completed, security violations, state changes
- [ ] Generate markdown file:
  - Session ID + start/end time
  - List of tools executed with status
  - State snapshot (PipelineState at session end)
  - Security events (all tier 6+ commands + user overrides)
  - Audit trail (30 most recent AuditEvents)
  - Recommendations (schema violations, doc read failures, etc.)
- [ ] Write to: `sessions/{session_id}/handoff.md`
- [ ] File is human-readable + machine-parseable

**AC-E4-032:** Session artifact persistence
- [ ] Compress session directory (including handoff.md)
- [ ] Upload to iCloud with conflict resolution (last-write-wins)
- [ ] Log upload status to audit trail
- [ ] Fallback to local storage if iCloud unavailable

### Related Requirements

- FR-E4-010: save-session-summary Hook Implementation
- FR-E4-016: Hook Logging & Audit Trail

### Related Stories

- STORY-E4-005 (update-pipeline-state creates AuditEvents)

### Dependencies

- STORY-E4-005 (AuditEvent logging)
- Epic 2 (AuditEvent model)

### Effort Breakdown

- HandoffDocument generation: 1 SP
- iCloud upload + compression: 0.6 SP
- Artifact formatting + recommendations: 0.4 SP
- **Total: 2 SP**

---

## Story STORY-E4-008: Migrate 12 SKILL.md Files to v3.0

**Story ID:** STORY-E4-008
**Epic:** E4 (Hook System Expansion)
**Priority:** P1
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **skill maintainer**, I want to **upgrade existing SKILL.md files to v3.0** so that **skills can leverage new hook declarations, context budgets, security tiers, and schema validation**.

### Description

Migrate all 12 existing SKILL.md files from v2.2 to v3.0. This includes running the automated upgrade script, manually reviewing security tier classifications, adding hook declarations and output schemas where applicable, and validating no breaking changes.

### Acceptance Criteria

**AC-E4-36:** Automated upgrade script execution
- [ ] Script: `./scripts/upgrade-skill-v2-to-v3.py`
- [ ] Processes all 12 SKILL.md files
- [ ] Generates v3.0 versions with default sections
- [ ] Produces upgrade report: per-file changes + required reviews
- [ ] No manual editing required for basic upgrade

**AC-E4-37:** Manual review + security tier classification
- [ ] Each skill manually reviewed for:
  - Security tier classification (1-10) based on bash commands
  - Hook declarations (which hooks apply to this skill)
  - Output schema (if stage has defined outputs)
  - Context budget (token limits, timeouts)
- [ ] 12 skills reviewed within 3-4 hours total (lightweight review)
- [ ] Reviewer: skill author or security team

**AC-E4-38:** Backward compatibility validation
- [ ] All 12 v3.0 SKILL.md files tested pre + post upgrade
- [ ] Behavior unchanged: no new enforcements break existing workflows
- [ ] v2.2 files still work as-is (not forced to upgrade)
- [ ] Upgrade is opt-in

**AC-E4-39:** Upgrade report + tracking
- [ ] Summary report: per-file security tier, hooks, schema status
- [ ] CSV export for project tracking
- [ ] List of skills requiring further enhancement (optional v3.0 features)

### Related Requirements

- FR-E4-012: SKILL.md v3.0 Upgrade Path
- FR-E4-019: Backward Compatibility

### Related Stories

- STORY-E4-001 (v3.0 template + upgrade path documentation)

### Dependencies

- STORY-E4-001 (ADR-009, upgrade script in FR-E4-012)

### Effort Breakdown

- Script execution + report generation: 1 SP
- Manual review (12 files): 1.2 SP
- Backward compatibility testing: 0.8 SP
- **Total: 3 SP**

---

## Story STORY-E4-009: Comprehensive Hook System Test Suite

**Story ID:** STORY-E4-009
**Epic:** E4 (Hook System Expansion)
**Priority:** P0
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **QA engineer**, I want to **comprehensively test all hooks and security model** so that **the hook system is robust, reliable, and production-ready**.

### Description

Develop full pytest suite covering all 6 hooks, all 10 security tiers, schema validation, state persistence, and session lifecycle. Includes fixture data for 30+ real-world bash command examples.

### Acceptance Criteria

**AC-E4-40:** Test suite structure (see prd-tests.md for full code)
- [ ] 5 test modules:
  - `test_enforce_doc_read.py`: block before read, allow after read
  - `test_security_tier.py`: 10 tiers with 30+ command examples
  - `test_validate_schema.py`: valid/invalid schema validation
  - `test_update_state.py`: PipelineState + AuditEvent integration
  - `test_session_hooks.py`: SessionStart + save-session-summary lifecycle
- [ ] Fixture data: security tier fixture as JSON
- [ ] Each test module independently runnable
- [ ] Total execution: <60s

**AC-E4-41:** Coverage requirements
- [ ] ≥95% code coverage for hook modules
- [ ] All 10 security tiers tested with real-world commands
- [ ] Edge cases: pipes, redirects, flags with values, etc.
- [ ] Pass/fail scenarios for schema validation
- [ ] Block/allow flows for doc read + security checks
- [ ] Session lifecycle: start → tools → end

### Related Requirements

- FR-E4-020: Comprehensive Test Coverage
- FR-E4-018: Hook Performance Requirements

### Related Stories

- STORY-E4-004 (30+ command examples for security tier testing)

### Dependencies

- All other stories (integration tests)

### Effort Breakdown

- Test case design: 1 SP
- Test implementation (5 modules): 1.2 SP
- Fixture data + CI integration: 0.8 SP
- **Total: 3 SP**

---

## Story Summary & SP Totals

| Story | Title | SP | Status |
|-------|-------|----|----|
| STORY-E4-001 | ADR-009 Survival v3.0 Template | 3 | New |
| STORY-E4-002 | enforce-doc-read Hook | 3 | New |
| STORY-E4-003 | validate-output-schema Hook | 3 | New |
| STORY-E4-004 | security-tier-check Hook (10-tier model) | 5 | New |
| STORY-E4-005 | update-pipeline-state Hook | 3 | New |
| STORY-E4-006 | SessionStart Hook | 2 | New |
| STORY-E4-007 | save-session-summary Hook | 2 | New |
| STORY-E4-008 | Migrate 12 SKILL.md to v3.0 | 3 | New |
| STORY-E4-009 | Comprehensive Test Suite | 3 | New |
| | **TOTAL** | **27** | |

---

## Dependencies Graph

```
STORY-E4-001 (ADR-009, v3.0)
  ├─ STORY-E4-002 (enforce-doc-read)
  │  └─ STORY-E4-006 (SessionStart: doc_read_tracker)
  ├─ STORY-E4-003 (validate-output-schema)
  │  └─ STORY-E4-005 (update-pipeline-state)
  ├─ STORY-E4-004 (security-tier-check)
  │  └─ STORY-E4-006 (SessionStart)
  ├─ STORY-E4-005 (update-pipeline-state)
  │  └─ STORY-E4-007 (save-session-summary)
  ├─ STORY-E4-006 (SessionStart)
  ├─ STORY-E4-007 (save-session-summary)
  ├─ STORY-E4-008 (Migrate SKILL.md v3.0)
  │  └─ STORY-E4-001 (ADR-009, upgrade script)
  └─ STORY-E4-009 (Test suite)
     └─ All other stories (integration tests)

Epic 2 Dependency: All stories depend on PipelineState + AuditEvent models
```

---

**Document Owner:** AI Architect Product Team
**Last Updated:** 2026-03-14
**Version:** 1.0
