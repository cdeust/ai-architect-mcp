# Epic 5: GitHub Actions Client - JIRA Tickets

**Document:** prd-jira.md
**Version:** 1.0
**Date:** 2026-03-14
**Project:** AI Architect
**Epic Key:** E5

---

## JIRA Ticket Index

| Ticket | Title | Type | SP | Status | Assignee | Sprint |
|--------|-------|------|-----|--------|----------|--------|
| E5-001 | GitOperationsPort Adapter Implementation | Story | 5 | New | TBD | S1 |
| E5-002 | FileSystemPort Adapter Implementation | Story | 3 | New | TBD | S2 |
| E5-003 | GitHubOperationsPort Adapter Implementation | Story | 5 | New | TBD | S2 |
| E5-004 | StageContextPort Adapter (Artifact-Backed Storage) | Story | 5 | New | TBD | S3 |
| E5-005 | XcodeOperationsPort Adapter (Headless Stub) | Story | 3 | New | TBD | S1 |
| E5-006 | Headless Entrypoint Script Implementation | Story | 5 | New | TBD | S3 |
| E5-007 | Issue-Triggered Workflow Implementation | Story | 5 | New | TBD | S4 |
| E5-008 | Nightly Workflow Implementation | Story | 3 | New | TBD | S4 |
| E5-009 | PR-Comment-Triggered Workflow Implementation | Story | 3 | New | TBD | S4 |
| E5-010 | Artifact Collection & Multi-Job Integration | Story | 3 | New | TBD | S4 |
| E5-011 | GitHub Check Run Status Reporting | Story | 5 | New | TBD | S5 |
| E5-012 | E2E Test: Issue to PR Flow | Story | 5 | New | TBD | S4 |

**Total:** 50 SP across 12 stories

---

## JIRA Ticket Details

### E5-001: GitOperationsPort Adapter Implementation

**Type:** Story
**Story Points:** 5
**Priority:** P0
**Status:** New
**Sprint:** Sprint 1
**Assignee:** TBD

**Summary:**
Implement GitOperationsPort for GitHub Actions context. Git operations (create_branch, commit, push, diff, log) must execute in GITHUB_WORKSPACE directory using git CLI.

**Description:**
As a pipeline engineer, I want to implement GitOperationsPort for GitHub Actions context so that git operations work in headless CI/CD workflows.

**Acceptance Criteria:**
- [ ] AC-E5-001: create_branch() creates git branch from base
- [ ] AC-E5-002: commit() stages files and creates commit
- [ ] AC-E5-003: push() sends changes to remote with GITHUB_TOKEN
- [ ] AC-E5-004: diff() returns unified diff, log() returns commit history
- [ ] AC-E5-005: GITHUB_WORKSPACE boundary enforced

**Definition of Done:**
- [ ] GitOpsAdapterImpl class implemented
- [ ] All 5 methods implemented (create_branch, commit, push, diff, log)
- [ ] Unit tests: test_gha_git_ops.py (≥4 test cases)
- [ ] Code coverage ≥95%
- [ ] mypy --strict passes
- [ ] Code review approved
- [ ] No lint errors

**Related Documents:**
- prd-requirements.md (FR-E5-001..005)
- prd-technical.md (Section 2.1)
- prd-user-stories.md (STORY-E5-001)

**Subtasks:**
1. [ ] Create GitOpsAdapterImpl class skeleton
2. [ ] Implement create_branch() method
3. [ ] Implement commit() method
4. [ ] Implement push() method
5. [ ] Implement diff() and log() methods
6. [ ] Add GITHUB_WORKSPACE validation
7. [ ] Write unit tests (4+ test cases)
8. [ ] Code review

---

### E5-002: FileSystemPort Adapter Implementation

**Type:** Story
**Story Points:** 3
**Priority:** P0
**Status:** New
**Sprint:** Sprint 2
**Assignee:** TBD

**Summary:**
Implement FileSystemPort for GitHub Actions. All file operations must be scoped to GITHUB_WORKSPACE and enforce path traversal boundaries.

**Description:**
As a pipeline engineer, I want to implement FileSystemPort for GitHub Actions so that file operations work in the headless workspace with security boundaries.

**Acceptance Criteria:**
- [ ] AC-E5-006: read() returns file contents
- [ ] AC-E5-007: write() creates/overwrites files with parent dirs
- [ ] AC-E5-008: list_directory() returns matching files via glob
- [ ] AC-E5-009: exists() checks path existence
- [ ] AC-E5-010: Path traversal prevented (../../../ rejected)

**Definition of Done:**
- [ ] FileSystemAdapterImpl class implemented
- [ ] All 4 methods implemented (read, write, list_directory, exists)
- [ ] Unit tests: test_gha_filesystem_ops.py (≥5 test cases)
- [ ] Path boundary enforcement tested
- [ ] Code coverage ≥95%
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-011..015)
- prd-technical.md (Section 2.2)
- prd-user-stories.md (STORY-E5-002)

**Subtasks:**
1. [ ] Create FileSystemAdapterImpl class skeleton
2. [ ] Implement _validate_path() boundary check
3. [ ] Implement read() method
4. [ ] Implement write() method with parent dir creation
5. [ ] Implement list_directory() method
6. [ ] Implement exists() method
7. [ ] Write unit tests (5+ test cases, including traversal attempts)
8. [ ] Code review

---

### E5-003: GitHubOperationsPort Adapter Implementation

**Type:** Story
**Story Points:** 5
**Priority:** P0
**Status:** New
**Sprint:** Sprint 2
**Assignee:** TBD

**Summary:**
Implement GitHubOperationsPort using GitHub REST API. All operations must use GITHUB_TOKEN and support rate limit handling with exponential backoff.

**Description:**
As a pipeline engineer, I want to implement GitHubOperationsPort for GitHub Actions so that PR creation, querying, and commenting work in CI/CD context.

**Acceptance Criteria:**
- [ ] AC-E5-011: create_pull_request() calls GitHub API
- [ ] AC-E5-012: get_pull_request() queries PR status
- [ ] AC-E5-013: add_comment() posts to PR
- [ ] AC-E5-014: Rate limiting handled (429 → exponential backoff)
- [ ] AC-E5-015: Environment variables validated (GITHUB_TOKEN, GITHUB_REPOSITORY)

**Definition of Done:**
- [ ] GitHubAdapterImpl class implemented
- [ ] All 3 methods implemented (create_pull_request, get_pull_request, add_comment)
- [ ] Rate limit retry logic (exponential backoff: 1s, 2s, 4s)
- [ ] Unit tests: test_gha_github_ops.py (≥5 test cases)
- [ ] Mock GitHub API responses
- [ ] Code coverage ≥95%
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-007..010)
- prd-technical.md (Section 2.3)
- prd-user-stories.md (STORY-E5-003)

**Subtasks:**
1. [ ] Create GitHubAdapterImpl class skeleton
2. [ ] Implement environment validation (GITHUB_TOKEN, GITHUB_REPOSITORY)
3. [ ] Implement _api_call() with aiohttp + retry logic
4. [ ] Implement create_pull_request() method
5. [ ] Implement get_pull_request() method
6. [ ] Implement add_comment() method
7. [ ] Write unit tests with mocked GitHub API (5+ test cases)
8. [ ] Test rate limit retry logic
9. [ ] Code review

---

### E5-004: StageContextPort Adapter (Artifact-Backed Storage)

**Type:** Story
**Story Points:** 5
**Priority:** P0
**Status:** New
**Sprint:** Sprint 3
**Assignee:** TBD

**Summary:**
Implement StageContextPort using local artifacts/ directory and GitHub Actions artifact actions. Support multi-job workflows via upload/download actions.

**Description:**
As a pipeline engineer, I want to implement StageContextPort using artifact-backed storage so that stage outputs persist across GitHub Actions job boundaries.

**Acceptance Criteria:**
- [ ] AC-E5-016: save_artifact() writes JSON to artifacts/{stage_id}/{finding_id}.json
- [ ] AC-E5-017: load_artifact() reads JSON artifact
- [ ] AC-E5-018: query_artifacts() filters by finding_id across stages
- [ ] AC-E5-019: Multi-job artifact sharing works (upload/download)

**Definition of Done:**
- [ ] ContextAdapterImpl class implemented
- [ ] All 3 methods implemented (save_artifact, load_artifact, query_artifacts)
- [ ] Unit tests: test_gha_context_ops.py (≥4 test cases)
- [ ] Multi-job workflow test (Job A uploads, Job B downloads)
- [ ] Data integrity verified
- [ ] Code coverage ≥95%
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-016..019)
- prd-technical.md (Section 2.4)
- prd-user-stories.md (STORY-E5-004)

**Subtasks:**
1. [ ] Create ContextAdapterImpl class skeleton
2. [ ] Implement save_artifact() method (JSON serialization)
3. [ ] Implement load_artifact() method (JSON deserialization)
4. [ ] Implement query_artifacts() method (filtering)
5. [ ] Design multi-job artifact structure
6. [ ] Write unit tests (4+ test cases)
7. [ ] Write multi-job simulation test
8. [ ] Code review

---

### E5-005: XcodeOperationsPort Adapter (Headless Stub)

**Type:** Story
**Story Points:** 3
**Priority:** P1
**Status:** New
**Sprint:** Sprint 1
**Assignee:** TBD

**Summary:**
Implement XcodeOperationsPort as headless stub. All methods raise NotSupportedInGitHubActionsError with helpful message.

**Description:**
As a pipeline engineer, I want to implement XcodeOperationsPort as a headless stub so that stage logic doesn't crash if Xcode methods are called.

**Acceptance Criteria:**
- [ ] AC-E5-020: build() raises NotSupportedInGitHubActionsError
- [ ] AC-E5-021: test() raises NotSupportedInGitHubActionsError
- [ ] AC-E5-022: preview() raises NotSupportedInGitHubActionsError
- [ ] Error message includes "macOS runner" suggestion

**Definition of Done:**
- [ ] XcodeAdapterImpl class implemented
- [ ] NotSupportedInGitHubActionsError exception defined
- [ ] All 3 methods raise error
- [ ] Unit tests: test_gha_xcode_ops.py (3 test cases)
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-006)
- prd-technical.md (Section 2.5)
- prd-user-stories.md (STORY-E5-005)

**Subtasks:**
1. [ ] Define NotSupportedInGitHubActionsError exception
2. [ ] Create XcodeAdapterImpl class skeleton
3. [ ] Implement build() method stub
4. [ ] Implement test() method stub
5. [ ] Implement preview() method stub
6. [ ] Write error message with macOS runner suggestion
7. [ ] Write unit tests (3 test cases)
8. [ ] Code review

---

### E5-006: Headless Entrypoint Script Implementation

**Type:** Story
**Story Points:** 5
**Priority:** P0
**Status:** New
**Sprint:** Sprint 3
**Assignee:** TBD

**Summary:**
Implement scripts/ci/entrypoint.py. Reads GitHub Actions event payloads, creates Finding objects, runs pipeline, reports status via check runs API.

**Description:**
As a GitHub Actions workflow author, I want to invoke the pipeline from a workflow so that the AI Architect pipeline executes in CI/CD.

**Acceptance Criteria:**
- [ ] AC-E5-023: Event parsing extracts context (issue #, PR #, comment text)
- [ ] AC-E5-024: Finding created with metadata
- [ ] AC-E5-025: Adapter instantiated correctly
- [ ] AC-E5-026: Pipeline invoked and outputs captured
- [ ] AC-E5-027: Artifacts collected and written
- [ ] AC-E5-028: Check run status reported

**Definition of Done:**
- [ ] scripts/ci/entrypoint.py created (200-250 lines)
- [ ] Event payload parsing working
- [ ] Finding creation working
- [ ] Adapter instantiation working
- [ ] Pipeline invocation working
- [ ] Artifact collection working
- [ ] Check run API integration working
- [ ] Unit tests: test_entrypoint.py (≥4 test cases)
- [ ] Code coverage ≥95%
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-020..024)
- prd-technical.md (Section 3)
- prd-user-stories.md (STORY-E5-006)

**Subtasks:**
1. [ ] Create scripts/ci/ directory structure
2. [ ] Create entrypoint.py skeleton
3. [ ] Implement GitHub Actions event parsing
4. [ ] Implement Finding object creation from event
5. [ ] Implement GitHubActionsAdapter instantiation
6. [ ] Implement pipeline invocation (TBD: stage logic)
7. [ ] Implement artifact collection
8. [ ] Implement check run creation + update
9. [ ] Write unit tests (4+ test cases)
10. [ ] Test error handling
11. [ ] Code review

---

### E5-007: Issue-Triggered Workflow Implementation

**Type:** Story
**Story Points:** 5
**Priority:** P0
**Status:** New
**Sprint:** Sprint 4
**Assignee:** TBD

**Summary:**
Implement .github/workflows/issue-triggered.yml. Auto-responds to issues with PR findings when issues are opened/reopened.

**Description:**
As a repository maintainer, I want to auto-respond to issues with PR findings so that every issue gets architectural analysis without manual triggers.

**Acceptance Criteria:**
- [ ] AC-E5-029: Workflow trigger configured (issues.types = [opened, reopened])
- [ ] AC-E5-030: Workflow job steps defined (checkout → setup Python → entrypoint → create PR)
- [ ] AC-E5-031: Issue → Finding mapping working
- [ ] AC-E5-032: PR creation in workflow working
- [ ] AC-E5-033: Secrets management (GITHUB_TOKEN, ANTHROPIC_API_KEY)

**Definition of Done:**
- [ ] .github/workflows/issue-triggered.yml created
- [ ] YAML syntax valid
- [ ] All steps defined (checkout, setup, entrypoint, PR creation)
- [ ] Secrets properly configured
- [ ] Tested manually (trigger issue, verify PR created)
- [ ] Artifacts uploaded
- [ ] Check runs reported on PR
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-025)
- prd-technical.md (Section 4.1)
- prd-user-stories.md (STORY-E5-007)

**Subtasks:**
1. [ ] Create .github/workflows/ directory if missing
2. [ ] Create issue-triggered.yml skeleton
3. [ ] Define trigger (issues opened/reopened)
4. [ ] Define job steps (checkout, Python setup, entrypoint)
5. [ ] Add artifact upload step
6. [ ] Add PR creation step
7. [ ] Configure secrets (GITHUB_TOKEN, ANTHROPIC_API_KEY)
8. [ ] Validate YAML syntax
9. [ ] Test with real issue (manual verification)
10. [ ] Code review

---

### E5-008: Nightly Workflow Implementation

**Type:** Story
**Story Points:** 3
**Priority:** P1
**Status:** New
**Sprint:** Sprint 4
**Assignee:** TBD

**Summary:**
Implement .github/workflows/nightly.yml. Runs full pipeline on schedule (0 2 * * * UTC) against recent PRs.

**Description:**
As an architecture team, I want to continuously analyze recent PRs so that we catch architectural issues before they merge.

**Acceptance Criteria:**
- [ ] AC-E5-032: Workflow trigger configured (schedule + manual trigger)
- [ ] AC-E5-035: Nightly job steps defined (discover PRs, analyze each, aggregate results)
- [ ] AC-E5-036: PR discovery working (recent 24h)

**Definition of Done:**
- [ ] .github/workflows/nightly.yml created
- [ ] YAML syntax valid
- [ ] Schedule trigger: 0 2 * * * UTC
- [ ] Manual trigger: workflow_dispatch
- [ ] PR discovery logic working
- [ ] Test with manual trigger
- [ ] Code review approved

**Related Documents:**
- prd-technical.md (Section 4.2)
- prd-user-stories.md (STORY-E5-008)

**Subtasks:**
1. [ ] Create nightly.yml skeleton
2. [ ] Define schedule trigger (0 2 * * *)
3. [ ] Define manual trigger (workflow_dispatch)
4. [ ] Implement PR discovery (gh pr list)
5. [ ] Implement analysis loop per PR
6. [ ] Implement results aggregation
7. [ ] Test with manual trigger
8. [ ] Code review

---

### E5-009: PR-Comment-Triggered Workflow Implementation

**Type:** Story
**Story Points:** 3
**Priority:** P2
**Status:** New
**Sprint:** Sprint 4
**Assignee:** TBD

**Summary:**
Implement .github/workflows/pr-comment.yml. Re-analyzes PR when comment mentions @architect.

**Description:**
As a developer, I want to re-analyze a PR by mentioning @architect so that I can re-run the pipeline on demand.

**Acceptance Criteria:**
- [ ] AC-E5-037: Comment trigger setup (activate on @architect mention)
- [ ] AC-E5-038: Workflow execution on mention
- [ ] AC-E5-039: Comment parsing

**Definition of Done:**
- [ ] .github/workflows/pr-comment.yml created
- [ ] YAML syntax valid
- [ ] Comment parsing: @architect mention detection
- [ ] PR context detection (only run on PRs, not issues)
- [ ] Test with manual comment on PR
- [ ] Code review approved

**Related Documents:**
- prd-technical.md (Section 4.3)
- prd-user-stories.md (STORY-E5-009)

**Subtasks:**
1. [ ] Create pr-comment.yml skeleton
2. [ ] Define issue_comment trigger
3. [ ] Implement @architect mention filter
4. [ ] Implement PR-only filter
5. [ ] Implement comment parsing
6. [ ] Test with manual comment on PR
7. [ ] Code review

---

### E5-010: Artifact Collection & Multi-Job Integration

**Type:** Story
**Story Points:** 3
**Priority:** P0
**Status:** New
**Sprint:** Sprint 4
**Assignee:** TBD

**Summary:**
Implement artifact upload/download logic in workflows. Support multi-job pipelines via GitHub Actions artifact actions.

**Description:**
As a pipeline engineer, I want to share stage outputs across GitHub Actions jobs so that complex workflows can parallelize architecture analysis.

**Acceptance Criteria:**
- [ ] AC-E5-040: Artifact upload in workflows
- [ ] AC-E5-041: Artifact download in downstream jobs
- [ ] AC-E5-042: Multi-job workflow test

**Definition of Done:**
- [ ] Artifact upload action configured in all workflows
- [ ] Artifact download action configured in downstream jobs
- [ ] Multi-job workflow test implemented + passing
- [ ] Data integrity verified (same in → same out)
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-019)
- prd-technical.md (Section 5)
- prd-user-stories.md (STORY-E5-010)

**Subtasks:**
1. [ ] Add actions/upload-artifact@v3 to all workflows
2. [ ] Configure artifact name and path
3. [ ] Add actions/download-artifact@v3 to downstream jobs
4. [ ] Test artifact persistence across job boundaries
5. [ ] Verify data integrity
6. [ ] Code review

---

### E5-011: GitHub Check Run Status Reporting

**Type:** Story
**Story Points:** 5
**Priority:** P0
**Status:** New
**Sprint:** Sprint 5
**Assignee:** TBD

**Summary:**
Implement GitHub check run API integration in entrypoint script. Create check run at start, update with final status.

**Description:**
As a developer, I want to see architectural findings as GitHub check runs so that I know immediately if analysis passed/failed.

**Acceptance Criteria:**
- [ ] AC-E5-043: Check run creation (status: in_progress)
- [ ] AC-E5-044: Check run completion (status: completed, conclusion: success/failure)
- [ ] AC-E5-045: Summary formatting (markdown)
- [ ] AC-E5-046: Error handling in check run

**Definition of Done:**
- [ ] Check run creation API working
- [ ] Check run update API working
- [ ] Summary formatting in markdown
- [ ] Error handling for failed pipelines
- [ ] Unit tests: test_entrypoint.py (extended)
- [ ] Integration test: check run appears on PR
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (FR-E5-024)
- prd-user-stories.md (STORY-E5-011)

**Subtasks:**
1. [ ] Implement check run creation (POST /repos/.../check-runs)
2. [ ] Implement check run update (PATCH /repos/.../check-runs/{id})
3. [ ] Implement summary formatting
4. [ ] Implement conclusion logic (success/failure)
5. [ ] Write unit tests
6. [ ] Test integration with real PR (manual)
7. [ ] Code review

---

### E5-012: E2E Test: Issue to PR Flow

**Type:** Story
**Story Points:** 5
**Priority:** P0
**Status:** New
**Sprint:** Sprint 4
**Assignee:** TBD

**Summary:**
Implement comprehensive E2E test for full issue→PR pipeline. Uses mocked GitHub API and filesystem.

**Description:**
As a QA engineer, I want to test the full issue→PR pipeline so that we verify end-to-end functionality before deployment.

**Acceptance Criteria:**
- [ ] AC-E5-047: E2E test setup (mock GitHub API + filesystem)
- [ ] AC-E5-048: Full flow execution (issue → Finding → adapter → PR creation)
- [ ] AC-E5-049: Artifact verification
- [ ] AC-E5-050: PR and check run verification

**Definition of Done:**
- [ ] tests/test_gha_pipeline_e2e.py created (200+ lines)
- [ ] Mock GitHub API responses
- [ ] Mock filesystem (GITHUB_WORKSPACE)
- [ ] Realistic GitHub Actions event payload
- [ ] Full flow tested (issue → PR)
- [ ] Artifact verification working
- [ ] Check run verification working
- [ ] Test coverage ≥90%
- [ ] Code review approved

**Related Documents:**
- prd-requirements.md (NFR-E5-003, NFR-E5-004)
- prd-technical.md (Section 9)
- prd-user-stories.md (STORY-E5-012)

**Subtasks:**
1. [ ] Create test_gha_pipeline_e2e.py skeleton
2. [ ] Implement GitHub Actions environment setup
3. [ ] Implement GitHub API mocks (issue, PR, check runs)
4. [ ] Implement filesystem mocks (GITHUB_WORKSPACE)
5. [ ] Create realistic GitHub Actions event payload
6. [ ] Implement full flow test (issue → Finding → adapter → PR)
7. [ ] Implement artifact verification
8. [ ] Implement check run verification
9. [ ] Write 200+ lines of test code
10. [ ] Code review

---

## JIRA CSV Export

```
Key,Epic,Type,Summary,Story Points,Priority,Status,Sprint,Assignee,Labels
E5-001,E5,Story,GitOperationsPort Adapter Implementation,5,P0,New,Sprint 1,TBD,adapter;git;epic5
E5-002,E5,Story,FileSystemPort Adapter Implementation,3,P0,New,Sprint 2,TBD,adapter;filesystem;epic5
E5-003,E5,Story,GitHubOperationsPort Adapter Implementation,5,P0,New,Sprint 2,TBD,adapter;github;epic5
E5-004,E5,Story,StageContextPort Adapter (Artifact-Backed Storage),5,P0,New,Sprint 3,TBD,adapter;artifact;epic5
E5-005,E5,Story,XcodeOperationsPort Adapter (Headless Stub),3,P1,New,Sprint 1,TBD,adapter;xcode;epic5
E5-006,E5,Story,Headless Entrypoint Script Implementation,5,P0,New,Sprint 3,TBD,entrypoint;script;epic5
E5-007,E5,Story,Issue-Triggered Workflow Implementation,5,P0,New,Sprint 4,TBD,workflow;github-actions;epic5
E5-008,E5,Story,Nightly Workflow Implementation,3,P1,New,Sprint 4,TBD,workflow;github-actions;epic5
E5-009,E5,Story,PR-Comment-Triggered Workflow Implementation,3,P2,New,Sprint 4,TBD,workflow;github-actions;epic5
E5-010,E5,Story,Artifact Collection & Multi-Job Integration,3,P0,New,Sprint 4,TBD,artifact;workflow;epic5
E5-011,E5,Story,GitHub Check Run Status Reporting,5,P0,New,Sprint 5,TBD,github;check-runs;epic5
E5-012,E5,Story,E2E Test: Issue to PR Flow,5,P0,New,Sprint 4,TBD,test;e2e;epic5
```

---

## Dependencies Map

```
E5-001 (GitOps)
├─ E5-002 (FileSystem) [No hard dependency]
├─ E5-003 (GitHub) [No hard dependency]
├─ E5-004 (Context) [No hard dependency]
├─ E5-005 (Xcode) [No hard dependency]
├─ E5-006 (Entrypoint) ← Depends on E5-001..005
├─ E5-007 (Issue workflow) ← Depends on E5-006
├─ E5-008 (Nightly workflow) ← Depends on E5-006
├─ E5-009 (PR-comment workflow) ← Depends on E5-006
├─ E5-010 (Artifact integration) ← Depends on E5-004
├─ E5-011 (Check runs) ← Depends on E5-006
└─ E5-012 (E2E test) ← Depends on E5-001..011 (integration test)
```

---

## Effort Summary

**Total: 50 SP across 12 stories**

| Phase | Stories | Total SP | Focus |
|-------|---------|----------|-------|
| **Adapter Implementation** | E5-001, E5-002, E5-003, E5-004, E5-005 | 21 SP | Ports ready for use |
| **Entrypoint & Scripts** | E5-006 | 5 SP | Pipeline invocation |
| **Workflow Templates** | E5-007, E5-008, E5-009, E5-010 | 14 SP | GitHub Actions automation |
| **Integration & Testing** | E5-011, E5-012 | 10 SP | Status reporting, E2E |

