# Epic 5: GitHub Actions Client - Overview

**Status:** Implementation-level PRD
**Version:** 1.0
**Date:** 2026-03-14
**Epic ID:** E5
**Size:** L (50 SP / 5-8 weeks)

---

## Executive Summary

Epic 5 introduces **GitHubActionsAdapter**, a headless CI/CD client that implements all 5 port interfaces (GitOperationsPort, XcodeOperationsPort, GitHubOperationsPort, FileSystemPort, StageContextPort) for automated pipeline execution inside GitHub Actions workflows.

This work enables **full GitOps automation**: Issue → Find → Architect → PR, all executed in headless GitHub Actions without human intervention. The adapter supports 3 workflow templates (issue-triggered, nightly, PR-comment-triggered) and integrates with the Epic 4 hook system for security and compliance enforcement in CI/CD contexts.

**Key capability:** Artifact-backed context storage allows multi-job workflows to persist stage outputs across GitHub Actions job boundaries using `actions/upload-artifact` and `actions/download-artifact`.

---

## Problem Statement

Current system limitations:
- **No CI/CD support**: Pipeline runs only on developer machines with Xcode + interactive CLI
- **No automation**: Architects must manually trigger pipelines for each issue
- **No multi-job workflows**: Cannot decompose pipeline across parallel GitHub Actions jobs
- **No artifact persistence**: Stage context cannot persist across job boundaries
- **No status reporting**: GitHub doesn't know when the pipeline succeeds/fails (no check runs)
- **No secret injection**: No standard pattern for API keys in headless execution

Result: Enterprise adoption impossible. "AI-driven architecture for every PR" requires human orchestration.

---

## Solution Overview

### GitHubActionsAdapter Class

A single adapter class implementing all 5 ports for GitHub Actions context:

```
GitHubActionsAdapter
├── GitOperationsPort (git CLI in GITHUB_WORKSPACE)
├── XcodeOperationsPort (simulated / error on GHA environment)
├── GitHubOperationsPort (GitHub API via GITHUB_TOKEN)
├── FileSystemPort (GITHUB_WORKSPACE directory)
└── StageContextPort (artifact-backed storage)
```

**Key Properties:**
- Single responsibility: Inject GitHub Actions environment variables into all 5 ports
- Dependency injection: Accept all 5 ports in constructor (can use mocks for testing)
- Stateless: No persistent state; all context flows through port method arguments

### 3 Workflow YAML Templates

Automating the full AI Architect pipeline:

| Template | Trigger | Job Flow | Purpose |
|----------|---------|----------|---------|
| **issue-triggered.yml** | Issue opened/labeled | Architect stage → Create PR | Auto-respond to issues with findings |
| **nightly.yml** | Schedule (0 2 * * *) | Full pipeline for recent PRs | Continuous oversight |
| **pr-comment.yml** | PR comment (@architect) | Re-run architect stage | On-demand re-analysis |

Each template:
1. Parses GitHub Actions event payload (issue #, PR #, comment text)
2. Creates Finding object with metadata
3. Runs pipeline stages (only applicable ones)
4. Uploads outputs as artifacts
5. Reports status via GitHub check runs API

### Headless Entrypoint Script

**Path:** `scripts/ci/entrypoint.py`

Single Python script that:
1. Reads `GITHUB_EVENT_PATH` environment variable
2. Parses GitHub Actions event JSON payload
3. Extracts issue #, PR #, or comment context
4. Creates Finding object
5. Instantiates GitHubActionsAdapter with all 5 ports
6. Invokes pipeline runner with Finding
7. Collects stage outputs → uploads as artifacts
8. Reports final status via GitHub API (check runs)

---

## Architecture: 5 Ports in GitHub Actions Context

### 1. GitOperationsPort

**Adapter Method:** Uses git CLI in `GITHUB_WORKSPACE` (default working directory)

- `create_branch`: `git checkout -b branch_name`
- `commit`: `git add files && git commit -m message`
- `push`: `git push origin branch_name`
- `diff`: `git diff base_ref head_ref`
- `log`: `git log branch_name --format=...`

**GitHub Actions Mapping:**
- Pre-cloned repo available at `GITHUB_WORKSPACE`
- Git user configured by GitHub Actions automatically
- GITHUB_TOKEN has write permissions to repo (for push)

### 2. XcodeOperationsPort

**Adapter Method:** Headless environment detection + graceful degradation

- `build()`: Raises `NotSupportedInGitHubActionsError` (no macOS runner by default)
- `test()`: Raises `NotSupportedInGitHubActionsError`
- `preview()`: Raises `NotSupportedInGitHubActionsError`

**Alternative:** Users can add `macos-latest` runner and skip these methods. E5 focuses on Linux environments.

### 3. GitHubOperationsPort

**Adapter Method:** Uses GitHub REST API via `GITHUB_TOKEN` environment variable

- `create_pull_request()`: `POST /repos/{owner}/{repo}/pulls`
- `get_pull_request()`: `GET /repos/{owner}/{repo}/pulls/{number}`
- `add_comment()`: `POST /repos/{owner}/{repo}/issues/{number}/comments`

**GitHub Actions Mapping:**
- `GITHUB_TOKEN` injected automatically by GitHub Actions
- `GITHUB_REPOSITORY` (owner/repo format) available
- Uses `requests` library to call GitHub API

### 4. FileSystemPort

**Adapter Method:** Direct file I/O in `GITHUB_WORKSPACE` directory

- `read(path)`: `open(path).read()`
- `write(path)`: `open(path, 'w').write(content)` + parent dirs created
- `list_directory(path, pattern)`: `glob.glob(pattern)` in path
- `exists(path)`: `os.path.exists(path)`

**GitHub Actions Mapping:**
- All operations scoped to `GITHUB_WORKSPACE`
- No isolation; full read/write access (secured by GitHub Actions sandbox)

### 5. StageContextPort

**Adapter Method:** Artifact-backed storage for multi-job workflows

- `save_artifact(stage_id, finding_id, artifact)`: Write to `artifacts/{stage_id}/{finding_id}.json`, upload via `actions/upload-artifact`
- `load_artifact(stage_id, finding_id)`: Download via `actions/download-artifact`, read from `artifacts/{stage_id}/{finding_id}.json`
- `query_artifacts(finding_id, query)`: List all artifacts for finding_id (in-memory grep)

**GitHub Actions Mapping:**
- Use GitHub Actions `artifacts/` action (native artifact storage)
- Artifacts automatically expire after 90 days (GitHub default)
- Multi-job workflow: Job A uploads, Job B downloads

---

## Dependency on Epic 4

Epic 4 (Hook System Expansion) must be merged first because:
1. **enforce-doc-read hook** must work in headless mode (no user interaction possible)
   - Adapter implementation: Skip interactive prompts; return error if enforcement required
2. **security-tier-check hook** validates bash commands in CI/CD context
   - Adapter implementation: Classify all git/build commands; block Tier 8-10
3. **update-pipeline-state hook** logs all operations to audit trail
   - Adapter implementation: AuditEvent logged for every port call

---

## Enterprise Adoption Enabler

With E5 complete, AI Architect enables:

1. **Auto-respond to issues**: Every issue → Finding → PR within minutes
2. **Continuous architecture oversight**: Nightly runs check all recent PRs
3. **On-demand re-analysis**: @architect mention in PR comment triggers new analysis
4. **Zero-touch GitOps**: Full pipeline without human intervention
5. **Transparent audit trail**: Every decision logged; violations caught by hooks

This is the final piece for enterprise adoption. E1-E4 are local tools; E5 is the CI/CD bridge.

---

## Deliverables

### Adapter Implementation
- `ai_architect_mcp/_adapters/github_actions_adapter.py` (350-400 lines)
- Implements 5 ports + GitHub Actions integration

### Workflow YAML Templates
- `.github/workflows/issue-triggered.yml`
- `.github/workflows/nightly.yml`
- `.github/workflows/pr-comment.yml`

### Entrypoint Script
- `scripts/ci/entrypoint.py` (200-250 lines)

### Tests
- `tests/test_gha_git_ops.py` (80+ lines, 3+ test cases)
- `tests/test_gha_filesystem_ops.py` (80+ lines, 3+ test cases)
- `tests/test_gha_github_ops.py` (100+ lines, 4+ test cases)
- `tests/test_gha_context_ops.py` (100+ lines, 4+ test cases)
- `tests/test_entrypoint.py` (150+ lines, 6+ test cases)
- `tests/test_gha_pipeline_e2e.py` (200+ lines, E2E flow)

### Documentation
- Full technical specification (TBD in prd-technical.md)
- Acceptance criteria (TBD in prd-acceptance.md)
- JIRA tickets (TBD in prd-jira.md)

---

## Success Criteria

### Functional
- All 5 ports implemented and tested
- 3 workflows executable and triggerable via GitHub UI
- Artifact persistence works across 2+ job boundaries
- Check run status updates on PR

### Performance
- Pipeline <30 minutes end-to-end on standard GitHub Actions runner
- Artifact upload/download <5 minutes
- No git large-file issues

### Security
- ANTHROPIC_API_KEY never logged; only accessed via environment
- GITHUB_TOKEN scoped minimally (pull-request + contents)
- All operations logged via Epic 4 hooks

### Reliability
- Workflow idempotency: Re-run same issue → same results
- Error handling: Graceful failure if Xcode not available
- Rollback path: Disable workflow via branch protection rules

---

## Timeline & Effort

**Total: 50 SP over 5-8 weeks**

- **Sprint 1 (Week 1):** Adapter core + GitOps port (8 SP)
- **Sprint 2 (Week 2):** FileSystem + GitHub ports (8 SP)
- **Sprint 3 (Week 3):** Context port + entrypoint (9 SP)
- **Sprint 4 (Week 4-5):** 3 workflow templates + E2E testing (13 SP)
- **Sprint 5 (Week 6-8):** Performance tuning, hook integration, docs (12 SP)

---

## Out of Scope

- macOS / Xcode-specific GitHub Actions runners (can be added in E6)
- Artifact encryption at rest (rely on GitHub's infrastructure encryption)
- Custom GitHub Actions written in TypeScript (Python entrypoint only)
- Rate limiting / backoff logic for GitHub API (assume standard quota)
