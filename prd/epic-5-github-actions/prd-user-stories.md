# Epic 5: GitHub Actions Client - User Stories

**Document:** prd-user-stories.md
**Version:** 1.0
**Date:** 2026-03-14
**Total SP:** 50 (Fibonacci: 3, 5, 8)

---

## Story STORY-E5-001: GitOperationsPort Adapter Implementation

**Story ID:** STORY-E5-001
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline engineer**, I want to **implement GitOperationsPort for GitHub Actions context** so that **git operations (branch, commit, push) work in headless CI/CD workflows**.

### Description

Implement the GitOperationsPort adapter for GitHub Actions. All 5 git methods must execute in the GITHUB_WORKSPACE directory using the git CLI. The adapter must handle GITHUB_TOKEN authentication for push operations and return results compatible with the pipeline stage logic.

### Acceptance Criteria

**AC-E5-001:** create_branch() method implemented
- [ ] Method signature: `async def create_branch(branch_name: str, base: str = "main") -> str`
- [ ] Executes `git checkout -b branch_name origin/base` in GITHUB_WORKSPACE
- [ ] Returns full branch reference (e.g., `refs/heads/feature/finding-123`)
- [ ] Raises GitError if base branch doesn't exist
- [ ] Latency: <2 seconds for typical operation

**AC-E5-002:** commit() method implemented
- [ ] Method signature: `async def commit(message: str, files: list[str]) -> str`
- [ ] Stages files: `git add files`
- [ ] Creates commit: `git commit -m message`
- [ ] Returns commit SHA (40 hex characters)
- [ ] Raises GitError if no changes to commit
- [ ] Validates all files in list exist before staging

**AC-E5-003:** push() method implemented
- [ ] Method signature: `async def push(branch: str, force: bool = False) -> None`
- [ ] Executes `git push origin branch` (with `--force` if force=True)
- [ ] Requires GITHUB_TOKEN environment variable set
- [ ] Raises AuthenticationError if GITHUB_TOKEN missing
- [ ] Raises GitError if remote branch doesn't exist

**AC-E5-004:** diff() and log() methods implemented
- [ ] diff(base, head) returns unified diff as string
- [ ] log(branch, count=10) returns list[dict] with sha, message, author, date
- [ ] Both methods work with branch names or SHAs
- [ ] Parsing: Correct extraction from `git diff` and `git log --format=` output

**AC-E5-005:** GITHUB_WORKSPACE boundary enforcement
- [ ] All git operations execute in GITHUB_WORKSPACE
- [ ] CWD checked at adapter initialization
- [ ] FileNotFoundError if GITHUB_WORKSPACE env var missing
- [ ] Integration test: Create branch, commit, push in mock environment

### Related Requirements

- FR-E5-001: Git branch creation
- FR-E5-002: Git commit
- FR-E5-003: Git push
- FR-E5-004: Git diff
- FR-E5-005: Git log

### Related Stories

None (foundational)

### Dependencies

- Git CLI installed on runner
- GITHUB_WORKSPACE environment variable available
- Epic 4: Hook integration for audit logging

### Effort Breakdown

- create_branch implementation: 1 SP
- commit/push implementation: 2 SP
- diff/log implementation: 1.5 SP
- Testing + GITHUB_WORKSPACE validation: 0.5 SP
- **Total: 5 SP**

---

## Story STORY-E5-002: FileSystemPort Adapter Implementation

**Story ID:** STORY-E5-002
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline engineer**, I want to **implement FileSystemPort for GitHub Actions** so that **file operations (read, write, list) work in the headless workspace**.

### Description

Implement FileSystemPort adapter for GitHub Actions. All operations must be scoped to GITHUB_WORKSPACE and enforce path traversal boundaries. Parent directories must be created on write operations.

### Acceptance Criteria

**AC-E5-006:** read() method implemented
- [ ] Method signature: `async def read(path: Path) -> str`
- [ ] Returns file contents as string
- [ ] Raises FileNotFoundError if path doesn't exist
- [ ] Enforces GITHUB_WORKSPACE boundary (reject absolute paths outside workspace)

**AC-E5-007:** write() method implemented
- [ ] Method signature: `async def write(path: Path, content: str) -> None`
- [ ] Creates parent directories as needed
- [ ] Overwrites existing files
- [ ] Enforces GITHUB_WORKSPACE boundary
- [ ] Raises ValueError if path attempts traversal outside workspace

**AC-E5-008:** list_directory() and exists() methods
- [ ] list_directory(path, pattern="*") returns list[Path]
- [ ] Pattern matching: glob.glob() semantics
- [ ] exists(path) returns bool for files and directories
- [ ] Both enforce GITHUB_WORKSPACE boundary

**AC-E5-009:** Path boundary enforcement implemented
- [ ] Use Path.resolve() to canonicalize paths
- [ ] Compare resolved path to GITHUB_WORKSPACE base
- [ ] Reject paths outside workspace with ValueError
- [ ] Reject `../` traversal attempts
- [ ] Test: Attempt to read /etc/passwd → ValueError

### Related Requirements

- FR-E5-011: File read
- FR-E5-012: File write
- FR-E5-013: Directory listing
- FR-E5-014: Existence check
- FR-E5-015: Workspace boundary

### Related Stories

None (foundational)

### Dependencies

- pathlib library (stdlib)
- GITHUB_WORKSPACE environment variable

### Effort Breakdown

- read/write/list/exists implementation: 1.5 SP
- Boundary enforcement: 1 SP
- Security testing: 0.5 SP
- **Total: 3 SP**

---

## Story STORY-E5-003: GitHubOperationsPort Adapter Implementation

**Story ID:** STORY-E5-003
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline engineer**, I want to **implement GitHubOperationsPort for GitHub Actions** so that **PR creation, querying, and commenting work in CI/CD context**.

### Description

Implement GitHubOperationsPort adapter using GitHub REST API. All operations must use GITHUB_TOKEN for authentication and GITHUB_REPOSITORY for owner/repo context. Implement rate limit handling and exponential backoff.

### Acceptance Criteria

**AC-E5-010:** create_pull_request() method
- [ ] Method signature: `async def create_pull_request(title, body, head, base="main") -> dict`
- [ ] Calls `POST /repos/{owner}/{repo}/pulls`
- [ ] Returns dict with `number`, `url`, `state` keys
- [ ] Raises AuthenticationError if GITHUB_TOKEN missing
- [ ] Raises APIError if PR creation fails (e.g., head branch doesn't exist)

**AC-E5-011:** get_pull_request() method
- [ ] Method signature: `async def get_pull_request(pr_number: int) -> dict`
- [ ] Calls `GET /repos/{owner}/{repo}/pulls/{number}`
- [ ] Returns dict with status, checks, review state
- [ ] Raises NotFoundError if PR doesn't exist

**AC-E5-012:** add_comment() method
- [ ] Method signature: `async def add_comment(pr_number: int, body: str) -> dict`
- [ ] Calls `POST /repos/{owner}/{repo}/issues/{number}/comments`
- [ ] Returns dict with `id`, `url` keys
- [ ] Markdown formatting preserved in body

**AC-E5-013:** Rate limit handling
- [ ] Detect 429 responses
- [ ] Implement exponential backoff: 1s, 2s, 4s (3 retries max)
- [ ] Log X-RateLimit-Remaining header value
- [ ] Raise RateLimitError if all retries exhausted

**AC-E5-014:** Environment variables extracted
- [ ] GITHUB_TOKEN: Authentication token
- [ ] GITHUB_REPOSITORY: owner/repo format
- [ ] Both required; raise EnvironmentError if missing
- [ ] Token scoped minimally: pull-request, contents

### Related Requirements

- FR-E5-007: PR creation
- FR-E5-008: PR details
- FR-E5-009: PR comment
- FR-E5-010: Rate limiting

### Related Stories

None (foundational)

### Dependencies

- requests library (for HTTP calls)
- GITHUB_TOKEN environment variable
- GITHUB_REPOSITORY environment variable

### Effort Breakdown

- PR API methods (create, get, comment): 2 SP
- Rate limit handling + retries: 2 SP
- Error handling + environment setup: 1 SP
- **Total: 5 SP**

---

## Story STORY-E5-004: StageContextPort Adapter (Artifact-Backed Storage)

**Story ID:** STORY-E5-004
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline engineer**, I want to **implement StageContextPort using artifact-backed storage** so that **stage outputs persist across GitHub Actions job boundaries**.

### Description

Implement StageContextPort adapter using local `artifacts/` directory and GitHub Actions artifact actions. The adapter saves/loads artifacts as JSON files and integrates with GitHub Actions workflow artifact upload/download actions.

### Acceptance Criteria

**AC-E5-015:** save_artifact() method
- [ ] Method signature: `async def save_artifact(stage_id: int, finding_id: str, artifact: dict) -> None`
- [ ] Writes artifact to `artifacts/{stage_id}/{finding_id}.json`
- [ ] Creates `artifacts/` directory if missing
- [ ] Serializes dict to JSON (sorted keys, indent 2)
- [ ] Overwrites existing artifacts

**AC-E5-016:** load_artifact() method
- [ ] Method signature: `async def load_artifact(stage_id: int, finding_id: str) -> dict`
- [ ] Reads from `artifacts/{stage_id}/{finding_id}.json`
- [ ] Returns deserialized dict
- [ ] Raises FileNotFoundError if artifact doesn't exist
- [ ] Raises JSONDecodeError if corrupt JSON

**AC-E5-017:** query_artifacts() method
- [ ] Method signature: `async def query_artifacts(finding_id: str, query: str) -> list[dict]`
- [ ] Lists all artifacts for finding_id across stages
- [ ] Filters by query: exact key match or regex value match
- [ ] Returns list of matching artifact dicts with metadata (stage_id, finding_id)

**AC-E5-018:** Multi-job workflow support
- [ ] Job A saves artifact via save_artifact()
- [ ] artifacts/` directory uploaded via `actions/upload-artifact`
- [ ] Job B downloads artifacts via `actions/download-artifact`
- [ ] Job B loads artifact via load_artifact()
- [ ] Test: Simulate 2-job workflow in test environment

**AC-E5-019:** Artifact retention & cleanup
- [ ] Artifacts written to GITHUB_WORKSPACE/artifacts/
- [ ] Retention: 90 days (GitHub default) via actions/upload-artifact
- [ ] Auto-cleanup: Older artifacts deleted by GitHub
- [ ] No manual cleanup code needed

### Related Requirements

- FR-E5-016: Artifact save
- FR-E5-017: Artifact load
- FR-E5-018: Artifact query
- FR-E5-019: GitHub Actions artifact integration

### Related Stories

None (foundational)

### Dependencies

- pathlib, json (stdlib)
- GitHub Actions `actions/upload-artifact@v3`
- GitHub Actions `actions/download-artifact@v3`

### Effort Breakdown

- save/load/query methods: 2 SP
- Multi-job workflow integration: 2 SP
- Testing (incl. 2-job simulation): 1 SP
- **Total: 5 SP**

---

## Story STORY-E5-005: XcodeOperationsPort Adapter (Headless Stub)

**Story ID:** STORY-E5-005
**Epic:** E5 (GitHub Actions Client)
**Priority:** P1
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline engineer**, I want to **implement XcodeOperationsPort for GitHub Actions** so that **stage logic doesn't crash if Xcode methods are called**.

### Description

Implement XcodeOperationsPort adapter as a headless stub. All 3 methods (build, test, preview) must raise NotSupportedInGitHubActionsError with a helpful message. This is a safe fallback for pipelines that may call Xcode operations.

### Acceptance Criteria

**AC-E5-020:** build() method stub
- [ ] Method signature: `async def build(scheme: str, configuration: str = "Debug") -> dict`
- [ ] Raises NotSupportedInGitHubActionsError
- [ ] Error message: "Xcode operations not supported in headless GitHub Actions environment. Use macOS runner for native builds."

**AC-E5-021:** test() and preview() method stubs
- [ ] test(scheme, test_plan=None) raises NotSupportedInGitHubActionsError
- [ ] preview(view_name) raises NotSupportedInGitHubActionsError
- [ ] Consistent error messages

**AC-E5-022:** Error type definition
- [ ] Create custom exception: `class NotSupportedInGitHubActionsError(Exception)`
- [ ] Inherit from Exception
- [ ] Include helpful message in docstring

**AC-E5-023:** Test error handling
- [ ] Test: Calling build() raises exception
- [ ] Test: Calling test() raises exception
- [ ] Test: Calling preview() raises exception
- [ ] Verify error message includes "macOS runner" suggestion

### Related Requirements

- FR-E5-006: Xcode unavailable

### Related Stories

None (foundational)

### Dependencies

- None (stdlib only)

### Effort Breakdown

- Exception class + method stubs: 1 SP
- Error messages + testing: 1 SP
- Documentation: 1 SP
- **Total: 3 SP**

---

## Story STORY-E5-006: Headless Entrypoint Script Implementation

**Story ID:** STORY-E5-006
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **GitHub Actions workflow author**, I want to **invoke the pipeline from a workflow** so that **the AI Architect pipeline executes in CI/CD**.

### Description

Implement `scripts/ci/entrypoint.py` script that reads GitHub Actions event payloads, creates Finding objects, instantiates GitHubActionsAdapter, runs the pipeline, and reports results. This is the CLI entry point for all 3 workflow templates.

### Acceptance Criteria

**AC-E5-024:** Event payload parsing
- [ ] Script reads `GITHUB_EVENT_PATH` environment variable
- [ ] Parses JSON event payload
- [ ] Extracts context: issue #, PR #, comment text, actor, timestamp
- [ ] Raises EnvironmentError if GITHUB_EVENT_PATH missing

**AC-E5-025:** Finding object creation
- [ ] Create Finding instance with metadata from event
- [ ] Populate: issue_number, pr_number, comment_text, actor, timestamp
- [ ] Generate unique finding_id (format: e.g., `finding-20260314-001`)
- [ ] Log Finding object to stdout (JSON format)

**AC-E5-026:** GitHubActionsAdapter instantiation
- [ ] Instantiate all 5 port adapters (GitOps, GitHub, FileSystem, StageContext, Xcode)
- [ ] Inject into GitHubActionsAdapter constructor
- [ ] Log adapter initialization to stdout

**AC-E5-027:** Pipeline invocation
- [ ] Call pipeline runner with Finding object
- [ ] Capture stage outputs
- [ ] Log stage completion to stdout
- [ ] Handle pipeline exceptions gracefully

**AC-E5-028:** Artifact collection & reporting
- [ ] Collect all stage outputs
- [ ] Write artifacts to `artifacts/{stage_id}/{finding_id}.json`
- [ ] Create GitHub check run on PR/commit
- [ ] Update check run status: in_progress → completed (success/failure)
- [ ] Include summary: finding count, stage names, errors

### Related Requirements

- FR-E5-020: Event parsing
- FR-E5-021: Finding creation
- FR-E5-022: Pipeline invocation
- FR-E5-023: Artifact collection
- FR-E5-024: Check run reporting

### Related Stories

- STORY-E5-001 (GitOps adapter must be done first)
- STORY-E5-002 (FileSystem adapter must be done first)
- STORY-E5-003 (GitHub adapter must be done first)
- STORY-E5-004 (Context adapter must be done first)
- STORY-E5-005 (Xcode adapter must be done first)

### Dependencies

- All 5 port adapters (STORY-E5-001..005)
- GitHub Actions environment variables (GITHUB_EVENT_PATH, GITHUB_TOKEN, GITHUB_REPOSITORY)

### Effort Breakdown

- Event parsing + Finding creation: 1.5 SP
- Adapter instantiation: 1 SP
- Pipeline invocation + artifact collection: 1.5 SP
- Check run API integration: 1 SP
- **Total: 5 SP**

---

## Story STORY-E5-007: Issue-Triggered Workflow Implementation

**Story ID:** STORY-E5-007
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **repository maintainer**, I want to **auto-respond to issues with PR findings** so that **every issue gets architectural analysis without manual triggers**.

### Description

Implement `.github/workflows/issue-triggered.yml` workflow that activates when issues are opened/reopened. The workflow parses the issue, creates a Finding, runs the architect stage only, and opens a PR with findings.

### Acceptance Criteria

**AC-E5-029:** Workflow trigger configuration
- [ ] Trigger: `on: { issues: { types: [opened, reopened] } }`
- [ ] Filters: Optional label filter (e.g., "needs-architecture")
- [ ] Runs on every issue or filtered issues

**AC-E5-030:** Workflow job steps
- [ ] Step 1: Checkout repository (`actions/checkout@v4`)
- [ ] Step 2: Set up Python 3.11 (`actions/setup-python@v4`)
- [ ] Step 3: Install dependencies (`pip install -r requirements.txt`)
- [ ] Step 4: Run entrypoint script (`python scripts/ci/entrypoint.py`)
- [ ] Step 5: Create PR with findings (`gh pr create` or adapter method)

**AC-E5-031:** Issue → Finding mapping
- [ ] Extract issue #, title, body, author from GITHUB_EVENT_PATH
- [ ] Create Finding with issue_number, title, description
- [ ] Stage: architect only (not full pipeline)

**AC-E5-032:** PR creation in workflow
- [ ] PR title: "Architecture Analysis for Issue #{issue_number}"
- [ ] PR body: Artifact outputs (findings, recommendations)
- [ ] PR branch: feature/issue-{issue_number}-architecture
- [ ] Link back to issue in PR body

**AC-E5-033:** Secrets management
- [ ] GITHUB_TOKEN: Automatically available in GitHub Actions
- [ ] ANTHROPIC_API_KEY: Via `secrets.ANTHROPIC_API_KEY` (must be configured in repo settings)
- [ ] Both passed as environment variables to entrypoint
- [ ] Never logged or echoed

### Related Requirements

- FR-E5-025: Issue-triggered workflow
- FR-E5-020..024: Entrypoint script

### Related Stories

- STORY-E5-006 (Entrypoint must be implemented first)

### Dependencies

- All adapters (STORY-E5-001..005)
- Entrypoint script (STORY-E5-006)
- Repository secrets configured (ANTHROPIC_API_KEY)

### Effort Breakdown

- Workflow YAML structure + triggers: 1.5 SP
- Job steps + environment setup: 1.5 SP
- Issue parsing + Finding creation: 1 SP
- PR creation integration: 1 SP
- **Total: 5 SP**

---

## Story STORY-E5-008: Nightly Workflow Implementation

**Story ID:** STORY-E5-008
**Epic:** E5 (GitHub Actions Client)
**Priority:** P1
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **architecture team**, I want to **continuously analyze recent PRs** so that **we catch architectural issues before they merge**.

### Description

Implement `.github/workflows/nightly.yml` workflow that runs on schedule (0 2 * * * UTC, nightly at 2am). The workflow runs the full pipeline against recent PRs and logs findings.

### Acceptance Criteria

**AC-E5-034:** Workflow trigger configuration
- [ ] Trigger: `on: { schedule: [cron: '0 2 * * *'] }`
- [ ] Runs daily at 2 AM UTC
- [ ] Manually triggerable via GitHub Actions UI

**AC-E5-035:** Nightly job steps
- [ ] Checkout latest main
- [ ] Query recent PRs (last 24 hours): `gh pr list`
- [ ] For each PR: Create Finding, run full pipeline
- [ ] Aggregate findings into report
- [ ] Post report as comment on each PR

**AC-E5-036:** PR discovery
- [ ] Use `gh pr list --state open --order created`
- [ ] Filter to PRs updated in last 24 hours
- [ ] Skip already-analyzed PRs (check previous run artifacts)

### Related Requirements

- FR-E5-001..024 (All port implementations)

### Related Stories

- STORY-E5-001..006 (All adapters + entrypoint)

### Dependencies

- GitHub CLI (gh) installed
- All adapters + entrypoint

### Effort Breakdown

- Workflow YAML + scheduling: 1 SP
- PR discovery logic: 1 SP
- Aggregation + reporting: 1 SP
- **Total: 3 SP**

---

## Story STORY-E5-009: PR-Comment-Triggered Workflow Implementation

**Story ID:** STORY-E5-009
**Epic:** E5 (GitHub Actions Client)
**Priority:** P2
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **developer**, I want to **re-analyze a PR by mentioning @architect** so that **I can re-run the pipeline on demand**.

### Description

Implement `.github/workflows/pr-comment.yml` workflow that activates when a PR comment mentions @architect. The workflow re-runs the architect stage and posts updated findings.

### Acceptance Criteria

**AC-E5-037:** Comment trigger setup
- [ ] Trigger: `on: { issue_comment: { types: [created, edited] } }`
- [ ] Filter: Parse comment body; activate only if mentions "@architect"
- [ ] Check PR context: Only run on PRs (not issues)

**AC-E5-038:** Workflow execution on mention
- [ ] Checkout PR branch
- [ ] Create Finding from PR + comment context
- [ ] Run architect stage
- [ ] Post results as comment reply

**AC-E5-039:** Comment parsing
- [ ] Extract mention: Check if comment contains "@architect"
- [ ] Extract PR number from context
- [ ] Log comment author and timestamp

### Related Requirements

- FR-E5-020..024 (Entrypoint + artifact handling)

### Related Stories

- STORY-E5-006..007 (Entrypoint + issue workflow as reference)

### Dependencies

- All adapters + entrypoint

### Effort Breakdown

- Comment trigger + parsing: 1 SP
- Workflow execution: 1 SP
- Results posting: 1 SP
- **Total: 3 SP**

---

## Story STORY-E5-010: Artifact Collection & Multi-Job Integration

**Story ID:** STORY-E5-010
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 3
**Status:** New
**Owner:** TBD

### User Story

As a **pipeline engineer**, I want to **share stage outputs across GitHub Actions jobs** so that **complex workflows can parallelize architecture analysis**.

### Description

Implement artifact upload/download logic in workflows to support multi-job pipelines. Each job uploads its stage artifacts, and downstream jobs download and process them.

### Acceptance Criteria

**AC-E5-040:** Artifact upload in workflows
- [ ] After entrypoint executes, upload artifacts/` directory
- [ ] Use `actions/upload-artifact@v3` action
- [ ] Artifact name: finding-{finding_id}
- [ ] Retention: 90 days (default)

**AC-E5-041:** Artifact download in downstream jobs
- [ ] Use `actions/download-artifact@v3` action
- [ ] Restore artifacts/ directory structure
- [ ] Load artifacts via StageContextPort.load_artifact()

**AC-E5-042:** Multi-job workflow test
- [ ] Simulate 2-job workflow: architect-stage → downstream-stage
- [ ] Job A creates artifacts, uploads
- [ ] Job B downloads, loads, processes artifacts
- [ ] Verify data integrity (same data in → same data out)

### Related Requirements

- FR-E5-016..019 (StageContextPort)

### Related Stories

- STORY-E5-004 (StageContextPort adapter)

### Dependencies

- All adapters

### Effort Breakdown

- Upload/download action setup: 1 SP
- Multi-job integration testing: 1.5 SP
- Documentation: 0.5 SP
- **Total: 3 SP**

---

## Story STORY-E5-011: GitHub Check Run Status Reporting

**Story ID:** STORY-E5-011
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **developer**, I want to **see architectural findings as GitHub check runs** so that **I know immediately if architecture analysis passed/failed**.

### Description

Implement GitHub check run API integration in the entrypoint script. The script creates a check run at the start of the pipeline and updates it with final status (success/failure) and a detailed summary.

### Acceptance Criteria

**AC-E5-043:** Check run creation
- [ ] Call `POST /repos/{owner}/{repo}/check-runs`
- [ ] Name: "AI Architect - Finding Analysis"
- [ ] Status: in_progress
- [ ] Commit SHA from GITHUB_SHA environment variable

**AC-E5-044:** Check run completion
- [ ] After pipeline finishes: Call `PATCH /repos/{owner}/{repo}/check-runs/{id}`
- [ ] Update status: completed
- [ ] Conclusion: success or failure (based on pipeline result)
- [ ] Summary: Findings count, stage names, execution time

**AC-E5-045:** Summary formatting
- [ ] Include: Finding count, stage names executed, errors (if any)
- [ ] Format as markdown
- [ ] Include links to PR/issue (if available)

**AC-E5-046:** Error handling in check run
- [ ] Pipeline exception → conclusion: failure
- [ ] Log error details to check run output
- [ ] Failure message: "Pipeline failed: {exception message}"

### Related Requirements

- FR-E5-024: Check run status reporting
- NFR-E5-001: Error handling

### Related Stories

- STORY-E5-006 (Entrypoint script)

### Dependencies

- GitHub API (check runs endpoint)
- GITHUB_TOKEN environment variable
- GITHUB_SHA environment variable

### Effort Breakdown

- Check run creation + completion: 2 SP
- Summary formatting + markdown: 1.5 SP
- Error handling: 1 SP
- Testing (mock GitHub API): 0.5 SP
- **Total: 5 SP**

---

## Story STORY-E5-012: E2E Test - Issue to PR Flow

**Story ID:** STORY-E5-012
**Epic:** E5 (GitHub Actions Client)
**Priority:** P0
**Story Points:** 5
**Status:** New
**Owner:** TBD

### User Story

As a **QA engineer**, I want to **test the full issue→PR pipeline** so that **we verify end-to-end functionality before deployment**.

### Description

Implement comprehensive E2E test that simulates the issue-triggered workflow: GitHub issue created → entrypoint invoked → Finding created → PR opened → findings reported. Uses mocked GitHub API and filesystem.

### Acceptance Criteria

**AC-E5-047:** E2E test setup
- [ ] Test file: `tests/test_gha_pipeline_e2e.py`
- [ ] Mock GitHub API responses (issue, PR creation, check runs)
- [ ] Mock filesystem (GITHUB_WORKSPACE)
- [ ] Create realistic GitHub Actions event payload

**AC-E5-048:** Full flow execution
- [ ] Simulate GitHub Actions environment (env vars set)
- [ ] Call entrypoint script with mocked event
- [ ] Verify Finding created correctly
- [ ] Verify adapters instantiated
- [ ] Verify pipeline runner invoked

**AC-E5-049:** Artifact verification
- [ ] Verify artifacts written to artifacts/` directory
- [ ] Verify artifact contents match expected schema
- [ ] Verify JSON serialization correct

**AC-E5-050:** PR and check run verification
- [ ] Verify PR creation API called with correct params
- [ ] Verify check run creation + update calls
- [ ] Verify summary formatted correctly

### Related Requirements

- FR-E5-020..024 (Entrypoint script)
- NFR-E5-003: Idempotency

### Related Stories

- All STORY-E5-001..011 (All components must be tested)

### Dependencies

- All adapters + entrypoint
- pytest, pytest-asyncio
- Mock libraries (unittest.mock)

### Effort Breakdown

- Test infrastructure + mocks: 1.5 SP
- Flow execution + assertions: 2 SP
- Artifact + API verification: 1 SP
- Edge case handling: 0.5 SP
- **Total: 5 SP**

---

## Story Point Summary

| Story | SP | Status |
|-------|-----|--------|
| STORY-E5-001: GitOps adapter | 5 | New |
| STORY-E5-002: FileSystem adapter | 3 | New |
| STORY-E5-003: GitHub adapter | 5 | New |
| STORY-E5-004: Context adapter | 5 | New |
| STORY-E5-005: Xcode adapter | 3 | New |
| STORY-E5-006: Entrypoint script | 5 | New |
| STORY-E5-007: Issue-triggered workflow | 5 | New |
| STORY-E5-008: Nightly workflow | 3 | New |
| STORY-E5-009: PR-comment workflow | 3 | New |
| STORY-E5-010: Artifact collection | 3 | New |
| STORY-E5-011: Check run status | 5 | New |
| STORY-E5-012: E2E test | 5 | New |
| | **50** | |

