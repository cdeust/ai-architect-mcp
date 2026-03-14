# Epic 5: GitHub Actions Client - Technical Specification

**Document:** prd-technical.md
**Version:** 1.0
**Date:** 2026-03-14

---

## Table of Contents

1. GitHubActionsAdapter Architecture
2. Port Implementations (5 ports)
3. Entrypoint Script Design
4. Workflow YAML Templates
5. Artifact Storage & Multi-Job Integration
6. Secret Injection Pattern
7. Error Handling & Logging
8. Performance Characteristics

---

## 1. GitHubActionsAdapter Architecture

### 1.1 Class Design

```python
class GitHubActionsAdapter:
    """Implements all 5 ports for GitHub Actions execution context.

    Dependency injection pattern: All port adapters injected via constructor.
    Enables unit testing with mocks.

    Public Properties:
    - git_ops: GitOperationsPort implementation
    - xcode_ops: XcodeOperationsPort implementation
    - github_ops: GitHubOperationsPort implementation
    - fs_ops: FileSystemPort implementation
    - context_ops: StageContextPort implementation
    """

    def __init__(
        self,
        git_ops: GitOperationsPort,
        xcode_ops: XcodeOperationsPort,
        github_ops: GitHubOperationsPort,
        fs_ops: FileSystemPort,
        context_ops: StageContextPort,
    ):
        """Initialize adapter with all 5 port implementations."""
        self.git_ops = git_ops
        self.xcode_ops = xcode_ops
        self.github_ops = github_ops
        self.fs_ops = fs_ops
        self.context_ops = context_ops

        # Validate environment
        self._validate_github_actions_env()

    def _validate_github_actions_env(self) -> None:
        """Verify required GitHub Actions environment variables."""
        required = ['GITHUB_WORKSPACE', 'GITHUB_TOKEN', 'GITHUB_REPOSITORY']
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise EnvironmentError(
                f"Missing GitHub Actions env vars: {missing}"
            )
```

### 1.2 Instantiation Pattern

For production (in workflows):

```python
# In entrypoint.py
from ai_architect_mcp._adapters.github_actions_adapter import (
    GitHubActionsAdapter,
)
from ai_architect_mcp._adapters.github_actions_impl import (
    GitOpsAdapterImpl,
    FileSystemAdapterImpl,
    GitHubAdapterImpl,
    XcodeAdapterImpl,
    ContextAdapterImpl,
)

adapter = GitHubActionsAdapter(
    git_ops=GitOpsAdapterImpl(),
    xcode_ops=XcodeAdapterImpl(),
    github_ops=GitHubAdapterImpl(),
    fs_ops=FileSystemAdapterImpl(),
    context_ops=ContextAdapterImpl(),
)
```

For testing (with mocks):

```python
# In tests
adapter = GitHubActionsAdapter(
    git_ops=Mock(spec=GitOperationsPort),
    xcode_ops=Mock(spec=XcodeOperationsPort),
    github_ops=Mock(spec=GitHubOperationsPort),
    fs_ops=Mock(spec=FileSystemPort),
    context_ops=Mock(spec=StageContextPort),
)
```

---

## 2. Port Implementations (5 Ports)

### 2.1 GitOperationsPort Implementation

**File:** `ai_architect_mcp/_adapters/github_actions_impl.py` (GitOpsAdapterImpl)

```python
class GitOpsAdapterImpl(GitOperationsPort):
    """Git operations in GITHUB_WORKSPACE via CLI."""

    def __init__(self):
        self.workspace = Path(os.getenv('GITHUB_WORKSPACE', '.'))
        self._validate_workspace()

    def _validate_workspace(self) -> None:
        """Ensure GITHUB_WORKSPACE exists and is a git repo."""
        if not self.workspace.exists():
            raise FileNotFoundError(f"GITHUB_WORKSPACE not found: {self.workspace}")
        if not (self.workspace / '.git').exists():
            raise ValueError(f"Not a git repository: {self.workspace}")

    async def create_branch(self, branch_name: str, base: str = "main") -> str:
        """Create branch from base."""
        cmd = f"git checkout -b {branch_name} origin/{base}"
        result = await self._run_git(cmd)
        if result.returncode != 0:
            raise GitError(f"Failed to create branch: {result.stderr}")
        return f"refs/heads/{branch_name}"

    async def commit(self, message: str, files: list[str]) -> str:
        """Stage files and commit."""
        # Stage files
        for file in files:
            if not (self.workspace / file).exists():
                raise FileNotFoundError(f"File not found: {file}")

        files_str = " ".join(f'"{f}"' for f in files)
        stage_cmd = f"git add {files_str}"
        await self._run_git(stage_cmd)

        # Commit
        commit_cmd = f"git commit -m {shlex.quote(message)}"
        result = await self._run_git(commit_cmd)

        # Extract SHA
        sha = result.stdout.strip().split()[2]  # Regex: ([a-f0-9]{40})
        return sha

    async def push(self, branch: str, force: bool = False) -> None:
        """Push branch to remote."""
        force_flag = "--force" if force else ""
        cmd = f"git push origin {branch} {force_flag}".strip()
        result = await self._run_git(cmd)
        if result.returncode != 0:
            raise GitError(f"Push failed: {result.stderr}")

    async def diff(self, base: str, head: str) -> str:
        """Get diff between refs."""
        cmd = f"git diff {base}..{head}"
        result = await self._run_git(cmd)
        return result.stdout

    async def log(self, branch: str, count: int = 10) -> list[dict[str, str]]:
        """Get commit log."""
        fmt = "%H%n%s%n%an%n%ai%n--COMMIT_END--"
        cmd = f"git log {branch} -n {count} --format={shlex.quote(fmt)}"
        result = await self._run_git(cmd)

        # Parse output
        entries = []
        for chunk in result.stdout.split("--COMMIT_END--"):
            lines = chunk.strip().split("\n")
            if len(lines) >= 4:
                entries.append({
                    'sha': lines[0],
                    'message': lines[1],
                    'author': lines[2],
                    'date': lines[3],
                })
        return entries

    async def _run_git(self, cmd: str) -> subprocess.CompletedProcess:
        """Run git command in GITHUB_WORKSPACE."""
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=str(self.workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
        )
```

**Environment Mapping:**
- `GITHUB_WORKSPACE`: Working directory for git commands
- `GITHUB_TOKEN`: Implicit; git uses it for push (pre-configured by GitHub Actions)
- `GITHUB_REPOSITORY`: Not needed; git uses origin remote (pre-configured)

### 2.2 FileSystemPort Implementation

**File:** `ai_architect_mcp/_adapters/github_actions_impl.py` (FileSystemAdapterImpl)

```python
class FileSystemAdapterImpl(FileSystemPort):
    """File operations in GITHUB_WORKSPACE."""

    def __init__(self):
        self.workspace = Path(os.getenv('GITHUB_WORKSPACE', '.'))

    def _validate_path(self, path: Path) -> Path:
        """Ensure path is within GITHUB_WORKSPACE."""
        resolved = (self.workspace / path).resolve()
        workspace_resolved = self.workspace.resolve()

        if not str(resolved).startswith(str(workspace_resolved)):
            raise ValueError(
                f"Path traversal attempted: {path} outside {self.workspace}"
            )
        return resolved

    async def read(self, path: Path) -> str:
        """Read file contents."""
        validated = self._validate_path(path)
        if not validated.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return validated.read_text()

    async def write(self, path: Path, content: str) -> None:
        """Write file contents."""
        validated = self._validate_path(path)
        validated.parent.mkdir(parents=True, exist_ok=True)
        validated.write_text(content)

    async def list_directory(
        self, path: Path, pattern: str = "*"
    ) -> list[Path]:
        """List directory."""
        validated = self._validate_path(path)
        if not validated.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        matches = validated.glob(pattern)
        return [p for p in matches if self._validate_path(p)]

    async def exists(self, path: Path) -> bool:
        """Check path existence."""
        try:
            self._validate_path(path)
            return (self.workspace / path).exists()
        except ValueError:
            return False
```

**Environment Mapping:**
- `GITHUB_WORKSPACE`: All file operations scoped here
- No other environment variables needed

### 2.3 GitHubOperationsPort Implementation

**File:** `ai_architect_mcp/_adapters/github_actions_impl.py` (GitHubAdapterImpl)

```python
class GitHubAdapterImpl(GitHubOperationsPort):
    """GitHub API operations via REST API."""

    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.repository = os.getenv('GITHUB_REPOSITORY')  # format: owner/repo

        if not self.token:
            raise EnvironmentError("GITHUB_TOKEN not set")
        if not self.repository:
            raise EnvironmentError("GITHUB_REPOSITORY not set")

        owner, repo = self.repository.split('/')
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.session = None  # Lazy init

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"token {self.token}"}
            )
        return self.session

    async def _api_call(
        self,
        method: str,
        endpoint: str,
        json_data: dict = None,
        retries: int = 3,
    ) -> dict:
        """Make GitHub API call with retry logic."""
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()

        for attempt in range(retries):
            try:
                async with session.request(
                    method, url, json=json_data
                ) as resp:
                    if resp.status == 429:  # Rate limited
                        wait = int(resp.headers.get('Retry-After', 2 ** attempt))
                        await asyncio.sleep(wait)
                        continue

                    resp.raise_for_status()
                    return await resp.json()
            except aiohttp.ClientError as e:
                if attempt == retries - 1:
                    raise GitHubAPIError(str(e))
                await asyncio.sleep(2 ** attempt)

        raise RateLimitError("GitHub API rate limit exceeded")

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict[str, Any]:
        """Create a pull request."""
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        result = await self._api_call("POST", "/pulls", data)
        return {
            "number": result["number"],
            "url": result["html_url"],
            "state": result["state"],
        }

    async def get_pull_request(self, pr_number: int) -> dict[str, Any]:
        """Get PR details."""
        result = await self._api_call("GET", f"/pulls/{pr_number}")
        return {
            "number": result["number"],
            "state": result["state"],
            "status": result.get("mergeable_state", "unknown"),
        }

    async def add_comment(self, pr_number: int, body: str) -> dict[str, str]:
        """Add comment to PR."""
        data = {"body": body}
        result = await self._api_call(
            "POST", f"/issues/{pr_number}/comments", data
        )
        return {
            "id": str(result["id"]),
            "url": result["html_url"],
        }
```

**Environment Mapping:**
- `GITHUB_TOKEN`: Authentication header
- `GITHUB_REPOSITORY`: owner/repo for API base URL

### 2.4 StageContextPort Implementation (Artifact-Backed)

**File:** `ai_architect_mcp/_adapters/github_actions_impl.py` (ContextAdapterImpl)

```python
class ContextAdapterImpl(StageContextPort):
    """Stage context backed by local artifacts/ directory."""

    def __init__(self):
        self.workspace = Path(os.getenv('GITHUB_WORKSPACE', '.'))
        self.artifacts_dir = self.workspace / 'artifacts'

    async def save_artifact(
        self, stage_id: int, finding_id: str, artifact: dict[str, Any]
    ) -> None:
        """Save artifact as JSON file."""
        stage_dir = self.artifacts_dir / str(stage_id)
        stage_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = stage_dir / f"{finding_id}.json"
        content = json.dumps(artifact, indent=2, sort_keys=True)
        artifact_path.write_text(content)

    async def load_artifact(
        self, stage_id: int, finding_id: str
    ) -> dict[str, Any]:
        """Load artifact from JSON file."""
        artifact_path = self.artifacts_dir / str(stage_id) / f"{finding_id}.json"

        if not artifact_path.exists():
            raise FileNotFoundError(
                f"Artifact not found: stage {stage_id}, finding {finding_id}"
            )

        return json.loads(artifact_path.read_text())

    async def query_artifacts(
        self, finding_id: str, query: str
    ) -> list[dict[str, Any]]:
        """Query artifacts across stages."""
        results = []

        if not self.artifacts_dir.exists():
            return results

        for stage_dir in self.artifacts_dir.iterdir():
            if not stage_dir.is_dir():
                continue

            artifact_path = stage_dir / f"{finding_id}.json"
            if artifact_path.exists():
                artifact = json.loads(artifact_path.read_text())

                # Simple filtering: exact key match or regex value match
                if self._matches_query(artifact, query):
                    results.append({
                        'stage_id': int(stage_dir.name),
                        'finding_id': finding_id,
                        'artifact': artifact,
                    })

        return results

    def _matches_query(self, artifact: dict, query: str) -> bool:
        """Check if artifact matches query."""
        # Exact key match
        if query in artifact:
            return True

        # Regex value match
        try:
            pattern = re.compile(query)
            for value in artifact.values():
                if isinstance(value, str) and pattern.search(value):
                    return True
        except re.error:
            pass

        return False
```

**Environment Mapping:**
- `GITHUB_WORKSPACE`: artifacts/ directory location
- Uses GitHub Actions native artifact upload/download actions (in workflows)

### 2.5 XcodeOperationsPort Implementation (Headless Stub)

**File:** `ai_architect_mcp/_adapters/github_actions_impl.py` (XcodeAdapterImpl)

```python
class NotSupportedInGitHubActionsError(Exception):
    """Raised when Xcode operations are attempted in headless GitHub Actions."""

    def __init__(self):
        super().__init__(
            "Xcode operations not supported in headless GitHub Actions environment. "
            "Use macOS runner (macos-latest) for native Xcode builds."
        )


class XcodeAdapterImpl(XcodeOperationsPort):
    """Xcode operations stub for headless GitHub Actions."""

    async def build(
        self, scheme: str, configuration: str = "Debug"
    ) -> dict[str, Any]:
        """Build not supported in headless mode."""
        raise NotSupportedInGitHubActionsError()

    async def test(
        self, scheme: str, test_plan: str = None
    ) -> dict[str, Any]:
        """Test not supported in headless mode."""
        raise NotSupportedInGitHubActionsError()

    async def preview(self, view_name: str) -> bytes:
        """Preview not supported in headless mode."""
        raise NotSupportedInGitHubActionsError()
```

---

## 3. Entrypoint Script Design

**File:** `scripts/ci/entrypoint.py`

```python
#!/usr/bin/env python3
"""GitHub Actions entrypoint for AI Architect pipeline.

Reads GitHub Actions event payload, creates Finding, runs pipeline,
reports results via check runs API.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from ai_architect_mcp._adapters.github_actions_adapter import (
    GitHubActionsAdapter,
)
from ai_architect_mcp._adapters.github_actions_impl import (
    GitOpsAdapterImpl,
    FileSystemAdapterImpl,
    GitHubAdapterImpl,
    XcodeAdapterImpl,
    ContextAdapterImpl,
)
from ai_architect_mcp.models import Finding


async def main():
    """Main entrypoint function."""
    try:
        # 1. Parse GitHub Actions event
        event_path = os.getenv('GITHUB_EVENT_PATH')
        if not event_path:
            raise EnvironmentError("GITHUB_EVENT_PATH not set")

        with open(event_path) as f:
            event = json.load(f)

        print(f"GitHub Actions Event: {json.dumps(event, indent=2)}")

        # 2. Create Finding from event
        finding = _create_finding_from_event(event)
        print(f"Created Finding: {finding.finding_id}")

        # 3. Instantiate GitHubActionsAdapter
        adapter = GitHubActionsAdapter(
            git_ops=GitOpsAdapterImpl(),
            xcode_ops=XcodeAdapterImpl(),
            github_ops=GitHubAdapterImpl(),
            fs_ops=FileSystemAdapterImpl(),
            context_ops=ContextAdapterImpl(),
        )
        print("Initialized GitHubActionsAdapter")

        # 4. Create check run
        check_run_id = await _create_check_run(adapter, finding)
        print(f"Created check run: {check_run_id}")

        # 5. Run pipeline (TBD: stage logic)
        stage_outputs = await _run_pipeline(adapter, finding)
        print(f"Pipeline completed: {len(stage_outputs)} stages")

        # 6. Collect artifacts
        await _collect_artifacts(adapter, finding, stage_outputs)
        print("Artifacts collected")

        # 7. Update check run with results
        await _update_check_run(adapter, check_run_id, stage_outputs)
        print("Check run updated")

        print("Entrypoint completed successfully")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _create_finding_from_event(event: dict) -> Finding:
    """Create Finding from GitHub Actions event payload."""
    # Detect event type
    if "issue" in event:
        return Finding(
            issue_number=event["issue"]["number"],
            title=event["issue"]["title"],
            description=event["issue"]["body"],
            actor=event["sender"]["login"],
            timestamp=event["issue"]["created_at"],
        )
    elif "pull_request" in event:
        return Finding(
            pr_number=event["pull_request"]["number"],
            title=event["pull_request"]["title"],
            description=event["pull_request"]["body"],
            actor=event["sender"]["login"],
            timestamp=event["pull_request"]["created_at"],
        )
    elif "comment" in event:
        return Finding(
            comment_text=event["comment"]["body"],
            actor=event["sender"]["login"],
            timestamp=event["comment"]["created_at"],
        )
    else:
        raise ValueError(f"Unsupported GitHub event: {event.get('action')}")


async def _create_check_run(adapter, finding: Finding) -> int:
    """Create GitHub check run."""
    check_run = await adapter.github_ops._api_call(
        "POST",
        "/check-runs",
        {
            "name": "AI Architect - Finding Analysis",
            "head_sha": os.getenv('GITHUB_SHA'),
            "status": "in_progress",
        },
    )
    return check_run["id"]


async def _run_pipeline(adapter, finding: Finding) -> dict:
    """Run AI Architect pipeline (TBD: stage logic)."""
    # Placeholder: Return empty outputs
    return {}


async def _collect_artifacts(adapter, finding: Finding, outputs: dict) -> None:
    """Collect stage outputs as artifacts."""
    for stage_id, output in outputs.items():
        await adapter.context_ops.save_artifact(
            stage_id=stage_id,
            finding_id=finding.finding_id,
            artifact=output,
        )


async def _update_check_run(adapter, check_run_id: int, outputs: dict) -> None:
    """Update check run with final status."""
    summary = f"Completed {len(outputs)} stages"
    await adapter.github_ops._api_call(
        "PATCH",
        f"/check-runs/{check_run_id}",
        {
            "status": "completed",
            "conclusion": "success",
            "output": {
                "title": "AI Architect Analysis",
                "summary": summary,
            },
        },
    )


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

---

## 4. Workflow YAML Templates

### 4.1 Issue-Triggered Workflow

**File:** `.github/workflows/issue-triggered.yml`

```yaml
name: Issue Triggered - Architecture Analysis

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run architect analysis
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/ci/entrypoint.py

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: architecture-findings-${{ github.event.issue.number }}
          path: artifacts/
          retention-days: 90

      - name: Create PR with findings
        if: success()
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr create \
            --title "Architecture Analysis for Issue #${{ github.event.issue.number }}" \
            --body "Automated architecture findings from AI Architect." \
            --head "feature/issue-${{ github.event.issue.number }}-architecture" \
            --base main
```

### 4.2 Nightly Workflow

**File:** `.github/workflows/nightly.yml`

```yaml
name: Nightly Architecture Review

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch  # Allow manual trigger

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  nightly-review:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - {pr_limit: 5}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Get recent PRs
        id: pr-list
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr list \
            --state open \
            --order created \
            --limit ${{ matrix.pr_limit }} \
            --json number,title,createdAt \
            > prs.json

      - name: Analyze PRs
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          for pr_num in $(jq -r '.[].number' prs.json); do
            echo "Analyzing PR #$pr_num..."
            GITHUB_EVENT_PATH=/tmp/pr-event.json python scripts/ci/entrypoint.py
          done

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: nightly-review-results
          path: artifacts/
          retention-days: 30
```

### 4.3 PR-Comment-Triggered Workflow

**File:** `.github/workflows/pr-comment.yml`

```yaml
name: PR Comment - Re-analyze on @architect mention

on:
  issue_comment:
    types: [created, edited]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  comment-trigger:
    if: |
      github.event.issue.pull_request &&
      contains(github.event.comment.body, '@architect')

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ github.event.issue.number }}/head

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run architect analysis
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/ci/entrypoint.py

      - name: Post results as comment
        if: success()
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          FINDINGS=$(cat artifacts/*/finding_summary.json | jq -r '.summary')
          gh pr comment ${{ github.event.issue.number }} \
            --body "**AI Architect Re-analysis:**\n\n$FINDINGS"

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: comment-trigger-results-pr${{ github.event.issue.number }}
          path: artifacts/
          retention-days: 90
```

---

## 5. Artifact Storage & Multi-Job Integration

### 5.1 Artifact Directory Structure

```
GITHUB_WORKSPACE/
├── artifacts/
│   ├── 0/
│   │   ├── finding-20260314-001.json
│   │   └── finding-20260314-002.json
│   ├── 1/
│   │   ├── finding-20260314-001.json
│   │   └── ...
│   ├── 2/
│   │   └── finding-20260314-001.json
│   └── ...
├── .github/
├── src/
├── tests/
└── ...
```

### 5.2 Multi-Job Workflow Pattern

```yaml
jobs:
  architect-stage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/ci/entrypoint.py  # Runs architect stage only
      - uses: actions/upload-artifact@v3
        with:
          name: architect-findings
          path: artifacts/0/  # Only stage 0 artifacts

  downstream-stage:
    needs: architect-stage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v3
        with:
          name: architect-findings
          path: artifacts/0/  # Restore exact directory structure
      - run: python scripts/ci/run_downstream.py  # Load artifacts via ContextPort
```

---

## 6. Secret Injection Pattern

### 6.1 Environment Variable Injection

Secrets are passed as environment variables in workflows:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # GitHub Actions built-in
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}  # User-configured
```

In Python code (never logged):

```python
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    raise EnvironmentError("ANTHROPIC_API_KEY not set")

# Use api_key in API calls
# Never: print(api_key) or log(api_key)
```

### 6.2 Secret Configuration

Users must configure secrets in GitHub repo settings:
1. Go to Settings → Secrets and variables → Actions
2. Create `ANTHROPIC_API_KEY` secret
3. Value: Actual API key (hidden from logs)

---

## 7. Error Handling & Logging

### 7.1 Exception Hierarchy

```python
class AIArchitectError(Exception):
    """Base exception for all AI Architect errors."""
    pass

class GitError(AIArchitectError):
    """Git operation failed."""
    pass

class GitHubAPIError(AIArchitectError):
    """GitHub API call failed."""
    pass

class RateLimitError(AIArchitectError):
    """GitHub API rate limit exceeded."""
    pass

class EnvironmentError(AIArchitectError):
    """Required environment variable missing."""
    pass

class NotSupportedInGitHubActionsError(AIArchitectError):
    """Operation not supported in headless GitHub Actions."""
    pass
```

### 7.2 Logging Strategy

All logs go to stdout (captured by GitHub Actions):

```python
# Info: What's happening
print(f"Created branch: {branch_name}")

# Errors: What went wrong
print(f"Error: {e}", file=sys.stderr)

# Never log secrets
api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"Using API key: {api_key}")  # WRONG!
```

---

## 8. Performance Characteristics

### 8.1 Expected Timings

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Checkout code | 5-10s | GitHub caching |
| Install deps | 30-60s | pip install |
| Git operations (all 5) | <5s each | Local git CLI |
| GitHub API calls | 1-2s each | Network latency + backoff |
| Artifact upload (<100MB) | 2-5 min | GitHub Actions upload |
| Artifact download | 1-3 min | GitHub Actions download |
| Full pipeline (E2E) | <30 min | All stages + artifacts |

### 8.2 Optimization Strategies

1. **Dependency caching:** Cache pip packages with `actions/setup-python@v4`
2. **Artifact compression:** ZIP large artifacts before upload
3. **Parallel jobs:** Use matrix strategy for multiple PRs (nightly workflow)
4. **Rate limit avoidance:** Cache API responses within same run

---

## 9. Testing & Verification

### 9.1 Unit Testing Pattern

```python
# tests/test_gha_git_ops.py
import pytest
from unittest.mock import Mock, patch, AsyncMock

@pytest.fixture
def git_adapter():
    with patch.dict(os.environ, {'GITHUB_WORKSPACE': '/tmp/test'}):
        yield GitOpsAdapterImpl()

@pytest.mark.asyncio
async def test_create_branch(git_adapter, monkeypatch):
    # Mock git subprocess
    monkeypatch.setattr(
        git_adapter, '_run_git',
        AsyncMock(return_value=Mock(returncode=0, stdout='...'))
    )

    result = await git_adapter.create_branch('feature/test')
    assert result == 'refs/heads/feature/test'
```

### 9.2 Integration Testing Pattern

```python
# tests/test_gha_pipeline_e2e.py
@pytest.mark.asyncio
async def test_issue_to_pr_flow():
    # Set up GitHub Actions environment
    with patch.dict(os.environ, {
        'GITHUB_WORKSPACE': tmpdir,
        'GITHUB_TOKEN': 'fake-token',
        'GITHUB_REPOSITORY': 'owner/repo',
        'GITHUB_SHA': 'abc123...',
        'GITHUB_EVENT_PATH': event_file,
    }):
        # Create adapter
        adapter = GitHubActionsAdapter(...)

        # Simulate event
        event = {'issue': {'number': 1, 'title': 'Test'}, ...}
        finding = _create_finding_from_event(event)

        # Run entrypoint
        result = await main()

        # Verify artifacts created
        assert (tmpdir / 'artifacts' / '0' / finding.finding_id).exists()
```

---

## Dependencies Summary

### Python Packages
- `aiohttp`: Async HTTP client for GitHub API
- `requests`: Sync HTTP (fallback if needed)
- `pathlib`: File path handling (stdlib)
- `json`: JSON serialization (stdlib)
- `asyncio`: Async runtime (stdlib)

### External Tools
- `git`: Git version control (pre-installed on GitHub Actions runners)
- `gh`: GitHub CLI (pre-installed on GitHub Actions runners)
- Python 3.11+

