# Epic 5: GitHub Actions Client - Development Roadmap

**Document:** prd-roadmap.md
**Version:** 1.0
**Date:** 2026-03-14
**Duration:** 5-8 weeks
**Total Effort:** 50 SP

---

## Sprint Overview

| Sprint | Duration | Focus | Capacity (SP) | Target Completion |
|--------|----------|-------|---------------|-------------------|
| **Sprint 1** | Week 1 | Adapter core + GitOps | 8 SP | 2026-03-21 |
| **Sprint 2** | Week 2 | FileSystem + GitHub ports | 8 SP | 2026-03-28 |
| **Sprint 3** | Week 3-3.5 | Context + Xcode + entrypoint | 9 SP | 2026-04-04 |
| **Sprint 4** | Week 4-5 | Workflows + E2E tests | 13 SP | 2026-04-18 |
| **Sprint 5** | Week 6-8 | Tuning, hooks, docs | 12 SP | 2026-05-02 |

---

## Sprint 1: Adapter Core & GitOperationsPort (8 SP)

**Duration:** Week 1 (2026-03-14 to 2026-03-21)
**Goal:** Foundation: base adapter class + git operations working

### Stories in Sprint 1

1. **STORY-E5-001: GitOperationsPort Adapter** (5 SP)
   - [ ] Implement GitOpsAdapterImpl class
   - [ ] Implement create_branch(), commit(), push(), diff(), log()
   - [ ] Add GITHUB_WORKSPACE validation
   - [ ] Unit tests: test_gha_git_ops.py (4 test cases)
   - [ ] Code review + merge

2. **STORY-E5-005: XcodeOperationsPort Adapter** (3 SP)
   - [ ] Implement XcodeAdapterImpl (stub)
   - [ ] Define NotSupportedInGitHubActionsError
   - [ ] All 3 methods raise error with helpful message
   - [ ] Unit tests: 3 test cases
   - [ ] Code review + merge

### Deliverables

- [ ] `ai_architect_mcp/_adapters/github_actions_impl.py` (partial: GitOpsAdapterImpl + XcodeAdapterImpl)
- [ ] `tests/test_gha_git_ops.py` (≥4 tests, ≥90% coverage)
- [ ] `tests/test_gha_xcode_ops.py` (3 tests)
- [ ] Git operations verified in mock environment

### Definition of Done

- [ ] All tests passing
- [ ] Code coverage ≥95%
- [ ] mypy --strict passes
- [ ] No lint errors
- [ ] Code review approved

---

## Sprint 2: FileSystem & GitHub Ports (8 SP)

**Duration:** Week 2 (2026-03-21 to 2026-03-28)
**Goal:** File operations + GitHub API functional

### Stories in Sprint 2

1. **STORY-E5-002: FileSystemPort Adapter** (3 SP)
   - [ ] Implement FileSystemAdapterImpl class
   - [ ] Implement read(), write(), list_directory(), exists()
   - [ ] Path boundary enforcement (no traversal)
   - [ ] Unit tests: test_gha_filesystem_ops.py (5 test cases)
   - [ ] Test traversal attempts blocked

2. **STORY-E5-003: GitHubOperationsPort Adapter** (5 SP)
   - [ ] Implement GitHubAdapterImpl class
   - [ ] Implement create_pull_request(), get_pull_request(), add_comment()
   - [ ] Rate limit handling (429 → exponential backoff)
   - [ ] Environment validation (GITHUB_TOKEN, GITHUB_REPOSITORY)
   - [ ] Unit tests: test_gha_github_ops.py (5 test cases)
   - [ ] Mock GitHub API responses

### Deliverables

- [ ] `ai_architect_mcp/_adapters/github_actions_impl.py` (extended: FileSystemAdapterImpl + GitHubAdapterImpl)
- [ ] `tests/test_gha_filesystem_ops.py` (≥5 tests)
- [ ] `tests/test_gha_github_ops.py` (≥5 tests)
- [ ] Rate limit retry logic verified
- [ ] Path traversal security verified

### Definition of Done

- [ ] All tests passing
- [ ] Code coverage ≥95%
- [ ] Rate limit backoff tested (3 retries max)
- [ ] Path boundary enforcement confirmed
- [ ] Code review approved

---

## Sprint 3: Context Port, Entrypoint, & Integration (9 SP)

**Duration:** Week 3-3.5 (2026-03-28 to 2026-04-04)
**Goal:** Artifact storage + entrypoint script ready

### Stories in Sprint 3

1. **STORY-E5-004: StageContextPort Adapter** (5 SP)
   - [ ] Implement ContextAdapterImpl class
   - [ ] Implement save_artifact(), load_artifact(), query_artifacts()
   - [ ] Artifact structure: artifacts/{stage_id}/{finding_id}.json
   - [ ] Multi-job workflow support (upload/download actions)
   - [ ] Unit tests: test_gha_context_ops.py (4 test cases)
   - [ ] Multi-job simulation test

2. **STORY-E5-006: Headless Entrypoint Script** (4 SP)
   - [ ] Create scripts/ci/entrypoint.py
   - [ ] Event parsing (GITHUB_EVENT_PATH)
   - [ ] Finding creation from issue/PR/comment
   - [ ] Adapter instantiation + validation
   - [ ] Pipeline invocation (TBD: stage logic)
   - [ ] Artifact collection + check run reporting
   - [ ] Unit tests: test_entrypoint.py (4 test cases)

### Deliverables

- [ ] `ai_architect_mcp/_adapters/github_actions_impl.py` (complete: all 5 adapters)
- [ ] `scripts/ci/entrypoint.py` (200-250 lines)
- [ ] `tests/test_gha_context_ops.py` (≥4 tests)
- [ ] `tests/test_entrypoint.py` (≥4 tests)
- [ ] Artifact directory structure documented

### Definition of Done

- [ ] Entrypoint executable: `python scripts/ci/entrypoint.py`
- [ ] Event parsing verified
- [ ] Finding creation tested
- [ ] Adapter instantiation verified
- [ ] All tests passing
- [ ] Code coverage ≥95%
- [ ] Code review approved

---

## Sprint 4: Workflow Templates & E2E Testing (13 SP)

**Duration:** Week 4-5 (2026-04-04 to 2026-04-18)
**Goal:** Workflows executable, E2E tests comprehensive

### Stories in Sprint 4

1. **STORY-E5-007: Issue-Triggered Workflow** (5 SP)
   - [ ] Create `.github/workflows/issue-triggered.yml`
   - [ ] Trigger: issues.types = [opened, reopened]
   - [ ] Steps: checkout → setup Python → run entrypoint → create PR
   - [ ] PR title: "Architecture Analysis for Issue #{number}"
   - [ ] Artifact upload via actions/upload-artifact
   - [ ] Secrets: GITHUB_TOKEN, ANTHROPIC_API_KEY
   - [ ] Test with real issue (manual verification)

2. **STORY-E5-008: Nightly Workflow** (3 SP)
   - [ ] Create `.github/workflows/nightly.yml`
   - [ ] Trigger: schedule at 0 2 * * * (2 AM UTC)
   - [ ] Manual trigger: workflow_dispatch
   - [ ] Discover recent PRs (last 24h)
   - [ ] Run analysis per PR
   - [ ] Aggregate results

3. **STORY-E5-009: PR-Comment Workflow** (2 SP)
   - [ ] Create `.github/workflows/pr-comment.yml`
   - [ ] Trigger: issue_comment with @architect mention
   - [ ] Runs on PR branch checkout
   - [ ] Posts results as reply comment
   - [ ] Uploads artifacts

4. **STORY-E5-010: Artifact Collection & Multi-Job** (2 SP)
   - [ ] Artifact upload/download action integration
   - [ ] Multi-job workflow test
   - [ ] Data integrity verification

5. **STORY-E5-012: E2E Test - Issue to PR** (5 SP)
   - [ ] Create `tests/test_gha_pipeline_e2e.py`
   - [ ] Full flow: issue → Finding → adapter → PR creation
   - [ ] Mock GitHub API + filesystem
   - [ ] Realistic event payload simulation
   - [ ] Artifact verification
   - [ ] Check run verification
   - [ ] 200+ lines of test code

### Deliverables

- [ ] `.github/workflows/issue-triggered.yml`
- [ ] `.github/workflows/nightly.yml`
- [ ] `.github/workflows/pr-comment.yml`
- [ ] `tests/test_gha_pipeline_e2e.py` (200+ lines)
- [ ] Workflow execution verified (manual testing)
- [ ] E2E test coverage ≥90%

### Definition of Done

- [ ] All 3 workflows created and syntactically valid
- [ ] E2E tests comprehensive (mock GitHub API, filesystem)
- [ ] All tests passing
- [ ] Manual workflow execution verified (test issue → PR)
- [ ] Artifacts generated + uploaded
- [ ] Check runs reported on PR
- [ ] Code review approved

---

## Sprint 5: Tuning, Hook Integration, & Docs (12 SP)

**Duration:** Week 6-8 (2026-04-18 to 2026-05-02)
**Goal:** Production-ready, fully integrated, documented

### Tasks in Sprint 5

1. **Performance Tuning** (3 SP)
   - [ ] Measure actual pipeline time (target: <30 min)
   - [ ] Identify bottlenecks (git ops, API calls, artifact upload)
   - [ ] Optimize artifact compression
   - [ ] Cache GitHub API responses within run
   - [ ] Document timings in prd-technical.md

2. **Epic 4 Hook Integration** (3 SP)
   - [ ] Verify security-tier-check hook works with bash commands (git, etc.)
   - [ ] Verify enforce-doc-read hook skipped in headless mode
   - [ ] Verify update-pipeline-state hook logs all port operations
   - [ ] Verify validate-output-schema hook enforced
   - [ ] Test suite: test_gha_hook_integration.py

3. **Error Handling & Logging** (2 SP)
   - [ ] Comprehensive error testing (STORY-E5-012 extended)
   - [ ] Test all exception types
   - [ ] Verify secrets never logged
   - [ ] Verify clear error messages for troubleshooting

4. **STORY-E5-011: Check Run Status Reporting** (5 SP)
   - [ ] GitHub check run creation
   - [ ] Status update: in_progress → completed
   - [ ] Conclusion: success/failure
   - [ ] Summary formatting (markdown)
   - [ ] Unit tests: test_entrypoint.py (extended)
   - [ ] Integration test: verify check run on PR

5. **Documentation** (1 SP)
   - [ ] README for GitHub Actions workflows
   - [ ] Troubleshooting guide
   - [ ] Secret configuration guide
   - [ ] Example issue for testing

### Deliverables

- [ ] Performance metrics documented
- [ ] Hook integration verified
- [ ] `tests/test_gha_hook_integration.py` (if applicable)
- [ ] Check run API fully tested + working
- [ ] Documentation complete
- [ ] All 50 SP stories merged

### Definition of Done

- [ ] All tests passing (100% success rate)
- [ ] Code coverage ≥95% (entire codebase)
- [ ] mypy --strict: 0 errors
- [ ] pylint/flake8 score ≥9.5/10
- [ ] Performance verified <30 min
- [ ] Hook integration confirmed
- [ ] Check runs reporting on PRs
- [ ] No secrets leaked in logs
- [ ] Documentation complete
- [ ] Release notes prepared

---

## Blockers & Risks

### Critical Dependencies

- **Epic 4 (Hook System)** must be merged before E5 full integration
  - Mitigation: E5 can proceed independently; hook integration in Sprint 5
- **GitHub Actions environment** must support Python 3.11
  - Mitigation: Verify on ubuntu-latest (guaranteed)
- **Entrypoint stage logic** (TBD in other epics)
  - Mitigation: Use placeholder stage runner for E2E tests

### Known Risks

1. **Rate limiting on GitHub API**
   - Risk: Nightly workflow hits rate limits (5000/hour quota)
   - Mitigation: Cache API responses, batch queries

2. **Artifact size growth**
   - Risk: Artifacts grow large over time (90-day retention)
   - Mitigation: Clean up old artifacts manually, document cleanup process

3. **macOS runner availability**
   - Risk: Xcode support deferred (not supported in ubuntu-latest)
   - Mitigation: Graceful error message, documented future work

4. **Secret leakage**
   - Risk: API key logged accidentally
   - Mitigation: Code review focused on env var access, test for logging

---

## Acceptance Gates

### Sprint 1 Gate
- [ ] GitOps + Xcode adapters working
- [ ] ≥4 unit tests passing
- [ ] Code review approved

### Sprint 2 Gate
- [ ] FileSystem + GitHub adapters working
- [ ] Rate limit retry logic verified
- [ ] Path traversal blocked
- [ ] ≥8 unit tests passing

### Sprint 3 Gate
- [ ] Context adapter + entrypoint script complete
- [ ] Event parsing working
- [ ] Artifact collection working
- [ ] ≥8 unit tests passing

### Sprint 4 Gate
- [ ] All 3 workflows created + syntactically valid
- [ ] E2E tests comprehensive (200+ lines)
- [ ] Manual issue → PR flow verified
- [ ] Artifacts generated + check runs reported

### Sprint 5 Gate (Release)
- [ ] All 50 SP completed + merged
- [ ] Code coverage ≥95%
- [ ] All tests passing
- [ ] Performance <30 min verified
- [ ] Documentation complete
- [ ] Hook integration confirmed
- [ ] Ready for enterprise adoption

---

## Team Capacity

Assumes 2-person team (1 lead, 1 junior):
- Lead: 40 SP total (code review, technical decisions, complex implementations)
- Junior: 10 SP total (simpler adapters, test implementation)

Adjusted for mentoring: 50 SP / 8 weeks = 6.25 SP/week average

---

## Success Metrics

**By Release (End of Sprint 5):**

1. **Functional:** All 5 ports implemented, 3 workflows executable, E2E flow working
2. **Quality:** ≥95% coverage, mypy strict, 0 lint errors
3. **Performance:** Full pipeline <30 min, artifact ops <5 min
4. **Security:** No secrets leaked, path traversal blocked, hook integration verified
5. **Documentation:** Complete README, troubleshooting guide, secret setup guide

