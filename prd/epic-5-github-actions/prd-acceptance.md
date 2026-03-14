# Epic 5: GitHub Actions Client - Acceptance Criteria

**Document:** prd-acceptance.md
**Version:** 1.0
**Date:** 2026-03-14
**Total ACs:** 40+

---

## GitOperationsPort Adapter (5 ACs)

**AC-E5-001: create_branch() creates git branch**
- [ ] Method signature matches port interface
- [ ] Executes `git checkout -b {name} origin/{base}` in GITHUB_WORKSPACE
- [ ] Returns `refs/heads/{branch_name}`
- [ ] Raises GitError if base branch doesn't exist
- [ ] Test: test_gha_git_ops.py::test_create_branch_success

**AC-E5-002: commit() stages and commits files**
- [ ] Files validated before staging
- [ ] `git add files` executed
- [ ] `git commit -m message` executed
- [ ] Returns 40-character commit SHA
- [ ] Raises GitError if nothing to commit
- [ ] Test: test_gha_git_ops.py::test_commit_success

**AC-E5-003: push() sends changes to remote**
- [ ] Executes `git push origin {branch}`
- [ ] Uses GITHUB_TOKEN for auth
- [ ] Supports force flag
- [ ] Raises AuthenticationError if token missing
- [ ] Test: test_gha_git_ops.py::test_push_with_token

**AC-E5-004: diff() and log() read git history**
- [ ] diff() returns unified diff string
- [ ] log() returns list of dicts with sha, message, author, date
- [ ] Both parse git output correctly
- [ ] Test: test_gha_git_ops.py::test_diff_and_log

**AC-E5-005: GITHUB_WORKSPACE boundary enforced**
- [ ] All git operations in GITHUB_WORKSPACE
- [ ] FileNotFoundError if workspace missing
- [ ] Test: test_gha_git_ops.py::test_workspace_validation

---

## FileSystemPort Adapter (5 ACs)

**AC-E5-006: read() returns file contents**
- [ ] Path validated against workspace boundary
- [ ] File contents returned as string
- [ ] FileNotFoundError if not found
- [ ] Respects UTF-8 encoding
- [ ] Test: test_gha_filesystem_ops.py::test_read_file

**AC-E5-007: write() creates/overwrites files**
- [ ] Parent directories created
- [ ] Content written as string
- [ ] Existing files overwritten
- [ ] Path boundary enforced
- [ ] Test: test_gha_filesystem_ops.py::test_write_file

**AC-E5-008: list_directory() returns matching files**
- [ ] Glob pattern supported
- [ ] Returns list[Path] objects
- [ ] Filtered correctly
- [ ] Test: test_gha_filesystem_ops.py::test_list_directory

**AC-E5-009: exists() checks path existence**
- [ ] Returns bool (true/false)
- [ ] Works for files and directories
- [ ] Path boundary enforced
- [ ] Test: test_gha_filesystem_ops.py::test_exists

**AC-E5-010: Path traversal prevented**
- [ ] `../../../` attempts rejected
- [ ] Absolute paths outside workspace rejected
- [ ] ValueError raised with clear message
- [ ] Test: test_gha_filesystem_ops.py::test_path_traversal_blocked

---

## GitHubOperationsPort Adapter (5 ACs)

**AC-E5-011: create_pull_request() calls GitHub API**
- [ ] POST /repos/{owner}/{repo}/pulls called
- [ ] Returns dict with number, url, state
- [ ] Title and body parameters passed
- [ ] Head and base refs specified
- [ ] Test: test_gha_github_ops.py::test_create_pr

**AC-E5-012: get_pull_request() queries PR status**
- [ ] GET /repos/{owner}/{repo}/pulls/{number} called
- [ ] Returns PR metadata (state, checks, reviews)
- [ ] Raises NotFoundError if PR doesn't exist
- [ ] Test: test_gha_github_ops.py::test_get_pr

**AC-E5-013: add_comment() posts to PR**
- [ ] POST /repos/{owner}/{repo}/issues/{number}/comments called
- [ ] Body parameter preserved (markdown)
- [ ] Returns dict with id and url
- [ ] Test: test_gha_github_ops.py::test_add_comment

**AC-E5-014: Rate limiting handled**
- [ ] 429 response detected
- [ ] Exponential backoff implemented (1s, 2s, 4s)
- [ ] Retries up to 3 times
- [ ] RateLimitError raised after exhausted retries
- [ ] Test: test_gha_github_ops.py::test_rate_limit_retry

**AC-E5-015: Environment variables validated**
- [ ] GITHUB_TOKEN required and present
- [ ] GITHUB_REPOSITORY required and present
- [ ] Both used for authentication and base URL
- [ ] EnvironmentError raised if missing
- [ ] Test: test_gha_github_ops.py::test_env_validation

---

## StageContextPort Adapter (4 ACs)

**AC-E5-016: save_artifact() writes JSON**
- [ ] Artifact written to artifacts/{stage_id}/{finding_id}.json
- [ ] artifacts/ directory created if missing
- [ ] JSON formatted with indent=2, sort_keys=True
- [ ] Overwrites existing artifacts
- [ ] Test: test_gha_context_ops.py::test_save_artifact

**AC-E5-017: load_artifact() reads JSON**
- [ ] Artifact read from correct path
- [ ] Deserialized to dict
- [ ] FileNotFoundError if not found
- [ ] JSONDecodeError if corrupt
- [ ] Test: test_gha_context_ops.py::test_load_artifact

**AC-E5-018: query_artifacts() filters by finding_id**
- [ ] Searches all stages (0-10)
- [ ] Returns matching artifacts
- [ ] Supports exact key match and regex filtering
- [ ] Returns list with stage_id metadata
- [ ] Test: test_gha_context_ops.py::test_query_artifacts

**AC-E5-019: Multi-job artifact sharing works**
- [ ] Job A saves artifact
- [ ] actions/upload-artifact called
- [ ] Job B downloads artifact
- [ ] actions/download-artifact called
- [ ] Data integrity verified (same in → same out)
- [ ] Test: test_gha_context_ops.py::test_multi_job_flow

---

## XcodeOperationsPort Adapter (3 ACs)

**AC-E5-020: build() raises NotSupportedError**
- [ ] Raises NotSupportedInGitHubActionsError
- [ ] Error message mentions macOS runner
- [ ] Test: test_gha_xcode_ops.py::test_build_unsupported

**AC-E5-021: test() raises NotSupportedError**
- [ ] Raises NotSupportedInGitHubActionsError
- [ ] Test: test_gha_xcode_ops.py::test_test_unsupported

**AC-E5-022: preview() raises NotSupportedError**
- [ ] Raises NotSupportedInGitHubActionsError
- [ ] Test: test_gha_xcode_ops.py::test_preview_unsupported

---

## Entrypoint Script (6 ACs)

**AC-E5-023: Event parsing extracts context**
- [ ] GITHUB_EVENT_PATH read
- [ ] JSON payload parsed
- [ ] Issue #, PR #, comment text extracted
- [ ] Actor and timestamp captured
- [ ] EnvironmentError if GITHUB_EVENT_PATH missing
- [ ] Test: test_entrypoint.py::test_event_parsing

**AC-E5-024: Finding created with metadata**
- [ ] Finding instantiated with event data
- [ ] finding_id generated (format: finding-YYYYMMDD-NNN)
- [ ] All fields populated
- [ ] Logged to stdout
- [ ] Test: test_entrypoint.py::test_finding_creation

**AC-E5-025: Adapter instantiated correctly**
- [ ] All 5 ports instantiated
- [ ] Injected into GitHubActionsAdapter
- [ ] Environment validated (GITHUB_WORKSPACE, GITHUB_TOKEN, etc.)
- [ ] EnvironmentError raised if validation fails
- [ ] Test: test_entrypoint.py::test_adapter_init

**AC-E5-026: Pipeline invoked and outputs captured**
- [ ] Pipeline runner called with Finding
- [ ] Stage outputs collected
- [ ] Exceptions handled gracefully
- [ ] Logged to stdout/stderr
- [ ] Test: test_entrypoint.py::test_pipeline_invocation

**AC-E5-027: Artifacts collected and written**
- [ ] Stage outputs written to artifacts/{stage_id}/{finding_id}.json
- [ ] All stages processed
- [ ] Files created with correct permissions
- [ ] Test: test_entrypoint.py::test_artifact_collection

**AC-E5-028: Check run status reported**
- [ ] Check run created at start (status: in_progress)
- [ ] Check run updated at end (status: completed)
- [ ] Conclusion set: success or failure
- [ ] Summary includes finding count and stage names
- [ ] GitHub API calls made with correct parameters
- [ ] Test: test_entrypoint.py::test_check_run_reporting

---

## Workflow Templates (7 ACs)

**AC-E5-029: Issue-triggered workflow activates**
- [ ] Trigger: issues.types = [opened, reopened]
- [ ] Workflow runs on issue creation
- [ ] Uses ubuntu-latest runner
- [ ] Checks out code, sets up Python
- [ ] File: .github/workflows/issue-triggered.yml

**AC-E5-030: Issue → Finding mapping**
- [ ] Issue # extracted from event
- [ ] Title and body captured
- [ ] Finding created with issue_number field
- [ ] Test simulation: test_gha_pipeline_e2e.py::test_issue_triggered

**AC-E5-031: Issue workflow creates PR**
- [ ] PR title includes issue #
- [ ] PR body includes findings
- [ ] Branch name: feature/issue-{number}-architecture
- [ ] PR opened against main
- [ ] Test: test_gha_pipeline_e2e.py::test_issue_to_pr

**AC-E5-032: Nightly workflow runs on schedule**
- [ ] Trigger: schedule at 0 2 * * * (2 AM UTC)
- [ ] Manually triggerable via workflow_dispatch
- [ ] Discovers recent PRs (last 24h)
- [ ] Analyzes each PR
- [ ] Aggregates findings
- [ ] File: .github/workflows/nightly.yml

**AC-E5-033: PR-comment workflow activates on @architect mention**
- [ ] Trigger: issue_comment.types = [created, edited]
- [ ] Checks for @architect in body
- [ ] Only runs on PRs (not issues)
- [ ] Checks out PR branch
- [ ] File: .github/workflows/pr-comment.yml

**AC-E5-034: Secrets passed securely**
- [ ] GITHUB_TOKEN available (built-in)
- [ ] ANTHROPIC_API_KEY from secrets
- [ ] Both in env vars only (not logged)
- [ ] Never echoed to stdout/stderr
- [ ] Test: test_gha_pipeline_e2e.py::test_secret_not_logged

**AC-E5-035: Artifacts uploaded and retained**
- [ ] actions/upload-artifact@v3 called
- [ ] artifacts/ directory uploaded
- [ ] Retention set to 90 days
- [ ] Available to downstream jobs
- [ ] Test: test_gha_pipeline_e2e.py::test_artifact_retention

---

## Integration & Hook System (4 ACs)

**AC-E5-036: Hook system integration**
- [ ] All port methods loggable for AuditEvent
- [ ] No security-tier violations (Tier 1-5 allowed for bash)
- [ ] enforce-doc-read hook skipped in headless mode
- [ ] validate-output-schema hook called after stages
- [ ] Depends on: Epic 4 merged

**AC-E5-037: Idempotency guaranteed**
- [ ] Re-running same issue → same results
- [ ] Artifact content deterministic
- [ ] No random filenames or timestamps
- [ ] Test: test_gha_pipeline_e2e.py::test_idempotency

**AC-E5-038: Error handling comprehensive**
- [ ] Xcode not available → NotSupportedError (not crash)
- [ ] GITHUB_TOKEN missing → EnvironmentError
- [ ] API call fails → GitHubAPIError (with retry)
- [ ] All errors logged to stderr
- [ ] Workflow fails gracefully (exit code 1)
- [ ] Test: test_gha_pipeline_e2e.py::test_error_handling

**AC-E5-039: Performance within bounds**
- [ ] Individual port operations <5 seconds
- [ ] Artifact upload/download <5 minutes
- [ ] Full pipeline <30 minutes
- [ ] All tests complete in <60 seconds
- [ ] Test: test_gha_pipeline_e2e.py::test_performance

---

## Code Quality & Testing (2 ACs)

**AC-E5-040: Code coverage ≥95%**
- [ ] Adapter code: ≥95% coverage
- [ ] Entrypoint script: ≥95% coverage
- [ ] Workflow YAML: Manual verification
- [ ] Verified with pytest-cov

**AC-E5-041: Type checking strict mode**
- [ ] mypy --strict passes (0 errors)
- [ ] All functions annotated
- [ ] All return types specified
- [ ] Verified with mypy tool

---

## Manual Verification Checklist

**Before Release:**

- [ ] Run all test suites: `pytest tests/ -v`
- [ ] Check coverage: `pytest --cov=ai_architect_mcp tests/`
- [ ] Type check: `mypy --strict ai_architect_mcp/`
- [ ] Lint: `pylint ai_architect_mcp/` (score ≥9.5)
- [ ] Test with real GitHub Actions:
  - [ ] Trigger issue-triggered.yml manually
  - [ ] Verify PR created
  - [ ] Check artifacts uploaded
  - [ ] Verify check run status updated
- [ ] Test with real GitHub API (mock secrets):
  - [ ] Create test issue
  - [ ] Verify workflow runs
  - [ ] Verify check run appears on PR
- [ ] Performance test:
  - [ ] Run full pipeline, measure time
  - [ ] Verify <30 minutes
- [ ] Security review:
  - [ ] No secrets logged
  - [ ] Path traversal blocked
  - [ ] Rate limit handling works
  - [ ] Hook enforcement respected

