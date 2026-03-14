# Epic 4: Hook System Expansion - Acceptance Criteria

**Document:** prd-acceptance.md
**Version:** 1.0
**Date:** 2026-03-14

---

## Overview

This document contains comprehensive acceptance criteria (ACs) for all Epic 4 deliverables. Each AC is traceable to one or more functional requirements (FRs) and user stories. ACs are organized by hook and feature area.

**Total AC Count:** 41

---

## AC-E4-001: enforce-doc-read Hook Blocks Unread SKILL.md

**Type:** Functional
**Related FR:** FR-E4-002, FR-E4-003
**Related Story:** STORY-E4-002
**Status:** New
**Priority:** P0

### Criteria

1. Hook is triggered before tool execution if `enforce-doc-read: true` in SKILL.md
2. Hook checks session state: `session.doc_read_tracker[skill_name]`
3. If skill_name NOT in doc_read_tracker:
   - Tool execution is blocked
   - Error message includes formatted SKILL.md content
   - User prompted for override: "I've read this. Override? (yes/no)"
4. If skill_name in doc_read_tracker:
   - Tool execution is allowed
   - No blocking message
   - Execution proceeds immediately
5. Hook latency is <100ms (measured with dict lookup only, not SKILL.md parsing)

### Test Cases

- TC-E4-001-A: Block unread SKILL.md on first tool execution
- TC-E4-001-B: Allow execution after user confirms read
- TC-E4-001-C: Latency benchmark <100ms
- TC-E4-001-D: Session state persists across multiple tool calls

### Verification

- [ ] Unit test: test_enforce_doc_read.py::test_blocks_unread
- [ ] Unit test: test_enforce_doc_read.py::test_allows_after_read
- [ ] Performance test: latency <100ms
- [ ] Integration test: session state persistence

---

## AC-E4-002: enforce-doc-read Hook User Override Flow

**Type:** Functional
**Related FR:** FR-E4-002, FR-E4-017
**Related Story:** STORY-E4-002
**Status:** New
**Priority:** P0

### Criteria

1. When hook blocks execution, display prompt: "SKILL.md not read yet. Override? (yes/no)"
2. If user enters "yes": update `doc_read_tracker[skill_name]` with ISO8601 timestamp
3. Retry tool execution immediately after override
4. Log override as AuditEvent with:
   - `event_type: override`
   - `hook_name: enforce-doc-read`
   - `user_decision: override`
   - `timestamp: ISO8601`
5. If user enters "no": abort tool execution, return to session prompt

### Test Cases

- TC-E4-002-A: User confirms override; tool executes
- TC-E4-002-B: User declines override; tool aborted
- TC-E4-002-C: Override logged to AuditEvent with user context
- TC-E4-002-D: Subsequent tool calls skip doc-read check

### Verification

- [ ] Unit test: test_enforce_doc_read.py::test_user_override_yes
- [ ] Unit test: test_enforce_doc_read.py::test_user_override_no
- [ ] Audit test: test_update_state.py::test_override_logged

---

## AC-E4-003: Document Read Tracking State Management

**Type:** Functional
**Related FR:** FR-E4-003
**Related Story:** STORY-E4-002
**Status:** New
**Priority:** P0

### Criteria

1. Session-scoped state object: `session.doc_read_tracker: dict[skill_name: str, read_at: ISO8601]`
2. Initialized in SessionStart hook to empty dict `{}`
3. Updated when user confirms read: `doc_read_tracker[skill_name] = datetime.now(ISO8601)`
4. Persisted in PipelineState (memory + iCloud sync)
5. Cleared when session ends (SessionEnd hook)
6. Query interface: `session.doc_read_tracker.get(skill_name)` returns ISO8601 timestamp or None

### Test Cases

- TC-E4-003-A: doc_read_tracker initialized empty in SessionStart
- TC-E4-003-B: doc_read_tracker updated on user confirmation
- TC-E4-003-C: doc_read_tracker persisted to PipelineState
- TC-E4-003-D: doc_read_tracker cleared on SessionEnd
- TC-E4-003-E: Multiple skill reads tracked separately

### Verification

- [ ] Unit test: test_session_hooks.py::test_doc_read_tracker_init
- [ ] Unit test: test_session_hooks.py::test_doc_read_tracker_update
- [ ] Integration test: test_update_state.py::test_state_persisted

---

## AC-E4-004: SKILL.md Formatting and Display

**Type:** Functional
**Related FR:** FR-E4-002
**Related Story:** STORY-E4-002
**Status:** New
**Priority:** P1

### Criteria

1. When doc-read hook blocks, display SKILL.md with:
   - Proper markdown rendering (headings, bold, italic, code blocks preserved)
   - Section headers clearly labeled
   - Table of contents for navigation
   - Terminal-optimized line length (<120 chars)
2. Content truncated to first 50 lines if SKILL.md >50 lines
   - Include note: "(Truncated. Full SKILL.md available at [path])"
3. Links/references preserved in output
4. Color coding: warnings in yellow, critical in red (if terminal supports)

### Test Cases

- TC-E4-004-A: SKILL.md <50 lines displayed in full
- TC-E4-004-B: SKILL.md >50 lines truncated with note
- TC-E4-004-C: Markdown formatting preserved in terminal output
- TC-E4-004-D: Links display as "[text](url)"

### Verification

- [ ] Unit test: test_enforce_doc_read.py::test_skill_md_formatting
- [ ] Manual test: display real SKILL.md to verify readability

---

## AC-E4-005: SessionStart Hook Initialization

**Type:** Functional
**Related FR:** FR-E4-001
**Related Story:** STORY-E4-006
**Status:** New
**Priority:** P0

### Criteria

1. SessionStart hook triggered once at session initialization (before first tool execution)
2. Hook performs initialization in sequence:
   a. Load PipelineState from iCloud (with 3-retry exponential backoff)
   b. Validate all SKILL.md files are ≥v2.2
   c. Check iCloud sync status (log warning if >5 min stale, but continue)
   d. Initialize `session.doc_read_tracker` to empty dict
   e. Initialize AuditEvent log with session_id + timestamp
3. Total latency: <500ms
4. If any step fails: return HookResult(status='block', message)
5. If successful: return HookResult(status='allow', context with sync status)

### Test Cases

- TC-E4-005-A: SessionStart completes successfully
- TC-E4-005-B: PipelineState loaded from iCloud
- TC-E4-005-C: SKILL.md versions validated (all ≥v2.2)
- TC-E4-005-D: iCloud sync status checked; warning logged if stale
- TC-E4-005-E: session.doc_read_tracker initialized to {}
- TC-E4-005-F: Latency <500ms

### Verification

- [ ] Unit test: test_session_hooks.py::test_session_start_init
- [ ] Unit test: test_session_hooks.py::test_skill_version_validation
- [ ] Performance test: latency <500ms
- [ ] Integration test: test_session_hooks.py::test_full_lifecycle

---

## AC-E4-006: SessionStart Error Handling

**Type:** Functional
**Related FR:** FR-E4-001
**Related Story:** STORY-E4-006
**Status:** New
**Priority:** P0

### Criteria

1. iCloud unavailable: Load from local cache; log warning; continue (non-blocking)
2. SKILL.md version <v2.2: Log error, list affected skills; continue (non-blocking)
3. iCloud sync stale (>5 min): Log warning; continue (non-blocking)
4. AuditEvent initialization fails: Log error; continue (non-blocking)
5. Fatal error (e.g., corrupted PipelineState): Block session initialization, return error

### Test Cases

- TC-E4-006-A: iCloud unavailable; fallback to local
- TC-E4-006-B: v2.1 SKILL.md detected; warning logged
- TC-E4-006-C: Sync status >5 min old; warning logged
- TC-E4-006-D: Corrupted PipelineState; session initialization blocked

### Verification

- [ ] Unit test: test_session_hooks.py::test_icloud_fallback
- [ ] Unit test: test_session_hooks.py::test_version_validation_error
- [ ] Unit test: test_session_hooks.py::test_corrupted_state_blocks

---

## AC-E4-007: SessionStart iCloud Sync Check

**Type:** Functional
**Related FR:** FR-E4-001
**Related Story:** STORY-E4-006
**Status:** New
**Priority:** P1

### Criteria

1. Hook queries iCloud sync API: last sync timestamp
2. Calculate lag: `now() - last_sync_timestamp`
3. If lag >5 minutes: log warning with lag_minutes; continue
4. If lag ≤5 minutes: log info; continue
5. Return sync status in HookResult context: `{synced: bool, lag_minutes: int}`

### Test Cases

- TC-E4-007-A: Sync current (<5 min); no warning
- TC-E4-007-B: Sync stale (>5 min); warning logged
- TC-E4-007-C: Sync status returned in HookResult context
- TC-E4-007-D: iCloud API failure handled gracefully

### Verification

- [ ] Unit test: test_session_hooks.py::test_icloud_sync_status
- [ ] Unit test: test_session_hooks.py::test_sync_warning

---

## AC-E4-008: AuditEvent Log Initialization

**Type:** Functional
**Related FR:** FR-E4-001
**Related Story:** STORY-E4-006
**Status:** New
**Priority:** P0

### Criteria

1. AuditEvent log initialized with first entry:
   - `event_type: session_start`
   - `actor: system`
   - `timestamp: ISO8601`
   - `session_id: UUID`
2. Log stored in memory + persisted to `sessions/{session_id}/audit.log`
3. Subsequent tool executions append entries to log
4. Query interface: `AuditLog.get_session_events(session_id)` returns list

### Test Cases

- TC-E4-008-A: AuditEvent log initialized in SessionStart
- TC-E4-008-B: First entry has correct fields
- TC-E4-008-C: Subsequent entries appended to log
- TC-E4-008-D: Query interface returns all events

### Verification

- [ ] Unit test: test_session_hooks.py::test_audit_log_init
- [ ] Unit test: test_update_state.py::test_audit_event_append

---

## AC-E4-009: security-tier-check Hook Activates Before Bash

**Type:** Functional
**Related FR:** FR-E4-004
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. Hook executes as pre-tool-use hook before any bash command
2. Receives bash command in HookContext: `context.command`
3. If no command provided: return `HookResult(status='allow')`
4. Parses command: extract binary name + flags
5. Classifies into tier 1-10 using CommandClassifier
6. Returns HookResult with:
   - `status: allow | ask | block`
   - `context.tier: int (1-10)`
   - `context.category: str`
   - `context.verdict: str`

### Test Cases

- TC-E4-009-A: Hook triggers before bash command
- TC-E4-009-B: Command parsed correctly
- TC-E4-009-C: Classification returns valid tier (1-10)
- TC-E4-009-D: No command provided; allow

### Verification

- [ ] Unit test: test_security_tier.py::test_hook_triggers
- [ ] Unit test: test_security_tier.py::test_command_parsing

---

## AC-E4-010: 10-Tier Model - Tier 1 (Safe Reads)

**Type:** Functional
**Related FR:** FR-E4-005
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. Tier 1 includes: cat, ls, grep, head, tail, less, find, stat, pwd (when query-only)
2. Risk level: None
3. Verdict: Allow
4. Examples:
   - `cat /etc/passwd` → Tier 1
   - `ls -la /home` → Tier 1
   - `grep pattern file.txt` → Tier 1
   - `find . -name "*.py"` → Tier 1
5. Execution allowed without user interaction
6. Not logged to security audit (low risk)

### Test Cases

- TC-E4-010-A through TC-E4-010-H: Each tier 1 command classified correctly

### Verification

- [ ] Unit test: test_security_tier.py::test_tier_1_commands (8 commands)

---

## AC-E4-011: 10-Tier Model - Tier 2 (Environment)

**Type:** Functional
**Related FR:** FR-E4-005
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. Tier 2 includes: echo, pwd, env, date, whoami, hostname, uname
2. Risk level: Low
3. Verdict: Allow
4. Examples:
   - `echo $PATH` → Tier 2
   - `env | grep USER` → Tier 2
   - `whoami` → Tier 2
   - `date +%s` → Tier 2

### Verification

- [ ] Unit test: test_security_tier.py::test_tier_2_commands (4 commands)

---

## AC-E4-012: 10-Tier Model - Tier 3 (Package Queries)

**Type:** Functional
**Related FR:** FR-E4-005
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. Tier 3 includes: pip, npm, brew, gem, apt, yum (read-only flags only)
2. Risk level: Low
3. Verdict: Allow
4. Examples:
   - `pip list` → Tier 3
   - `npm ls` → Tier 3
   - `brew list` → Tier 3
5. Note: `pip install` or `npm install` → Tier 5 (publish)

### Verification

- [ ] Unit test: test_security_tier.py::test_tier_3_commands (5 commands)

---

## AC-E4-013: 10-Tier Model - Tier 4-5 (Write/Publish)

**Type:** Functional
**Related FR:** FR-E4-005
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. **Tier 4 (Write/create):** touch, mkdir, cp, mv, rm, sed, awk, ed
   - Risk: Moderate
   - Verdict: Allow + Log
   - Examples: `touch file.txt`, `mkdir -p dir`, `cp file1 file2`

2. **Tier 5 (Publish):** git push, npm publish, aws s3 cp, gcloud deploy
   - Risk: Moderate
   - Verdict: Allow + Log
   - Examples: `git push origin main`, `npm publish --access public`

3. Both logged to AuditEvent but not blocking

### Verification

- [ ] Unit test: test_security_tier.py::test_tier_4_commands (5 commands)
- [ ] Unit test: test_security_tier.py::test_tier_5_commands (4 commands)

---

## AC-E4-014: 10-Tier Model - Tier 6-7 (Block+Ask)

**Type:** Functional
**Related FR:** FR-E4-005
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. **Tier 6 (Docker ops):** docker run, docker build, docker push, podman, buildah
   - Risk: High
   - Verdict: Block + Ask
   - Reason: Can leak secrets, escalate privileges
   - Example: `docker run -v /root:/mnt ubuntu` → Tier 6

2. **Tier 7 (Permissions):** chmod, chown, sudo, su, usermod, setfacl
   - Risk: High
   - Verdict: Block + Ask
   - Reason: Permission changes, privilege escalation
   - Example: `chmod 777 /etc/shadow` → Tier 7

3. User prompted: "This command is tier X. Override? (yes/no)"
4. If yes: execute, log override; if no: abort

### Verification

- [ ] Unit test: test_security_tier.py::test_tier_6_commands (3 commands)
- [ ] Unit test: test_security_tier.py::test_tier_7_commands (3 commands)
- [ ] Unit test: test_security_tier.py::test_tier_6_user_override

---

## AC-E4-015: 10-Tier Model - Tier 8-10 (Block Unconditionally)

**Type:** Functional
**Related FR:** FR-E4-005
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. **Tier 8 (Process kill):** kill, killall, pkill
   - Risk: Very High
   - Verdict: Block (no override)
   - Example: `kill -9 12345` → Blocked

2. **Tier 9 (System files):** rm /etc/*, /usr/bin/*, /sys/*, /proc/*
   - Risk: Critical
   - Verdict: Block (no override)
   - Example: `rm /etc/shadow` → Blocked

3. **Tier 10 (Destructive):** rm -rf /, dd if=/dev/zero of=/dev/...
   - Risk: Catastrophic
   - Verdict: Block (no override)
   - Example: `rm -rf /` → Blocked immediately

4. All tier 8-10 commands logged as critical security violations
5. No user override option for tier 8-10

### Verification

- [ ] Unit test: test_security_tier.py::test_tier_8_commands (2 commands)
- [ ] Unit test: test_security_tier.py::test_tier_9_commands (2 commands)
- [ ] Unit test: test_security_tier.py::test_tier_10_commands (2 commands)

---

## AC-E4-016: Security Tier Latency <200ms

**Type:** Non-Functional
**Related FR:** FR-E4-004, FR-E4-018
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. Command classification latency: <200ms (p95 over 1000 executions)
2. Regex compilation cached at startup (not on each command)
3. Tier lookup table in memory (JSON config loaded once)
4. No network I/O during classification
5. Measured on standard hardware (2-core, 4GB RAM)

### Test Cases

- TC-E4-016-A: Classification latency <200ms (p95)
- TC-E4-016-B: Regex compilation cached
- TC-E4-016-C: Tier lookup from memory

### Verification

- [ ] Performance test: test_security_tier.py::test_classification_latency
- [ ] Benchmark: 1000 command classifications, report p50/p95/p99

---

## AC-E4-017: Security Tier Classification Accuracy

**Type:** Functional
**Related FR:** FR-E4-004
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P0

### Criteria

1. Classify 30+ real-world bash commands with 100% accuracy
2. Edge cases handled:
   - Flags with values: `rm -rf /tmp/dir` → Tier 9 (system files prefix)
   - Pipes/redirects: `cat file | grep pattern` → Tier 1 (cat is primary)
   - Aliases: `ll` (alias for `ls -l`) → Tier 1
   - Full paths: `/usr/bin/rm /tmp/file` → Tier 4 (write)
3. No false negatives on tier 8-10 (dangerous commands never misclassified as safe)
4. False positive rate <1% (safe commands sometimes classified higher; acceptable)

### Test Cases

- TC-E4-017-A through TC-E4-017-AE: 30 command examples

### Verification

- [ ] Unit test: test_security_tier.py::test_command_examples (fixture data in fixtures/security_tiers.json)
- [ ] Code review: security team validates classification logic

---

## AC-E4-018: Command Parsing - Edge Cases

**Type:** Functional
**Related FR:** FR-E4-004
**Related Story:** STORY-E4-004
**Status:** New
**Priority:** P1

### Criteria

1. Parse commands with:
   - Shell operators: pipes `|`, redirects `>`, `<`, `2>&1`
   - Semicolons: `cmd1; cmd2`
   - Ampersand: `cmd &`
   - Quotes: `"string"`, `'string'`
2. Extract primary binary for classification
3. Handle edge cases:
   - No command: return tier 1
   - Whitespace-only command: return tier 1
   - Comment (#): skip, return tier 1
   - Command substitution: $(cmd) or `cmd`
4. Examples:
   - `cat file | grep pattern` → primary: `cat` → Tier 1
   - `rm file > /dev/null 2>&1` → primary: `rm` → Tier 4
   - `docker run ubuntu &` → primary: `docker` → Tier 6

### Verification

- [ ] Unit test: test_security_tier.py::test_command_parsing_pipes
- [ ] Unit test: test_security_tier.py::test_command_parsing_redirects
- [ ] Unit test: test_security_tier.py::test_command_parsing_quotes

---

## AC-E4-019: validate-output-schema Hook Activation

**Type:** Functional
**Related FR:** FR-E4-006
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. Hook executes as post-tool-use hook after tool completion
2. Checks if `output-schema: {...}` declared in SKILL.md
3. If no schema: return allow (hook inactive)
4. If schema present: validate tool output against schema
5. Latency: <300ms for schemas <5KB

### Test Cases

- TC-E4-019-A: Hook triggers after tool execution
- TC-E4-019-B: No schema; hook allows
- TC-E4-019-C: Schema present; validation runs
- TC-E4-019-D: Latency <300ms

### Verification

- [ ] Unit test: test_validate_schema.py::test_hook_triggers
- [ ] Unit test: test_validate_schema.py::test_no_schema_allow

---

## AC-E4-020: Schema Validation - Type Checking

**Type:** Functional
**Related FR:** FR-E4-007
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. Validate output types against schema:
   - `type: string` → must be string
   - `type: integer` → must be int
   - `type: object` → must be dict/object
   - `type: array` → must be list
   - `type: boolean` → must be bool
   - `type: number` → must be int or float
2. Type mismatch → validation error
3. Examples:
   - Schema: `{type: string}`, Output: `123` → Error
   - Schema: `{type: integer}`, Output: `"hello"` → Error

### Verification

- [ ] Unit test: test_validate_schema.py::test_type_checking (6 types)

---

## AC-E4-021: Schema Validation - Required Fields

**Type:** Functional
**Related FR:** FR-E4-007
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. Enforce `required` field list in schema
2. All fields in `required` must be present in output
3. Missing required field → validation error
4. Examples:
   - Schema: `{required: [name, age]}`, Output: `{name: "John"}` → Error
   - Schema: `{required: [name, age]}`, Output: `{name: "John", age: 30}` → Pass

### Verification

- [ ] Unit test: test_validate_schema.py::test_required_fields

---

## AC-E4-022: Schema Validation - Nested Objects & Arrays

**Type:** Functional
**Related FR:** FR-E4-007
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. Validate nested object structures:
   ```json
   {
     "type": "object",
     "properties": {
       "user": {
         "type": "object",
         "properties": {
           "name": { "type": "string" }
         }
       }
     }
   }
   ```
2. Validate array contents:
   ```json
   {
     "type": "array",
     "items": { "type": "string" },
     "minItems": 1,
     "maxItems": 10
   }
   ```
3. Nested validation errors reported with path: `output.user.name is not string`

### Verification

- [ ] Unit test: test_validate_schema.py::test_nested_objects
- [ ] Unit test: test_validate_schema.py::test_array_validation

---

## AC-E4-023: Schema Validation - Pattern & Enum

**Type:** Functional
**Related FR:** FR-E4-007
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. Validate string patterns:
   ```json
   {
     "type": "string",
     "pattern": "^[a-z0-9]+$"
   }
   ```
2. Validate enum values:
   ```json
   {
     "type": "string",
     "enum": ["success", "warning", "failure"]
   }
   ```
3. Pattern mismatch → error
4. Value not in enum → error

### Verification

- [ ] Unit test: test_validate_schema.py::test_pattern_validation
- [ ] Unit test: test_validate_schema.py::test_enum_validation

---

## AC-E4-024: Schema Validation - Blocking vs Warning

**Type:** Functional
**Related FR:** FR-E4-007
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. If `enforce-schema: true` (default):
   - Validation failure blocks stage completion
   - Tool output discarded
   - Error message suggests schema correction
2. If `enforce-schema: false`:
   - Validation failure logged as warning only
   - Stage completion allowed
   - Tool output passed through
3. Both modes log errors to AuditEvent
4. Examples:
   - `enforce-schema: true` + invalid output → stage fails
   - `enforce-schema: false` + invalid output → stage succeeds with warning

### Verification

- [ ] Unit test: test_validate_schema.py::test_blocking_mode
- [ ] Unit test: test_validate_schema.py::test_warning_mode

---

## AC-E4-025: validate-output-schema Integration

**Type:** Functional
**Related FR:** FR-E4-006
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. Hook receives tool output from PipelineState
2. Output format determined by `output-format` in SKILL.md (json|yaml|text)
3. Parse output according to format (JSON or YAML parsing)
4. Validate parsed output against schema
5. Return HookResult:
   - `status: allow` if valid
   - `status: block` if invalid + `enforce-schema: true`
   - `context.errors: list[str]` with validation errors

### Verification

- [ ] Unit test: test_validate_schema.py::test_json_output
- [ ] Unit test: test_validate_schema.py::test_yaml_output
- [ ] Unit test: test_validate_schema.py::test_invalid_json

---

## AC-E4-026: Output Schema Configuration in SKILL.md

**Type:** Functional
**Related FR:** FR-E4-007
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P0

### Criteria

1. SKILL.md declares output schema in `output-schema` section
2. Schema format: JSON Schema Draft 7
3. Optional `output-format: json|yaml|text` (default: json)
4. Optional `enforce-schema: true|false` (default: true)
5. Example:
   ```yaml
   output-schema:
     type: object
     required: [status, result]
     properties:
       status:
         type: string
         enum: [success, warning, failure]
       result:
         type: object
   enforce-schema: true
   ```

### Verification

- [ ] Unit test: test_validate_schema.py::test_skill_md_config

---

## AC-E4-027: Output Validation Error Messages

**Type:** Functional
**Related FR:** FR-E4-007
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P1

### Criteria

1. Error messages clear + actionable:
   - "Field 'status' is required"
   - "Field 'count' must be integer, got string"
   - "Field 'name' must match pattern '^[a-z]+'
2. Include path to error: "output.user.name is not string"
3. Suggest schema correction if applicable
4. Log full error chain for debugging

### Verification

- [ ] Unit test: test_validate_schema.py::test_error_messages
- [ ] Manual test: review error messages for clarity

---

## AC-E4-028: Output Validation with Different Formats

**Type:** Functional
**Related FR:** FR-E4-006
**Related Story:** STORY-E4-003
**Status:** New
**Priority:** P1

### Criteria

1. Validate JSON output:
   - Parse JSON string to object
   - Validate object against schema
2. Validate YAML output:
   - Parse YAML string to object
   - Validate object against schema
3. Validate plain text output:
   - Wrap in object: `{value: text}`
   - Validate against schema (optional, likely `enforce-schema: false`)
4. Examples:
   - JSON: `{"status": "success", "result": {...}}`
   - YAML: `status: success\nresult: {...}`
   - Text: Raw text output (limited schema validation)

### Verification

- [ ] Unit test: test_validate_schema.py::test_json_format
- [ ] Unit test: test_validate_schema.py::test_yaml_format
- [ ] Unit test: test_validate_schema.py::test_text_format

---

## AC-E4-029: update-pipeline-state Hook - PipelineState Fields

**Type:** Functional
**Related FR:** FR-E4-008
**Related Story:** STORY-E4-005
**Status:** New
**Priority:** P0

### Criteria

1. Hook updates PipelineState after tool execution:
   - `last_tool_executed: str` ← context.tool_name
   - `last_stage_completed: str` ← stage ID
   - `tool_execution_count: int` ← increment by 1
   - `stage_completion_timestamp: ISO8601` ← datetime.now()
   - `last_execution_status: success|warning|failure` ← tool result
2. Fields validated before persistence
3. Atomic update: all fields updated together or none
4. Latency: <150ms

### Test Cases

- TC-E4-029-A: Fields updated correctly
- TC-E4-029-B: Timestamps in ISO8601 format
- TC-E4-029-C: Atomic updates
- TC-E4-029-D: Latency <150ms

### Verification

- [ ] Unit test: test_update_state.py::test_state_fields_updated
- [ ] Unit test: test_update_state.py::test_atomic_update

---

## AC-E4-030: update-pipeline-state Hook - AuditEvent Creation

**Type:** Functional
**Related FR:** FR-E4-008
**Related Story:** STORY-E4-005
**Status:** New
**Priority:** P0

### Criteria

1. AuditEvent created with fields:
   - `timestamp: ISO8601` ← datetime.now()
   - `event_type: tool_execution`
   - `actor: system|user` (depends on context)
   - `action: execute_tool`
   - `resource: skill_name` ← context.tool_name
   - `result: success|warning|failure` ← execution result
   - `context: dict` ← hook-specific data (tool output, state changes)
2. AuditEvent persisted to session log (memory + disk)
3. iCloud sync triggered immediately after persist
4. Sync retry logic: exponential backoff, max 3 retries
5. If iCloud unavailable: fallback to local storage

### Test Cases

- TC-E4-030-A: AuditEvent created with correct fields
- TC-E4-030-B: AuditEvent persisted to disk
- TC-E4-030-C: iCloud sync triggered
- TC-E4-030-D: iCloud sync retry + fallback

### Verification

- [ ] Unit test: test_update_state.py::test_audit_event_created
- [ ] Unit test: test_update_state.py::test_audit_event_persisted
- [ ] Unit test: test_update_state.py::test_icloud_sync

---

## AC-E4-031: save-session-summary Hook - HandoffDocument

**Type:** Functional
**Related FR:** FR-E4-010
**Related Story:** STORY-E4-007
**Status:** New
**Priority:** P0

### Criteria

1. HandoffDocument generated with sections:
   - **Session Metadata:** session_id, start_time, end_time, duration
   - **Tool Summary:** list of executed tools with status (success|warning|failure)
   - **State Snapshot:** PipelineState at session end
   - **Security Events:** all tier 6+ commands + user overrides
   - **Audit Trail:** 30 most recent AuditEvents
   - **Recommendations:** schema violations, doc read failures, etc.
2. Format: Markdown file, human-readable + machine-parseable
3. Written to: `sessions/{session_id}/handoff.md`
4. File includes date, session ID, key metrics

### Test Cases

- TC-E4-031-A: HandoffDocument generated from AuditEvents
- TC-E4-031-B: All sections present and populated
- TC-E4-031-C: Markdown formatted correctly
- TC-E4-031-D: File written to correct location

### Verification

- [ ] Unit test: test_session_hooks.py::test_handoff_generation
- [ ] Unit test: test_session_hooks.py::test_handoff_content
- [ ] Manual test: review generated handoff.md file

---

## AC-E4-032: save-session-summary Hook - Artifact Persistence

**Type:** Functional
**Related FR:** FR-E4-010
**Related Story:** STORY-E4-007
**Status:** New
**Priority:** P0

### Criteria

1. Compress session directory: tar.gz format
2. Upload to iCloud with:
   - Session ID in filename: `session-{session_id}.tar.gz`
   - Conflict resolution: last-write-wins
   - Retry logic: exponential backoff, max 3 retries
3. If iCloud unavailable: fallback to local storage `sessions/{session_id}/`
4. Log upload status to AuditEvent
5. Return HookResult with path + upload status

### Test Cases

- TC-E4-032-A: Session directory compressed
- TC-E4-032-B: Upload to iCloud succeeds
- TC-E4-032-C: iCloud unavailable; fallback to local
- TC-E4-032-D: Upload status logged to AuditEvent

### Verification

- [ ] Unit test: test_session_hooks.py::test_compression
- [ ] Unit test: test_session_hooks.py::test_icloud_upload
- [ ] Unit test: test_session_hooks.py::test_fallback_to_local

---

## AC-E4-033: Survival Architecture v3.0 Template Sections

**Type:** Functional
**Related FR:** FR-E4-011
**Related Story:** STORY-E4-001
**Status:** New
**Priority:** P0

### Criteria

1. v3.0 template includes new sections:
   - `survival-architecture-version: 3.0`
   - `hooks-declared: [list of hooks]`
   - `context-budget: {stage-1: {...}, stage-2: {...}}`
   - `security-tier: [1-10]`
   - `output-schema: {JSON Schema}`
   - `enforce-schema: true|false`
2. All sections optional; v2.2 compatibility maintained
3. Template file: `templates/skill-template-v3.0.md`
4. Template includes inline documentation + examples

### Test Cases

- TC-E4-033-A: v3.0 template has all sections
- TC-E4-033-B: Sections documented
- TC-E4-033-C: v2.2 compatibility maintained
- TC-E4-033-D: Template parseable and valid

### Verification

- [ ] Unit test: test_skill_md_parser.py::test_v3_template_parsing
- [ ] Manual test: review template for completeness

---

## AC-E4-034: Hook Declarations in SKILL.md

**Type:** Functional
**Related FR:** FR-E4-011
**Related Story:** STORY-E4-001
**Status:** New
**Priority:** P0

### Criteria

1. SKILL.md declares hooks applicable to skill:
   ```yaml
   hooks-declared:
     - enforce-doc-read
     - security-tier-check
     - validate-output-schema
   ```
2. Hooks listed by name (must match registered hooks)
3. Parser validates hook names
4. Hooks not declared: disabled for that skill
5. All skills can optionally declare hooks

### Verification

- [ ] Unit test: test_skill_md_parser.py::test_hook_declarations
- [ ] Unit test: test_skill_md_parser.py::test_invalid_hook_name

---

## AC-E4-035: Context Budget & Security Tier in SKILL.md

**Type:** Functional
**Related FR:** FR-E4-011
**Related Story:** STORY-E4-001
**Status:** New
**Priority:** P0

### Criteria

1. SKILL.md declares context budget:
   ```yaml
   context-budget:
     stage-1:
       max-tokens: 4000
       timeout-seconds: 30
   ```
2. SKILL.md declares security tier:
   ```yaml
   security-tier: 4  # Write/create
   ```
3. Parser extracts both fields
4. Used by hooks for enforcement + classification
5. Optional; defaults applied if missing

### Verification

- [ ] Unit test: test_skill_md_parser.py::test_context_budget_parsing
- [ ] Unit test: test_skill_md_parser.py::test_security_tier_parsing

---

## AC-E4-036: SKILL.md v2.2 → v3.0 Migration Script

**Type:** Functional
**Related FR:** FR-E4-012
**Related Story:** STORY-E4-008
**Status:** New
**Priority:** P0

### Criteria

1. Script: `./scripts/upgrade-skill-v2-to-v3.py`
2. Processes all SKILL.md files in `skills/` directory
3. For each file:
   - Generate v3.0 sections with defaults
   - Insert into v3.0 location
   - Backup original: `SKILL.md.v2.2.bak`
4. Output: upgrade report with required reviews per skill
5. No breaking changes; v2.2 files remain valid

### Test Cases

- TC-E4-036-A: Script runs without errors
- TC-E4-036-B: v3.0 sections inserted correctly
- TC-E4-036-C: Original files backed up
- TC-E4-036-D: Upgrade report generated

### Verification

- [ ] Unit test: test_migration.py::test_upgrade_script
- [ ] Integration test: upgrade all 12 SKILL.md files

---

## AC-E4-037: Hook Latency Budget

**Type:** Non-Functional
**Related FR:** FR-E4-018
**Related Story:** All
**Status:** New
**Priority:** P0

### Criteria

1. Individual hook latencies:
   - enforce-doc-read: <100ms
   - security-tier-check: <200ms
   - validate-output-schema: <300ms
   - update-pipeline-state: <150ms
2. Combined pre-tool hooks: <500ms
3. Combined post-tool hooks: <500ms
4. Measured on standard hardware (2-core, 4GB RAM)
5. p95 latency over 1000 executions

### Verification

- [ ] Performance test: test_performance.py (all hooks)
- [ ] Latency report: per-hook, p50/p95/p99

---

## AC-E4-038: Hook Memory Usage

**Type:** Non-Functional
**Related FR:** FR-E4-018
**Related Story:** All
**Status:** New
**Priority:** P1

### Criteria

1. Each hook uses <50MB memory during execution
2. No memory leaks across 1000 hook executions
3. Measured using RSS (resident set size)

### Verification

- [ ] Memory test: test_memory.py (all hooks)
- [ ] Memory profiling: valgrind or Python memory_profiler

---

## AC-E4-039: Backward Compatibility with v2.2

**Type:** Functional
**Related FR:** FR-E4-019
**Related Story:** STORY-E4-008
**Status:** New
**Priority:** P0

### Criteria

1. All 12 existing v2.2 SKILL.md files execute unchanged
2. Behavior identical pre + post upgrade
3. Hooks default-disabled for v2.2 files (no enforcement)
4. No breaking changes in tool execution
5. v3.0 optional; not mandatory

### Test Cases

- TC-E4-039-A through TC-E4-039-L: Test all 12 v2.2 SKILL.md files pre + post upgrade

### Verification

- [ ] Regression test: test_compatibility.py::test_v2_2_skill_md_files (12 tests)

---

## AC-E4-040: Test Coverage ≥95%

**Type:** Functional
**Related FR:** FR-E4-020
**Related Story:** STORY-E4-009
**Status:** New
**Priority:** P0

### Criteria

1. Hook modules: ≥95% code coverage
2. Test files: test_*.py in tests/ directory
3. Measured with pytest-cov
4. Exclude: config loading, external API mocks
5. Coverage report generated: coverage.html

### Verification

- [ ] Coverage test: pytest --cov=hooks --cov-report=html
- [ ] Coverage report: ≥95% overall

---

## AC-E4-041: Test Suite Execution Speed

**Type:** Non-Functional
**Related FR:** FR-E4-020
**Related Story:** STORY-E4-009
**Status:** New
**Priority:** P1

### Criteria

1. Full test suite runs in <60 seconds
2. Includes: 5 test modules, 40+ test cases, 30+ command fixtures
3. Measured on standard CI hardware
4. Individual test max 5 seconds

### Verification

- [ ] Performance test: time pytest -v
- [ ] Report: total execution time

---

## AC Summary by Category

| Category | AC Count | Status |
|----------|----------|--------|
| enforce-doc-read | 4 | New |
| security-tier-check | 10 | New |
| validate-output-schema | 6 | New |
| update-pipeline-state | 2 | New |
| SessionStart | 4 | New |
| save-session-summary | 2 | New |
| Survival v3.0 | 3 | New |
| Migration | 1 | New |
| Non-Functional | 3 | New |
| Backward Compatibility | 1 | New |
| **Total** | **41** | |

---

**Document Owner:** QA Team
**Last Updated:** 2026-03-14
**Version:** 1.0
