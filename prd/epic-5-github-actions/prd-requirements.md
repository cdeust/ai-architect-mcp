# Epic 5: GitHub Actions Client - Requirements

**Document:** prd-requirements.md
**Version:** 1.0
**Date:** 2026-03-14
**Total Requirements:** 25 FR + 8 NFR

---

## Functional Requirements

### GitOperationsPort Adapter

**FR-E5-001: Git branch creation in GITHUB_WORKSPACE**
- Implement `create_branch(branch_name, base="main")`
- Execute `git checkout -b branch_name origin/base` in GITHUB_WORKSPACE
- Return full branch reference (e.g., `refs/heads/feature/finding-123`)
- Error handling: FileNotFoundError if GITHUB_WORKSPACE not found

**FR-E5-002: Git commit with file staging**
- Implement `commit(message, files)`
- Stage specified files: `git add files`
- Create commit: `git commit -m message`
- Return commit SHA
- Validate files exist before staging

**FR-E5-003: Git push to remote**
- Implement `push(branch, force=False)`
- Execute `git push origin branch` (or `--force` if force=True)
- Require GITHUB_TOKEN environment variable
- Error if branch doesn't exist

**FR-E5-004: Git diff generation**
- Implement `diff(base, head)`
- Return unified diff output from `git diff base head`
- Support both branch names and SHAs as refs

**FR-E5-005: Git log retrieval**
- Implement `log(branch, count=10)`
- Return list of dicts with keys: `sha`, `message`, `author`, `date`
- Parse `git log --format=...` output
- Limit to last `count` entries

### XcodeOperationsPort Adapter

**FR-E5-006: Xcode unavailable in GitHub Actions**
- Implement `build()`, `test()`, `preview()`
- All three methods raise `NotSupportedInGitHubActionsError`
- Error message: "Xcode operations not supported in headless GitHub Actions environment"
- Future expansion: Detect macOS runner and implement

### GitHubOperationsPort Adapter

**FR-E5-007: PR creation via GitHub API**
- Implement `create_pull_request(title, body, head, base="main")`
- Call `POST /repos/{owner}/{repo}/pulls`
- Use GITHUB_TOKEN for authentication
- Return dict with `number`, `url`, `state`

**FR-E5-008: PR details retrieval**
- Implement `get_pull_request(pr_number)`
- Call `GET /repos/{owner}/{repo}/pulls/{number}`
- Return dict with status, checks, review state

**FR-E5-009: PR comment addition**
- Implement `add_comment(pr_number, body)`
- Call `POST /repos/{owner}/{repo}/issues/{number}/comments`
- Return dict with `id`, `url`

**FR-E5-010: GitHub API rate limiting**
- Handle rate limit responses (429)
- Implement exponential backoff (retry 3 times)
- Log rate limit warnings

### FileSystemPort Adapter

**FR-E5-011: File read operation**
- Implement `read(path)`
- Return file contents as string
- Raise FileNotFoundError if path doesn't exist
- Enforce GITHUB_WORKSPACE boundary (relative path resolution)

**FR-E5-012: File write operation**
- Implement `write(path, content)`
- Create parent directories if missing
- Overwrite existing files
- Enforce GITHUB_WORKSPACE boundary

**FR-E5-013: Directory listing**
- Implement `list_directory(path, pattern="*")`
- Return list of matching Path objects
- Use glob pattern for filtering
- Enforce GITHUB_WORKSPACE boundary

**FR-E5-014: File existence check**
- Implement `exists(path)`
- Return bool
- Support both files and directories

**FR-E5-015: GITHUB_WORKSPACE boundary enforcement**
- All file operations (read, write, list, exists) must resolve paths relative to GITHUB_WORKSPACE
- Reject absolute paths outside GITHUB_WORKSPACE
- Reject `../../../` path traversal attempts
- Use `Path.resolve()` to canonicalize before comparison

### StageContextPort Adapter

**FR-E5-016: Artifact save operation**
- Implement `save_artifact(stage_id, finding_id, artifact)`
- Write artifact as JSON to `artifacts/{stage_id}/{finding_id}.json`
- Create artifacts/ directory if missing
- Return None (side effect: file written)

**FR-E5-017: Artifact load operation**
- Implement `load_artifact(stage_id, finding_id)`
- Read artifact from `artifacts/{stage_id}/{finding_id}.json`
- Return dict
- Raise FileNotFoundError if artifact not found

**FR-E5-018: Artifact query operation**
- Implement `query_artifacts(finding_id, query)`
- List all artifacts in `artifacts/*/` for given finding_id
- Filter by semantic query (exact match on keys, regex on values)
- Return list of matching artifact dicts

**FR-E5-019: GitHub Actions artifact integration**
- Use `actions/upload-artifact` action in workflows
- Use `actions/download-artifact` action in workflows
- Support multi-job artifact sharing (job A uploads, job B downloads)
- Artifact retention: 90 days (GitHub default)

### Entrypoint Script

**FR-E5-020: GitHub Actions event parsing**
- Script location: `scripts/ci/entrypoint.py`
- Read `GITHUB_EVENT_PATH` environment variable
- Parse JSON event payload
- Extract context: issue #, PR #, comment text, actor, timestamp

**FR-E5-021: Finding object creation**
- Create Finding object with metadata from GitHub Actions event
- Populate fields: `issue_number`, `pr_number`, `comment_text`, `actor`, `timestamp`
- Generate unique finding_id if not provided

**FR-E5-022: Pipeline invocation**
- Instantiate GitHubActionsAdapter with all 5 ports
- Call pipeline runner (TBD: stage logic)
- Pass Finding object
- Capture stage outputs

**FR-E5-023: Artifact collection**
- Collect all stage outputs from pipeline execution
- Write to `artifacts/{stage_id}/{finding_id}.json`
- Upload via `actions/upload-artifact`

**FR-E5-024: GitHub check run status reporting**
- Create GitHub check run on PR/commit
- Update status: `in_progress` → `completed` (success/failure)
- Include summary: findings count, stage names, errors
- Use GitHub API `POST /repos/{owner}/{repo}/check-runs`

### Workflow Templates

**FR-E5-025: Issue-triggered workflow**
- File: `.github/workflows/issue-triggered.yml`
- Trigger: `issues: { types: [opened, reopened] }`
- Steps: Checkout → Run entrypoint → Create PR
- Parse issue title/body → Create Finding
- Call architect stage only

---

## Non-Functional Requirements

**NFR-E5-001: Pipeline execution time**
- Full pipeline (all stages) must complete in <30 minutes
- Individual port operations (git, filesystem, GitHub API) must complete in <5 seconds each
- Artifact upload/download <5 minutes for typical artifacts (100 MB)

**NFR-E5-002: Secret security**
- ANTHROPIC_API_KEY never logged or echoed
- Accessed only via os.environ.get()
- Secrets not written to artifacts or PR comments
- Epic 4 hook: `security-tier-check` must classify env access as Tier 7+ (block if untrusted)

**NFR-E5-003: Workflow idempotency**
- Re-running same workflow (same issue/PR) must produce identical results (within RNG seed)
- Artifact content deterministic
- No random file names or timestamps

**NFR-E5-004: Error handling & graceful degradation**
- If Xcode port is called: Return NotSupportedInGitHubActionsError (not crash)
- If GITHUB_TOKEN missing: Return AuthenticationError with helpful message
- If GITHUB_WORKSPACE missing: Return EnvironmentError
- All errors must be loggable and result in workflow failure (not silent skip)

**NFR-E5-005: GitHub API quota compliance**
- Assume GitHub Actions rate limit: 5,000 requests/hour
- Estimate per-pipeline: <50 API calls (GET PR, POST comment, check run updates)
- Implement caching for repeated API calls within same workflow run
- Log X-RateLimit-Remaining header

**NFR-E5-006: Artifact persistence across jobs**
- Artifacts must persist from Job A (architect stage) to Job B (downstream stage) if multi-job workflow
- Use GitHub Actions' native artifact storage (not external S3)
- Artifacts automatically available to next job via `actions/download-artifact`

**NFR-E5-007: Headless constraint**
- All operations must work without human interaction (no prompts, no UI)
- No stdin input expected
- No X11 display required

**NFR-E5-008: Hook system integration**
- All port method calls must be loggable for Epic 4 AuditEvent tracking
- Must not violate security-tier-check for bash commands (Tier 1-5 allowed)
- Must support enforce-doc-read hook (skip if no doc enforcement needed)
- Must support validate-output-schema hook (validate stage outputs)

---

## Requirements Cross-Reference

### By Epic 4 Hook Type

| Hook | Requirements | Port |
|------|--------------|------|
| enforce-doc-read | None (skip in headless) | All |
| security-tier-check | FR-E5-001..005, NFR-E5-002 | Git, FS |
| validate-output-schema | FR-E5-016..018 | Context |
| update-pipeline-state | All (AuditEvent logging) | All |

### By Workflow Template

| Workflow | Requirements |
|----------|--------------|
| issue-triggered.yml | FR-E5-020..025 |
| nightly.yml | FR-E5-001..005, 007..009, 011..025 |
| pr-comment.yml | FR-E5-020..024 |

### By Port

| Port | Requirements |
|------|--------------|
| GitOps | FR-E5-001..005, NFR-E5-001, NFR-E5-008 |
| Xcode | FR-E5-006 |
| GitHub | FR-E5-007..010, NFR-E5-005 |
| FileSystem | FR-E5-011..015 |
| StageContext | FR-E5-016..019 |
| Entrypoint | FR-E5-020..024 |

---

## Acceptance Thresholds

- **Code Coverage:** ≥95% of adapter + entrypoint code
- **Test Pass Rate:** 100%
- **Linting:** pylint/flake8 score ≥9.5/10
- **Type Checking:** mypy strict mode, 0 errors
- **Documentation:** All public methods have docstrings (Google style)
- **Performance:** All tests complete in <60 seconds total

