# PRD User Stories — AI Architect Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**PRD Type:** Full Scope Overview

---

## User Personas

| Persona | Description | Primary Epics |
|---------|-------------|---------------|
| **Indie Dev** | Solo developer using AI Architect to generate specs for personal projects | Epics 1, 2, 3 |
| **Professional** | Engineering team member running nightly pipeline improvements | Epics 4, 5, 6 |
| **Enterprise Architect** | Technical leader enforcing architecture standards across teams | Epics 1, 4, 5 |
| **Educator** | University instructor using pipeline as a teaching tool | Epic 6 |
| **CI/CD Engineer** | DevOps engineer integrating AI Architect into GitHub Actions | Epic 5 |
| **Platform Contributor** | Open-source contributor extending AI Architect | Epics 3, 6 |

---

## Epic 1: Plan Interview Stage (Stage 4.5)

### US-001: Plan Interview Blocks Incomplete PRDs

**As an** Enterprise Architect,
**I want** the pipeline to interrogate PRD plans across 10 dimensions before allowing review,
**so that** incomplete or poorly-thought-out specifications are caught before engineering effort begins.

**Acceptance Criteria:**

- AC-001: Given a completed Stage 4 output, when Stage 4.5 runs, then all 10 dimensions are evaluated and scored.
- AC-002: Given any dimension scores below its pass threshold, when the pipeline attempts to advance to Stage 5, then progression is blocked with a detailed report of failing dimensions.
- AC-003: Given all dimensions pass, when Stage 4.5 completes, then enriched context is written to StageContextPort for Stage 5 consumption.

### US-002: Dimension-Level Scoring

**As an** Indie Dev,
**I want** to see which specific dimensions of my plan are weak,
**so that** I can iteratively improve before the pipeline proceeds.

**Acceptance Criteria:**

- AC-004: Given a Stage 4.5 run, when results are returned, then each dimension has a numeric score (0.0–1.0) and a pass/fail indicator.
- AC-005: Given a failing dimension, when the report is generated, then it includes specific findings and suggested improvements.

---

## Epic 2: Four-Layer Memory Model

### US-003: Cross-Device Pipeline State

**As a** Professional running AI Architect on Mac and reviewing on iPad,
**I want** pipeline state to sync across my Apple devices via iCloud,
**so that** I can start a pipeline run on one device and monitor or continue on another.

**Acceptance Criteria:**

- AC-006: Given a PipelineState update on Mac, when iCloud sync completes, then the same state is readable on iPad within 5 seconds.
- AC-007: Given a sync conflict (concurrent updates from 2 devices), when CloudKit detects the conflict, then the most recent timestamp wins and both devices converge.

### US-004: Experience Pattern Decay

**As an** Enterprise Architect,
**I want** the system to naturally forget outdated patterns while retaining recent learnings,
**so that** recommendations evolve with the codebase rather than accumulating stale knowledge.

**Acceptance Criteria:**

- AC-008: Given an experience pattern with half-life of 30 days, when 30 days have elapsed, then its relevance score is 50% of the initial value.
- AC-009: Given an experience pattern accessed by the pipeline, when it is used in a decision, then its half-life resets (reinforcement learning).

### US-005: Progressive Context Loading

**As an** Indie Dev with limited context window,
**I want** the system to load only the context I need at each moment,
**so that** I don't waste tokens on irrelevant information.

**Acceptance Criteria:**

- AC-010: Given context usage at 70%, when the budget monitor triggers, then the system switches from L3 full docs to L2 summaries.
- AC-011: Given context usage at 93%, when the budget monitor triggers, then a HandoffDocument is auto-generated and the session can be resumed later.

### US-006: Immutable Audit Trail

**As an** Enterprise Architect,
**I want** every pipeline action logged immutably,
**so that** I have a complete audit trail for compliance and debugging.

**Acceptance Criteria:**

- AC-012: Given any stage completion, when the pipeline advances, then an AuditEvent is appended with who, what, when, where, and outcome fields.
- AC-013: Given an AuditEvent in the log, when any operation attempts to modify or delete it, then the operation is rejected.

---

## Epic 3: Consensus Algorithm Completion

### US-007: Bayesian Consensus for Uncertain Claims

**As a** Platform Contributor,
**I want** Bayesian consensus available as a verification option,
**so that** claims with high uncertainty can be evaluated using prior probability updating.

**Acceptance Criteria:**

- AC-014: Given a set of judge scores and a Beta prior, when Bayesian consensus runs, then it produces a posterior distribution with mean and credible interval.
- AC-015: Given the `ConsensusAlgorithm.BAYESIAN` enum value, when the verification engine routes to it, then the Bayesian implementation is invoked.

### US-008: Majority Voting for Simple Claims

**As a** Professional,
**I want** a fast majority voting option for simple, low-complexity claims,
**so that** verification doesn't over-invest in trivial checks.

**Acceptance Criteria:**

- AC-016: Given 5 judge scores and a >50% threshold, when majority voting runs, then it returns the majority opinion with agreement percentage.
- AC-017: Given a tie (e.g., 2 vs 2 with 1 abstain), when majority voting encounters a tie, then the tie-breaking rule (configurable: highest confidence, random, escalate to debate) is applied.

---

## Epic 4: Hook System Expansion

### US-009: Documentation Enforcement

**As an** Enterprise Architect,
**I want** the pipeline to refuse write operations until the developer has read the stage's SKILL.md,
**so that** architectural contracts are understood before implementation begins.

**Acceptance Criteria:**

- AC-018: Given a session where SKILL.md has NOT been read, when a write tool is invoked, then the hook blocks the operation and returns an error directing the developer to read the SKILL.md first.
- AC-019: Given a session where SKILL.md HAS been read, when a write tool is invoked, then the hook allows the operation to proceed.

### US-010: Security-Tiered Bash Execution

**As a** Professional,
**I want** bash commands assessed against a security threat model before execution,
**so that** dangerous operations (tier 8–10) are blocked while routine operations proceed.

**Acceptance Criteria:**

- AC-020: Given a bash command `rm -rf /`, when the security tier check runs, then it classifies as tier 10 and blocks execution.
- AC-021: Given a bash command `git status`, when the security tier check runs, then it classifies as tier 1 and allows execution with < 200ms overhead.

### US-011: Automatic Session Handoff

**As an** Indie Dev,
**I want** the session state automatically saved when I close the app,
**so that** I can resume exactly where I left off next time.

**Acceptance Criteria:**

- AC-022: Given a session ending (app close or session timeout), when the save-session-summary hook triggers, then a HandoffDocument is written with full session state.
- AC-023: Given a HandoffDocument from a previous session, when a new session starts, then the SessionStart hook offers to resume from that document.

---

## Epic 5: GitHub Actions Client

### US-012: Issue-Triggered Pipeline

**As a** CI/CD Engineer,
**I want** GitHub issues labeled `ai-architect` to automatically trigger a full pipeline run,
**so that** the team gets merge-ready PRs without manual intervention.

**Acceptance Criteria:**

- AC-024: Given a GitHub issue with label `ai-architect`, when the workflow triggers, then a full Stage 0–10 pipeline run executes.
- AC-025: Given a successful pipeline run, when Stage 10 completes, then a PR is created with the verification report attached.

### US-013: Nightly Improvement Runs

**As a** Professional,
**I want** the pipeline to run nightly and find improvement opportunities,
**so that** the codebase continuously improves without manual triggering.

**Acceptance Criteria:**

- AC-026: Given a configured nightly cron schedule, when the schedule triggers, then the pipeline runs Discovery (Stage 1) and reports findings as GitHub issues.
- AC-027: Given findings above a configured threshold, when the nightly run identifies them, then it proceeds through the full pipeline and creates PRs.

### US-014: Status Reporting

**As a** CI/CD Engineer,
**I want** pipeline progress visible as GitHub check runs,
**so that** I can monitor pipeline execution without accessing internal logs.

**Acceptance Criteria:**

- AC-028: Given a running pipeline, when each stage completes, then a GitHub check run is updated with the stage result.
- AC-029: Given a pipeline failure, when any stage fails, then the check run shows failure with the stage name and error summary.

---

## Epic 6: Python MCP Server Migration

### US-015: pip-Installable Package

**As an** Educator,
**I want** to install AI Architect via `pip install ai-architect-mcp`,
**so that** students can set up the tool in minutes without complex build processes.

**Acceptance Criteria:**

- AC-030: Given a Python 3.12+ environment, when `pip install ai-architect-mcp` runs, then all dependencies install successfully in < 30 seconds.
- AC-031: Given the package installed, when `ai-architect-mcp serve` is executed, then the FastMCP server starts and registers all 32 tools.

### US-016: Configuration via TOML

**As a** Professional,
**I want** to configure the server via a TOML file and environment variables,
**so that** I can customize behavior without modifying source code.

**Acceptance Criteria:**

- AC-032: Given an `ai-architect.toml` file in the working directory, when the server starts, then it reads configuration from the file.
- AC-033: Given an environment variable `AI_ARCHITECT_LOG_LEVEL=debug`, when it overrides a TOML value, then the environment variable takes precedence.

### US-017: Migration from Node.js

**As a** Platform Contributor,
**I want** a clear migration guide from the Node.js server to the Python server,
**so that** I can switch existing integrations without breaking changes.

**Acceptance Criteria:**

- AC-034: Given the migration guide, when a user follows it, then all 13 Node.js tools map to their Python equivalents.
- AC-035: Given the same MCP client, when it connects to the Python server instead of Node.js, then all tool calls produce identical response schemas.

---

## Story-to-Epic Mapping

| Story | Epic | Persona | Priority |
|-------|------|---------|----------|
| US-001 | Epic 1 | Enterprise Architect | P0 |
| US-002 | Epic 1 | Indie Dev | P0 |
| US-003 | Epic 2 | Professional | P0 |
| US-004 | Epic 2 | Enterprise Architect | P0 |
| US-005 | Epic 2 | Indie Dev | P1 |
| US-006 | Epic 2 | Enterprise Architect | P0 |
| US-007 | Epic 3 | Platform Contributor | P2 |
| US-008 | Epic 3 | Professional | P2 |
| US-009 | Epic 4 | Enterprise Architect | P0 |
| US-010 | Epic 4 | Professional | P1 |
| US-011 | Epic 4 | Indie Dev | P1 |
| US-012 | Epic 5 | CI/CD Engineer | P1 |
| US-013 | Epic 5 | Professional | P1 |
| US-014 | Epic 5 | CI/CD Engineer | P1 |
| US-015 | Epic 6 | Educator | P1 |
| US-016 | Epic 6 | Professional | P1 |
| US-017 | Epic 6 | Platform Contributor | P1 |
