# PRD Technical Specification — AI Architect Missing Components

**Version:** 1.0.0
**Date:** 2026-03-14
**PRD Type:** Full Scope Overview (High-Level Architecture Only)

---

## 1. Architecture Overview

AI Architect follows a four-layer architecture (Skills / Tools / Reasoning / Data) with hexagonal ports/adapters pattern. All new components MUST comply with the existing architectural principles defined in ADR-001.

**Layer Rules (Inviolable):**
- **Skills** define WHAT (SKILL.md files — declarative contracts)
- **Tools** define HOW (Python MCP server — 32 tools, algorithms, adapters)
- **Claude** decides WHY (reasoning layer — strategy selection, retry logic)
- **Data** persists WHAT HAPPENED (context memory, audit trail, experience patterns)

**Dependency Direction:** Skills → Tools → Domain ← Adapters. Domain has ZERO outward dependencies.

---

## 2. Epic 1: Plan Interview Stage — Architecture

### 2.1 Module Structure

```
mcp/ai_architect_mcp/_interview/
├── __init__.py
├── dimensions.py          # 10 dimension definitions (pure domain)
├── scorer.py              # Scoring engine (pure domain)
├── interview_engine.py    # Orchestration (uses ports only)
└── models.py              # InterviewResult, DimensionScore (Pydantic v2)

skills/stage-4.5-plan-interview/
└── SKILL.md               # Survival Architecture v3.0 template

mcp/ai_architect_mcp/_tools/
└── interview_tools.py     # 2 new MCP tools
```

### 2.2 Domain Layer (Ports)

```python
# Domain — Pure business logic, zero framework imports

class DimensionPort(Protocol):
    """Port for evaluating a single interview dimension."""
    async def evaluate(
        self, prd_context: StageContext, dimension: DimensionType
    ) -> DimensionScore: ...

class InterviewGatePort(Protocol):
    """Port for the interview gate decision."""
    async def should_proceed(
        self, scores: list[DimensionScore], thresholds: dict[DimensionType, float]
    ) -> GateDecision: ...
```

### 2.3 10 Dimensions

| Dimension | Pass Threshold | What It Evaluates |
|-----------|---------------|-------------------|
| Technical Feasibility | 0.7 | Can this be built with available technology? |
| UI/UX Design | 0.6 | Is the user experience well-defined? |
| Risk Assessment | 0.7 | Are risks identified and mitigated? |
| Tradeoff Analysis | 0.6 | Are alternatives considered with reasoning? |
| Edge Cases | 0.7 | Are boundary conditions addressed? |
| Dependency Mapping | 0.8 | Are all dependencies identified? |
| Test Strategy | 0.7 | Is the testing approach comprehensive? |
| Deployment Planning | 0.6 | Is deployment strategy defined? |
| Gap Detection | 0.8 | Are there unaddressed requirements? |
| Security Review | 0.8 | Are security implications assessed? |

---

## 3. Epic 2: Four-Layer Memory Model — Architecture

### 3.1 Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT MEMORY                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Session  │  │ Project  │  │Experience│  │Analytics │  │
│  │  Layer   │  │  Layer   │  │  Layer   │  │  Layer   │  │
│  │          │  │          │  │          │  │          │  │
│  │Pipeline  │  │Finding + │  │Patterns  │  │AuditEvent│  │
│  │State     │  │StageOut  │  │+ Decay   │  │(immutable│  │
│  │          │  │          │  │          │  │          │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┘        │
│                          │                                   │
│                   ┌──────┴──────┐                            │
│                   │  CloudKit   │                            │
│                   │   Sync      │                            │
│                   └─────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Domain Models (Pydantic v2)

```python
# Domain — Zero framework imports

class PipelineState(BaseModel):
    """Session layer: current pipeline execution state."""
    run_id: str
    current_stage: int  # 0-10
    active_finding_id: str
    agent_id: str
    skill_versions: dict[str, str]  # stage_name -> version
    started_at: str  # ISO 8601
    last_updated_at: str  # ISO 8601
    status: PipelineStatus  # RUNNING, PAUSED, COMPLETED, FAILED

class ExperiencePattern(BaseModel):
    """Experience layer: learned patterns with biological decay."""
    pattern_id: str
    pattern_type: PatternType
    description: str
    initial_relevance: float  # 0.0-1.0
    half_life_days: float  # configurable per type
    created_at: str  # ISO 8601
    last_accessed_at: str  # ISO 8601

    def current_relevance(self, now_iso: str) -> float:
        """Biological decay: relevance = initial × 0.5^(elapsed / half_life)"""
        # Pure computation, no framework imports
        ...

class AuditEvent(BaseModel):
    """Analytics layer: immutable audit trail entry."""
    event_id: str
    who: str  # agent_id
    what: str  # action description
    when: str  # ISO 8601 timestamp
    where: str  # stage name or component
    outcome: AuditOutcome  # SUCCESS, FAILURE, SKIPPED
    metadata: dict[str, str]  # additional context
```

### 3.3 New Ports

```python
class PipelineStatePort(Protocol):
    async def load(self, run_id: str) -> PipelineState | None: ...
    async def save(self, state: PipelineState) -> None: ...
    async def sync(self) -> SyncResult: ...

class ExperiencePort(Protocol):
    async def store(self, pattern: ExperiencePattern) -> None: ...
    async def query(self, pattern_type: PatternType, min_relevance: float) -> list[ExperiencePattern]: ...
    async def reinforce(self, pattern_id: str) -> None: ...

class AuditPort(Protocol):
    async def append(self, event: AuditEvent) -> None: ...
    async def query(self, filters: AuditQuery) -> list[AuditEvent]: ...
    # No update() or delete() — immutable by design
```

### 3.4 Progressive Disclosure

| Level | Token Budget | When Loaded | Content |
|-------|-------------|-------------|---------|
| L1 Config | ~500 tokens | Always (session start) | Pipeline config, active finding summary, skill versions |
| L2 Summary | ~300 tokens | On stage match | Stage-specific summary, key decisions, blockers |
| L3 Full | ~3,000 tokens | On demand | Full documentation, code examples, decision rationale |

**Budget Monitor Thresholds:**
- 70% context usage → Switch from L3 to L2 for all non-active stages
- 93% context usage → Auto-generate HandoffDocument, offer session save

---

## 4. Epic 3: Consensus Algorithms — Architecture

### 4.1 Bayesian Consensus

```python
# Pure domain algorithm, no framework imports

class BayesianConsensus:
    """
    Bayesian posterior aggregation with Beta prior.

    Given judge scores [0,1] and a Beta(α, β) prior:
    1. Convert scores to binary (above/below threshold)
    2. Update posterior: α' = α + successes, β' = β + failures
    3. Posterior mean = α' / (α' + β')
    4. Credible interval from Beta distribution
    """
    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta

    def compute(self, scores: list[float], threshold: float = 0.5) -> ConsensusResult:
        ...
```

### 4.2 Majority Voting

```python
class MajorityVoting:
    """
    Simple threshold-based majority agreement.

    1. Count votes above/below threshold
    2. Majority = side with more votes
    3. Tie-breaking: configurable (highest_confidence, escalate_to_debate)
    """
    def __init__(self, threshold: float = 0.5, tie_breaker: TieBreaker = TieBreaker.HIGHEST_CONFIDENCE):
        self.threshold = threshold
        self.tie_breaker = tie_breaker

    def compute(self, scores: list[float]) -> ConsensusResult:
        ...
```

---

## 5. Epic 4: Hook System — Architecture

### 5.1 Hook Dispatch Model

```
Session Lifecycle:
  SessionStart → [stage loop: PreToolUse → Tool → PostToolUse] → SessionEnd

Hook Types:
  ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
  │   Session Hooks  │     │  PreToolUse Hooks │     │ PostToolUse Hooks│
  │                  │     │                   │     │                  │
  │ session-start.sh │     │ enforce-doc-read  │     │ validate-schema  │
  │ save-summary.sh  │     │ security-tier     │     │ update-state     │
  └─────────────────┘     └──────────────────┘     └─────────────────┘
```

### 5.2 Security Tier Model (10 Tiers)

| Tier | Risk Level | Examples | Action |
|------|-----------|----------|--------|
| 1 | None | `git status`, `ls`, `cat` | Allow |
| 2 | Minimal | `git log`, `grep`, `find` | Allow |
| 3 | Low | `git diff`, `python -c "..."` | Allow |
| 4 | Moderate | `git commit`, `pip install` | Allow + log |
| 5 | Elevated | `git push`, `npm publish` | Allow + log + confirm |
| 6 | High | `docker run`, `curl | bash` | Block + ask user |
| 7 | Very High | `chmod 777`, `chown` | Block + ask user |
| 8 | Critical | `rm -rf`, `git reset --hard` | Block unconditionally |
| 9 | Severe | System file modification | Block unconditionally |
| 10 | Catastrophic | `rm -rf /`, disk wipe patterns | Block unconditionally |

---

## 6. Epic 5: GitHub Actions — Architecture

### 6.1 Adapter Pattern

```python
# Adapter implementing existing ports for GitHub Actions context

class GitHubActionsAdapter:
    """
    Implements all 5 port interfaces for headless CI/CD execution.
    Uses GITHUB_TOKEN and ANTHROPIC_API_KEY from Actions secrets.
    """

    class GitOps(GitOperationsPort):
        """Git operations using checkout action's git binary."""
        ...

    class XcodeOps(XcodeOperationsPort):
        """Xcode operations via macos-latest runner (when available)."""
        ...

    class GitHubOps(GitHubOperationsPort):
        """GitHub API operations using octokit from GITHUB_TOKEN."""
        ...

    class FileSystemOps(FileSystemPort):
        """Filesystem operations within GITHUB_WORKSPACE."""
        ...

    class ContextOps(StageContextPort):
        """Context stored as GitHub Actions artifacts between stages."""
        ...
```

### 6.2 Workflow Templates

Three workflow YAML files:
1. `ai-architect-pipeline.yml` — Issue-triggered (label: `ai-architect`)
2. `ai-architect-nightly.yml` — Schedule-triggered (configurable cron)
3. `ai-architect-pr-review.yml` — PR comment-triggered (`/ai-architect run`)

---

## 7. Epic 6: Python Package — Architecture

### 7.1 Package Structure

```
ai-architect-mcp/
├── pyproject.toml           # PyPI metadata, dependencies
├── ai_architect_mcp/
│   ├── __init__.py          # Version, public API
│   ├── __main__.py          # CLI: `python -m ai_architect_mcp` or `ai-architect-mcp serve`
│   ├── _config/
│   │   ├── loader.py        # TOML config + env var override
│   │   └── defaults.toml    # Default configuration
│   ├── server.py            # FastMCP entry (existing)
│   ├── _adapters/           # (existing)
│   ├── _models/             # (existing + new from Epic 2)
│   ├── _verification/       # (existing + new from Epic 3)
│   ├── _prompting/          # (existing)
│   ├── _context/            # (existing + new from Epic 2)
│   ├── _interview/          # (new from Epic 1)
│   ├── _scoring/            # (existing)
│   └── _tools/              # (existing + new from Epics 1, 4)
└── tests/                   # (existing 42 files + new)
```

### 7.2 CLI Entry Point

```python
# __main__.py
import click

@click.group()
def cli():
    """AI Architect MCP Server"""

@cli.command()
@click.option("--port", default=8080, help="Server port")
@click.option("--config", default="ai-architect.toml", help="Config file path")
def serve(port: int, config: str):
    """Start the FastMCP server."""
    ...

@cli.command()
def version():
    """Show version information."""
    ...
```

---

## 8. Survival Architecture v3.0 Template (ADR-009)

### New Sections Added to v2.2

```markdown
## Hook Declarations (NEW in v3.0)
### PreToolUse Hooks
- enforce-doc-read: MANDATORY
- security-tier-check: tier <= 5 for this stage

### PostToolUse Hooks
- validate-output-schema: {output_contract_reference}
- update-pipeline-state: stage completion event

## Context Budget (NEW in v3.0)
- L1 Config: {what's always loaded}
- L2 Summary: {what's loaded on match}
- L3 Full: {what's loaded on demand}
- Budget threshold: {stage-specific token limit}

## Security Tier (NEW in v3.0)
- Maximum allowed tier: {1-10}
- Justification: {why this tier is appropriate}
```

### Backward Compatibility

All v2.2 SKILL.md files are valid under v3.0. New sections default to:
- Hook Declarations: empty (no hooks enforced)
- Context Budget: unlimited (L3 always loaded)
- Security Tier: 5 (moderate, default safe)

---

## 9. Cross-Epic Integration Points

| From | To | Integration | Contract |
|------|----|-------------|----------|
| Epic 1 (Interview) | Orchestrator | Stage ordering (4 → 4.5 → 5) | StageContextPort |
| Epic 2 (Memory) | Epic 4 (Hooks) | AuditEvent model for update-pipeline-state hook | AuditPort |
| Epic 2 (Memory) | Epic 1 (Interview) | PipelineState tracks interview results | PipelineStatePort |
| Epic 4 (Hooks) | Epic 5 (GHA) | Hooks must work in headless mode | Hook dispatch interface |
| Epic 4 (Hooks) | All stages | v3.0 template adoption | SKILL.md format |
| Epics 1–4 | Epic 6 (Python) | All new code packaged in PyPI | Package includes |

---

## 10. Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| MCP Server | FastMCP (Python) | Latest | Existing choice, pip-installable |
| Domain Models | Pydantic v2 | ≥ 2.0 | Existing choice, type-safe validation |
| Persistence | SwiftData + CloudKit | macOS 26+ | Apple-native, iCloud sync |
| Testing | pytest + pytest-asyncio | Latest | Existing choice |
| Linting | ruff | Latest | Existing choice |
| Type Checking | mypy (strict) | Latest | Existing choice |
| CI/CD | GitHub Actions | Latest | Target for Epic 5 |
| Packaging | Hatchling | Latest | Existing build system |

**HUMAN REVIEW REQUIRED**
- **Section:** CloudKit sync architecture (Epic 2)
- **Reason:** CloudKit conflict resolution strategy needs validation with real multi-device testing
- **Reviewer:** Clément (prototype in Sprint 0)
- **Before:** Epic 2 Sprint 1 kickoff
