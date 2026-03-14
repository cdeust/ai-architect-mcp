# Epic 4: Hook System Expansion - Requirements

**Document:** prd-requirements.md
**Version:** 1.0
**Date:** 2026-03-14

---

## Functional Requirements

### FR-E4-001: SessionStart Hook Initialization
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Hook Behavior

The `SessionStart` hook SHALL execute once at the beginning of each session, before any tool execution.

**Details:**
- Load PipelineState from iCloud (or local fallback if unavailable)
- Validate all loaded SKILL.md files are ≥v2.2
- Verify iCloud sync status; log warning if sync stale (>5 min) but continue
- Initialize AuditEvent log with `session_id` and session start timestamp
- Set `session.doc_read_tracker` to empty dict for tracking which SKILL.md files have been read

**Related Stories:** STORY-E4-006
**Related ACs:** AC-E4-005, AC-E4-006, AC-E4-007, AC-E4-008

---

### FR-E4-002: enforce-doc-read Hook Activation
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Hook Behavior

The `enforce-doc-read` hook SHALL be callable as a pre-tool-use hook to enforce SKILL.md reading before tool execution.

**Details:**
- If SKILL.md declares `enforce-doc-read: true`, hook is active
- Check if current skill's SKILL.md has been read in this session (tracked in `session.doc_read_tracker`)
- If NOT read: Block tool execution, return error + formatted SKILL.md content for user to read
- If read: Allow tool execution
- Support override: If user explicitly confirms "I've read the SKILL.md", mark as read and retry

**Related Stories:** STORY-E4-002
**Related ACs:** AC-E4-001, AC-E4-002, AC-E4-003, AC-E4-004

---

### FR-E4-003: Document Read Tracking
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** State Management

The system SHALL track which SKILL.md files have been read in the current session.

**Details:**
- Session-scoped state: `session.doc_read_tracker: dict[skill_name: str, read_at: ISO8601]`
- Updated when user confirms read or when enforced-doc-read hook allows execution
- Persisted in PipelineState (not cross-session)
- Cleared on SessionEnd

**Related Stories:** STORY-E4-002
**Related ACs:** AC-E4-003, AC-E4-004

---

### FR-E4-004: security-tier-check Hook Activation
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Hook Behavior

The `security-tier-check` hook SHALL execute before any bash command execution to classify threat level.

**Details:**
- Parse incoming bash command (extract binary name, flags, arguments)
- Classify command into 1 of 10 tiers (see prd-overview.md security model)
- Tier 1-5: Log and allow
- Tier 6-7: Block and ask user for confirmation
- Tier 8-10: Block unconditionally, log critical violation
- Return structured result: `{tier: int, command: str, verdict: allow|ask|block, reason: str}`

**Related Stories:** STORY-E4-004
**Related ACs:** AC-E4-009, AC-E4-010, AC-E4-011, AC-E4-012, AC-E4-013, AC-E4-014

---

### FR-E4-005: 10-Tier Security Classification Model
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Security

The `security-tier-check` hook SHALL implement a 10-tier security model as defined below.

**Tier Definitions:**

| Tier | Category | Risk | Examples | Verdict |
|------|----------|------|----------|---------|
| 1 | Safe reads | None | cat, ls, grep, head, tail, less | Allow |
| 2 | Environment | Low | echo, pwd, env, date, whoami | Allow |
| 3 | Package queries | Low | pip list, npm ls, brew list, gem list | Allow |
| 4 | Write/create | Moderate | touch, mkdir, cp, mv, sed, awk | Allow + log |
| 5 | Publish | Moderate | git push, npm publish, aws s3 cp | Allow + log |
| 6 | Docker ops | High | docker run, docker build, docker push | Block + ask |
| 7 | Permissions | High | chmod, chown, sudo, su, usermod | Block + ask |
| 8 | Process kill | Very high | kill, killall, pkill | Block unconditionally |
| 9 | System files | Critical | rm /etc, /usr/bin, /sys, /proc | Block unconditionally |
| 10 | Destructive | Catastrophic | rm -rf /, dd if=/dev/zero, shred -fvfz | Block unconditionally |

**Classification Method:**
- Regex-based command parsing (binary + flags extraction)
- Tier lookup table in code (modifiable JSON config)
- User-defined overrides via security config file (optional, per-skill)

**Related Stories:** STORY-E4-004
**Related ACs:** AC-E4-009 through AC-E4-024

---

### FR-E4-006: validate-output-schema Hook Activation
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Hook Behavior

The `validate-output-schema` hook SHALL execute after tool completion to validate stage output against SKILL.md contract.

**Details:**
- If SKILL.md declares `output-schema: {...}`, hook is active
- Parse tool output (JSON, YAML, or plain text based on `output-format` in SKILL.md)
- Validate output against declared JSON Schema
- If valid: Allow stage completion, log success
- If invalid: Block stage completion, log validation error, suggest schema correction
- Return result: `{valid: bool, errors: list[str], output: object}`

**Related Stories:** STORY-E4-003
**Related ACs:** AC-E4-025, AC-E4-026, AC-E4-027, AC-E4-028

---

### FR-E4-007: Schema Validation Rules
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Contracts

Stage output SHALL be validated using JSON Schema if declared in SKILL.md.

**Details:**
- Schema language: JSON Schema Draft 7 (as used by Pydantic v2)
- Required fields must be present
- Type checking enforced (string vs int vs object)
- Pattern matching for regex fields
- Enum validation for restricted values
- Nested object validation
- Array validation with minItems/maxItems/uniqueItems
- Validation failures are non-blocking warnings if `enforce-schema: false` (log only)
- Validation failures are blocking if `enforce-schema: true` (halt stage)

**Related Stories:** STORY-E4-003
**Related ACs:** AC-E4-025, AC-E4-026, AC-E4-027

---

### FR-E4-008: update-pipeline-state Hook Activation
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Hook Behavior

The `update-pipeline-state` hook SHALL execute after tool completion to update PipelineState and log AuditEvent.

**Details:**
- Triggered automatically after post-tool-use hooks
- Update PipelineState fields:
  - `last_tool_executed: str` (tool name)
  - `last_stage_completed: str` (stage name)
  - `tool_execution_count: int` (increment)
  - `stage_completion_timestamp: ISO8601`
  - `last_execution_status: success|warning|failure`
- Create AuditEvent entry:
  - `timestamp: ISO8601`
  - `event_type: tool_execution | state_update | hook_violation`
  - `actor: system | user`
  - `action: execute_tool | validate_schema | classify_security`
  - `resource: skill_name | command`
  - `result: success | blocked | warning`
  - `context: dict` (hook-specific data)
- Persist AuditEvent to session log + iCloud sync

**Related Stories:** STORY-E4-005
**Related ACs:** AC-E4-029, AC-E4-030

---

### FR-E4-009: Pipeline State Persistence
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** State Management

PipelineState updates by `update-pipeline-state` hook SHALL be persisted to both memory and iCloud.

**Details:**
- In-memory state updated atomically
- iCloud sync triggered after each state update
- Fallback to local disk if iCloud unavailable
- Sync retry logic: exponential backoff, max 3 retries
- Conflict resolution: last-write-wins with audit trail
- Session state available to subsequent hooks/tools

**Related Stories:** STORY-E4-005
**Related ACs:** AC-E4-029, AC-E4-030

---

### FR-E4-010: save-session-summary Hook Implementation
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Hook Behavior

The `save-session-summary` hook SHALL execute at session end to auto-generate HandoffDocument.

**Details:**
- Triggered automatically on SessionEnd event
- Collect all AuditEvents from session log
- Summarize: tools executed, stages completed, security violations, state changes
- Generate HandoffDocument with:
  - Session ID + start/end time
  - List of executed tools + success/failure status
  - State snapshot (PipelineState at session end)
  - Security events (all tier 6+ commands, user overrides)
  - Audit trail (30 most recent AuditEvents)
  - Recommendations (schema violations, doc read failures, etc.)
- Write to session directory: `sessions/{session_id}/handoff.md`
- Compress + upload to iCloud

**Related Stories:** STORY-E4-007
**Related ACs:** AC-E4-031, AC-E4-032

---

### FR-E4-011: Survival Architecture v3.0 Template
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Template

SKILL.md SHALL support Survival Architecture v3.0 (ADR-009) with new optional sections.

**Details:**
- Template extends v2.2 (backward compatible)
- New sections:
  - `survival-architecture-version: 3.0`
  - `hooks-declared:` (list of hook names applicable to this skill)
  - `context-budget:` (token limits per stage, timeout thresholds)
  - `security-tier: [1-10]` (classification of skill's bash commands)
  - `output-schema: {...}` (JSON Schema for expected stage outputs)
  - `enforce-schema: true|false` (blocking vs warning on schema violation)
- v2.2 SKILL.md remains valid with default hook behavior (no enforcement)
- v3.0 optional; no breaking changes

**Related Stories:** STORY-E4-001
**Related ACs:** AC-E4-033, AC-E4-034, AC-E4-035

---

### FR-E4-012: SKILL.md v3.0 Upgrade Path
**Epic:** Hook System Expansion
**Priority:** P1
**Category:** Migration

The system SHALL provide automatic and manual upgrade paths for SKILL.md v2.2 → v3.0.

**Details:**
- Automatic generation: Extract existing sections, add v3.0 defaults
- Manual review: 12 SKILL.md files require human review + security tier classification
- No breaking changes; v2.2 files default to hook-disabled (compatible)
- Upgrade script: `./scripts/upgrade-skill-v2-to-v3.py`
- Output: Updated SKILL.md + upgrade report

**Related Stories:** STORY-E4-008
**Related ACs:** AC-E4-036

---

### FR-E4-013: Hook Dispatch Architecture
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Architecture

Hook execution SHALL follow defined dispatch model with proper sequencing.

**Details:**
- **SessionStart hooks** (once per session):
  - Executed before any tool execution
  - Order: defined in session config
  - Failure halts session initialization
- **Pre-tool-use hooks** (before each tool):
  - Executed in sequence: enforce-doc-read → security-tier-check → custom hooks
  - Can block tool execution (with user override option)
  - Failure cascades: if enforce-doc-read blocks, security-tier-check skipped
- **Post-tool-use hooks** (after each tool):
  - Executed in sequence: validate-output-schema → update-pipeline-state → custom hooks
  - Cannot block tool execution (too late), but log violations
  - Failures logged as warnings
- **SessionEnd hooks** (once per session):
  - Executed after all tools complete
  - Order: save-session-summary → custom hooks
  - Failure logged; session still closes

**Related Stories:** STORY-E4-001, STORY-E4-002, STORY-E4-003, STORY-E4-004, STORY-E4-005
**Related ACs:** AC-E4-001 through AC-E4-032

---

### FR-E4-014: Hook Implementation as Python Modules
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Implementation

Hooks SHALL be implemented as Python modules (not just shell scripts) for testability and reusability.

**Details:**
- Hook interface: Abstract base class `Hook(ABC)` with `execute()` method
- Hooks located in: `hooks/{hook_type}/{hook_name}.py`
- Standard imports: `from hooks.base import Hook, HookContext, HookResult`
- Each hook returns `HookResult: {status: allow|block|ask, message: str, context: dict}`
- Hooks are async-capable (support async/await for I/O-heavy operations)
- Shell script wrappers optional; Python takes precedence

**Related Stories:** All
**Related ACs:** AC-E4-001 through AC-E4-032

---

### FR-E4-015: Hook Context Passing
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Architecture

Hooks SHALL receive structured context through `HookContext` object.

**Details:**
- `HookContext` contains:
  - `session_id: str`
  - `session_state: PipelineState`
  - `tool_name: str`
  - `command: str` (for bash hooks)
  - `skill_config: dict` (parsed SKILL.md)
  - `audit_log: list[AuditEvent]`
  - `doc_read_tracker: dict`
  - `security_config: dict` (tier overrides)
- HookContext passed to all hooks uniformly
- Hooks can read but not modify context directly (logging only)

**Related Stories:** All
**Related ACs:** AC-E4-001 through AC-E4-032

---

### FR-E4-016: Hook Logging & Audit Trail
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Observability

All hook decisions SHALL be logged to AuditEvent with full context.

**Details:**
- Every hook execution → AuditEvent entry
- Logged fields: timestamp, hook_name, skill_name, decision (allow|block|ask), reason, context
- Special handling for security-tier-check: tier classification logged separately
- Audit trail persisted to session log + iCloud
- Query interface: `AuditLog.query(hook_name=..., skill_name=..., result=...)`

**Related Stories:** STORY-E4-005, STORY-E4-007
**Related ACs:** AC-E4-029, AC-E4-030, AC-E4-031

---

### FR-E4-017: User Override for Pre-tool Hooks
**Epic:** Hook System Expansion
**Priority:** P1
**Category:** User Experience

Users SHALL be able to override pre-tool-use hook blocks with explicit confirmation.

**Details:**
- When enforce-doc-read or security-tier-check blocks tool execution:
  - Display reason + context
  - Prompt: "Override and proceed? (yes/no)"
  - If user confirms: log override as AuditEvent, proceed with tool execution
  - If user declines: stop tool execution
- Override logged with user context (who, when, reason they provided)
- Audit trail tracks all overrides for security review

**Related Stories:** STORY-E4-002, STORY-E4-004
**Related ACs:** AC-E4-004, AC-E4-024

---

### FR-E4-018: Hook Performance Requirements
**Epic:** Hook System Expansion
**Priority:** P1
**Category:** Non-Functional

Hook execution SHALL meet defined latency and resource constraints.

**Details:**
- enforce-doc-read: <100ms (simple dict lookup)
- security-tier-check: <200ms (regex + tier lookup)
- validate-output-schema: <300ms (JSON validation)
- update-pipeline-state: <150ms (state update + I/O)
- SessionStart: <500ms (total, all hooks)
- SessionEnd: <1s (total, all hooks)
- No hook shall consume >50MB memory
- Measured on standard hardware (2-core, 4GB RAM)

**Related Stories:** All
**Related ACs:** AC-E4-037, AC-E4-038

---

### FR-E4-019: Backward Compatibility
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Compatibility

Existing SKILL.md v2.2 files SHALL continue to work unchanged.

**Details:**
- v2.2 SKILL.md files without v3.0 sections: hooks default to disabled
- Default behavior: no enforcement, pass-through allow
- Migration optional, not mandatory
- Upgrade script provided but not forced
- Dual-version support in parser (v2.2 + v3.0 simultaneously)

**Related Stories:** STORY-E4-008
**Related ACs:** AC-E4-039

---

### FR-E4-020: Comprehensive Test Coverage
**Epic:** Hook System Expansion
**Priority:** P0
**Category:** Testing

Hook system SHALL have ≥95% code coverage with real-world test scenarios.

**Details:**
- Test files: see prd-tests.md
- Coverage measured with pytest-cov
- All 10 security tiers tested with real-world commands
- Schema validation tested: valid + invalid outputs
- Doc read blocking + allowing tested
- State persistence tested
- Session lifecycle (start → tools → end) tested
- All pre-hook block flows tested
- User override flows tested

**Related Stories:** STORY-E4-009
**Related ACs:** AC-E4-040, AC-E4-041

---

## Non-Functional Requirements

### NFR-E4-001: Hook Latency Budget
**Requirement:** All hooks combined <500ms per tool execution
**Measurement:** p95 latency over 1000 executions
**Owner:** STORY-E4-009

### NFR-E4-002: Security Classification Speed
**Requirement:** security-tier-check <200ms; tier lookup <50ms
**Measurement:** Per-command classification time, regex compilation cached
**Owner:** STORY-E4-004

### NFR-E4-003: Schema Validation Speed
**Requirement:** validate-output-schema <300ms for schemas <5KB
**Measurement:** JSON parsing + validation overhead
**Owner:** STORY-E4-003

### NFR-E4-004: State Persistence
**Requirement:** PipelineState + AuditEvent persisted within 100ms of update
**Measurement:** Write latency to disk + iCloud queue
**Owner:** STORY-E4-005

### NFR-E4-005: Backward Compatibility
**Requirement:** 100% of v2.2 SKILL.md files execute unchanged
**Measurement:** All 12 existing SKILL.md files tested pre + post upgrade
**Owner:** STORY-E4-008

### NFR-E4-006: Memory Efficiency
**Requirement:** Hook execution <50MB per hook
**Measurement:** RSS memory usage during hook execution
**Owner:** All stories

### NFR-E4-007: Audit Trail Completeness
**Requirement:** 100% of hook decisions logged to AuditEvent
**Measurement:** No decisions missing from audit trail
**Owner:** STORY-E4-005, STORY-E4-007

### NFR-E4-008: iCloud Sync Reliability
**Requirement:** PipelineState sync succeeds 99% of time; fallback to local if unavailable
**Measurement:** Sync success rate + fallback activation count
**Owner:** STORY-E4-005, STORY-E4-006

### NFR-E4-009: Documentation Clarity
**Requirement:** All hooks + security model documented with examples
**Measurement:** PR review + team feedback
**Owner:** All stories

### NFR-E4-010: Test Execution Speed
**Requirement:** Full test suite runs in <60s
**Measurement:** pytest execution time
**Owner:** STORY-E4-009

---

## Requirements Traceability

| FR ID | Story | Status | Owner |
|-------|-------|--------|-------|
| FR-E4-001 | STORY-E4-006 | New | TBD |
| FR-E4-002 | STORY-E4-002 | New | TBD |
| FR-E4-003 | STORY-E4-002 | New | TBD |
| FR-E4-004 | STORY-E4-004 | New | TBD |
| FR-E4-005 | STORY-E4-004 | New | TBD |
| FR-E4-006 | STORY-E4-003 | New | TBD |
| FR-E4-007 | STORY-E4-003 | New | TBD |
| FR-E4-008 | STORY-E4-005 | New | TBD |
| FR-E4-009 | STORY-E4-005 | New | TBD |
| FR-E4-010 | STORY-E4-007 | New | TBD |
| FR-E4-011 | STORY-E4-001 | New | TBD |
| FR-E4-012 | STORY-E4-008 | New | TBD |
| FR-E4-013 | All | New | TBD |
| FR-E4-014 | All | New | TBD |
| FR-E4-015 | All | New | TBD |
| FR-E4-016 | STORY-E4-005, STORY-E4-007 | New | TBD |
| FR-E4-017 | STORY-E4-002, STORY-E4-004 | New | TBD |
| FR-E4-018 | All | New | TBD |
| FR-E4-019 | STORY-E4-008 | New | TBD |
| FR-E4-020 | STORY-E4-009 | New | TBD |

---

**Document Owner:** AI Architect Product Team
**Last Updated:** 2026-03-14
**Version:** 1.0
