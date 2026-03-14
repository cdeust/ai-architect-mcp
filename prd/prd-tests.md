# PRD Test Specification — AI Architect Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**PRD Type:** Full Scope Overview (Test Strategy, Not Full Implementations)

---

## Test Strategy Overview

This document defines the **test strategy** for all 6 epics. Full test implementations (with actual code) will be generated in per-epic implementation PRDs. This overview establishes naming conventions, coverage targets, and the traceability matrix.

**Existing Test Baseline:**
- 42 test files, 2,933 LOC
- Framework: pytest + pytest-asyncio
- All tests deterministic (no external dependencies)
- Fixtures in `tests/conftest.py` and `tests/fixtures/`

**Target After All Epics:**
- ~70+ test files, ~5,000+ LOC estimated
- Coverage: ≥ 85% line coverage for all new code
- All new tests follow existing patterns

---

## PART A: Coverage Tests by Epic

### Epic 1: Plan Interview — Test Plan

| Test File | Type | What It Tests | AC Coverage |
|-----------|------|---------------|-------------|
| `test_interview/test_dimensions.py` | Unit | 10 dimension definitions and evaluation logic | AC-001, AC-004 |
| `test_interview/test_scorer.py` | Unit | Scoring engine with configurable thresholds | AC-004, AC-005 |
| `test_interview/test_gate.py` | Unit | Gate logic: block on failure, proceed on pass | AC-002 |
| `test_interview/test_context_integration.py` | Integration | StageContext read (Stage 4) and write (Stage 5) | AC-003 |
| `test_interview/test_tools.py` | Unit | MCP tool registration and invocation | AC-001 |
| `test_interview/test_stage_flow.py` | Integration | Full Stage 4 → 4.5 → 5 pipeline flow | AC-001–AC-005 |

**Naming Convention:** `test_dimension_{dimension_name}`, `test_gate_blocks_on_failure`, `test_gate_proceeds_on_pass`

### Epic 2: Memory Model — Test Plan

| Test File | Type | What It Tests | AC Coverage |
|-----------|------|---------------|-------------|
| `test_memory/test_pipeline_state.py` | Unit | PipelineState model creation, serialization | AC-006 |
| `test_memory/test_experience_pattern.py` | Unit | ExperiencePattern model, decay calculation | AC-008, AC-009 |
| `test_memory/test_audit_event.py` | Unit | AuditEvent creation, immutability enforcement | AC-012, AC-013 |
| `test_memory/test_cloudkit_adapter.py` | Integration | CloudKit sync for all 3 models | AC-006, AC-007 |
| `test_memory/test_conflict_resolution.py` | Integration | Last-writer-wins conflict resolution | AC-007 |
| `test_memory/test_progressive_disclosure.py` | Unit | L1/L2/L3 level switching | AC-010 |
| `test_memory/test_budget_monitor.py` | Unit | 70% and 93% threshold triggers | AC-010, AC-011 |
| `test_memory/test_auto_handoff.py` | Integration | HandoffDocument generation at 93% | AC-011 |

**Key Test Patterns:**
- Decay tests use deterministic timestamps (not `datetime.now()`)
- Immutability tests verify both programmatic and adapter-level rejection
- CloudKit tests use mock adapter (real CloudKit testing is manual)

### Epic 3: Consensus — Test Plan

| Test File | Type | What It Tests | AC Coverage |
|-----------|------|---------------|-------------|
| `test_verification/test_bayesian_consensus.py` | Unit | Bayesian posterior calculation, prior updating | AC-014 |
| `test_verification/test_majority_voting.py` | Unit | Threshold agreement, tie-breaking | AC-016, AC-017 |
| `test_verification/test_consensus_routing.py` | Unit | Enum routing to correct algorithm | AC-015, AC-017 |

**Test Data:** Deterministic fixtures with known inputs → expected outputs (bit-for-bit matching per project instructions).

### Epic 4: Hooks — Test Plan

| Test File | Type | What It Tests | AC Coverage |
|-----------|------|---------------|-------------|
| `test_hooks/test_enforce_doc_read.py` | Unit | Block writes before SKILL.md read, allow after | AC-018, AC-019 |
| `test_hooks/test_security_tier.py` | Unit | Tier classification for known commands | AC-020, AC-021 |
| `test_hooks/test_validate_schema.py` | Unit | Output schema validation against contracts | — |
| `test_hooks/test_update_state.py` | Integration | PipelineState update + AuditEvent logging | AC-012 |
| `test_hooks/test_session_hooks.py` | Integration | SessionStart + save-session-summary lifecycle | AC-022, AC-023 |

**Security Tier Test Matrix:**
- Tier 1 commands: `git status`, `ls`, `cat` → allow
- Tier 5 commands: `git push`, `npm publish` → allow + log
- Tier 8+ commands: `rm -rf`, system modifications → block

### Epic 5: GitHub Actions — Test Plan

| Test File | Type | What It Tests | AC Coverage |
|-----------|------|---------------|-------------|
| `test_adapters/test_github_actions_adapter.py` | Unit | All 5 port implementations | AC-024 |
| `test_adapters/test_gha_git_ops.py` | Unit | Git operations in Actions context | AC-024 |
| `test_adapters/test_gha_github_ops.py` | Unit | PR creation, check runs | AC-025, AC-028 |
| `test_adapters/test_gha_context_ops.py` | Unit | Artifact-based context storage | AC-024 |
| `test_integration/test_gha_pipeline.py` | E2E | Issue → Pipeline → PR flow | AC-024, AC-025 |
| `test_integration/test_gha_nightly.py` | E2E | Nightly discovery + PR creation | AC-026, AC-027 |

### Epic 6: Python Migration — Test Plan

| Test File | Type | What It Tests | AC Coverage |
|-----------|------|---------------|-------------|
| `test_package/test_cli.py` | Unit | CLI entry point, serve command | AC-031 |
| `test_package/test_config.py` | Unit | TOML loader, env var override | AC-032, AC-033 |
| `test_package/test_tool_registration.py` | Integration | All 32 tools register in package | AC-031 |
| `test_package/test_algorithm_access.py` | Integration | All algorithms accessible | — |
| `test_package/test_install.py` | E2E | pip install + serve works | AC-030, AC-031 |
| `test_package/test_node_compatibility.py` | Integration | Response schema matches Node.js | AC-035 |

---

## PART B: AC Validation Tests

Each AC from the PRD maps to at least one validation test. Full implementations provided in per-epic PRDs.

| AC | Test Method | Test Type | Validation Approach |
|----|------------|-----------|---------------------|
| AC-001 | `test_all_dimensions_evaluated` | Unit | Assert 10 DimensionScore objects returned |
| AC-002 | `test_gate_blocks_on_failure` | Integration | Set 1 dimension below threshold, assert StageError |
| AC-003 | `test_enriched_context_written` | Integration | Assert StageContext contains dimension data |
| AC-004 | `test_dimension_score_range` | Unit | Assert all scores in [0.0, 1.0] |
| AC-005 | `test_failing_dimension_has_findings` | Unit | Assert findings list non-empty on failure |
| AC-006 | `test_pipeline_state_sync` | Integration | Write on mock device A, read on mock device B |
| AC-007 | `test_conflict_resolution_last_writer_wins` | Integration | Simulate concurrent writes, assert latest wins |
| AC-008 | `test_half_life_decay` | Unit | 30-day half-life → 50% relevance (±1%) |
| AC-009 | `test_pattern_reinforcement` | Unit | Access pattern → last_accessed_at updates |
| AC-010 | `test_progressive_disclosure_70_percent` | Unit | At 70% budget → L3 demoted to L2 |
| AC-011 | `test_auto_handoff_at_93_percent` | Integration | At 93% budget → HandoffDocument generated |
| AC-012 | `test_audit_event_per_stage` | Integration | Stage complete → AuditEvent appended |
| AC-013 | `test_audit_event_immutability` | Unit | Attempt update/delete → error raised |
| AC-014 | `test_bayesian_posterior` | Unit | Known scores + prior → expected posterior |
| AC-015 | `test_bayesian_routing` | Unit | `BAYESIAN` enum → BayesianConsensus called |
| AC-016 | `test_majority_voting_basic` | Unit | 3/5 above threshold → majority pass |
| AC-017 | `test_majority_voting_tie_break` | Unit | 2/4 tie → tie-breaker applied |
| AC-018 | `test_write_blocked_before_read` | Unit | No SKILL.md read → write rejected |
| AC-019 | `test_write_allowed_after_read` | Unit | SKILL.md read → write proceeds |
| AC-020 | `test_tier_10_blocked` | Unit | `rm -rf /` → blocked |
| AC-021 | `test_tier_1_allowed_fast` | Unit | `git status` → allowed, < 200ms |
| AC-022 | `test_session_end_saves_handoff` | Integration | Session end → HandoffDocument written |
| AC-023 | `test_session_start_offers_resume` | Integration | HandoffDocument exists → resume offered |
| AC-024 | `test_issue_triggers_pipeline` | E2E | Issue with label → pipeline starts |
| AC-025 | `test_pipeline_creates_pr` | E2E | Successful run → PR created |
| AC-026 | `test_nightly_discovery` | E2E | Cron trigger → discovery findings reported |
| AC-027 | `test_nightly_auto_pr` | E2E | High-threshold finding → PR auto-created |
| AC-028 | `test_check_run_updated` | Integration | Stage complete → check run status updated |
| AC-029 | `test_check_run_failure` | Integration | Stage failure → check run shows failure |
| AC-030 | `test_pip_install` | E2E | `pip install` succeeds in < 30s |
| AC-031 | `test_serve_starts` | E2E | `ai-architect-mcp serve` starts, tools registered |
| AC-032 | `test_toml_config_loaded` | Unit | Config file → settings applied |
| AC-033 | `test_env_var_override` | Unit | Env var overrides TOML value |
| AC-034 | `test_migration_guide_tools_map` | Integration | All 13 Node.js tools have Python equivalents |
| AC-035 | `test_response_schema_compatibility` | Integration | Same input → same output schema |

---

## PART C: Traceability Matrix

| AC ID | AC Title | Test Name(s) | Test Type | Status |
|-------|----------|-------------|-----------|--------|
| AC-001 | Full Dimension Evaluation | `test_all_dimensions_evaluated` | Unit | Pending |
| AC-002 | Gate Blocking | `test_gate_blocks_on_failure` | Integration | Pending |
| AC-003 | Context Pass-Through | `test_enriched_context_written` | Integration | Pending |
| AC-004 | Dimension Score Output | `test_dimension_score_range` | Unit | Pending |
| AC-005 | Failing Dimension Report | `test_failing_dimension_has_findings` | Unit | Pending |
| AC-006 | Cross-Device Sync | `test_pipeline_state_sync` | Integration | Pending |
| AC-007 | Conflict Resolution | `test_conflict_resolution_last_writer_wins` | Integration | Pending |
| AC-008 | Half-Life Decay | `test_half_life_decay` | Unit | Pending |
| AC-009 | Pattern Reinforcement | `test_pattern_reinforcement` | Unit | Pending |
| AC-010 | Progressive Disclosure 70% | `test_progressive_disclosure_70_percent` | Unit | Pending |
| AC-011 | Auto-Handoff 93% | `test_auto_handoff_at_93_percent` | Integration | Pending |
| AC-012 | Audit Event Logging | `test_audit_event_per_stage` | Integration | Pending |
| AC-013 | Audit Event Immutability | `test_audit_event_immutability` | Unit | Pending |
| AC-014 | Bayesian Posterior | `test_bayesian_posterior` | Unit | Pending |
| AC-015 | Bayesian Routing | `test_bayesian_routing` | Unit | Pending |
| AC-016 | Majority Voting Basic | `test_majority_voting_basic` | Unit | Pending |
| AC-017 | Majority Voting Tie | `test_majority_voting_tie_break` | Unit | Pending |
| AC-018 | Write Blocked Before Read | `test_write_blocked_before_read` | Unit | Pending |
| AC-019 | Write Allowed After Read | `test_write_allowed_after_read` | Unit | Pending |
| AC-020 | Tier 10 Blocked | `test_tier_10_blocked` | Unit | Pending |
| AC-021 | Tier 1 Allowed Fast | `test_tier_1_allowed_fast` | Unit | Pending |
| AC-022 | Session End Handoff | `test_session_end_saves_handoff` | Integration | Pending |
| AC-023 | Session Start Resume | `test_session_start_offers_resume` | Integration | Pending |
| AC-024 | Issue Triggers Pipeline | `test_issue_triggers_pipeline` | E2E | Pending |
| AC-025 | Pipeline Creates PR | `test_pipeline_creates_pr` | E2E | Pending |
| AC-026 | Nightly Discovery | `test_nightly_discovery` | E2E | Pending |
| AC-027 | Nightly Auto PR | `test_nightly_auto_pr` | E2E | Pending |
| AC-028 | Check Run Updated | `test_check_run_updated` | Integration | Pending |
| AC-029 | Check Run Failure | `test_check_run_failure` | Integration | Pending |
| AC-030 | pip Install | `test_pip_install` | E2E | Pending |
| AC-031 | Serve Starts | `test_serve_starts` | E2E | Pending |
| AC-032 | TOML Config Loaded | `test_toml_config_loaded` | Unit | Pending |
| AC-033 | Env Var Override | `test_env_var_override` | Unit | Pending |
| AC-034 | Migration Tools Map | `test_migration_guide_tools_map` | Integration | Pending |
| AC-035 | Schema Compatibility | `test_response_schema_compatibility` | Integration | Pending |

**Traceability Summary:** 35/35 ACs mapped to tests. 0 orphan ACs.

---

## Test Data Requirements

| Dataset | Purpose | Size | Location |
|---------|---------|------|----------|
| `dimension_scores.json` | Fixture for dimension evaluation tests | 10 entries | `tests/fixtures/interview/` |
| `experience_decay_timeline.json` | Fixture for decay calculation verification | 20 time points | `tests/fixtures/memory/` |
| `consensus_inputs.json` | Fixture for Bayesian/MV algorithm verification | 15 score sets | `tests/fixtures/verification/` |
| `security_tier_commands.json` | Fixture for tier classification tests | 30 commands | `tests/fixtures/hooks/` |
| `node_tool_responses.json` | Fixture for Node.js compatibility testing | 13 response schemas | `tests/fixtures/package/` |

---

## Coverage Targets

| Category | Current | Target | Measurement |
|----------|---------|--------|-------------|
| Line coverage (new code) | N/A | ≥ 85% | `pytest --cov` |
| Branch coverage (new code) | N/A | ≥ 75% | `pytest --cov --cov-branch` |
| AC coverage | 0/35 | 35/35 | Traceability matrix |
| Test isolation | 100% | 100% | No shared mutable state |
