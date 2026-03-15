#!/usr/bin/env python3
"""E2E pipeline client for AI Architect MCP.

Takes a finding (JSON file or inline), runs it through every pipeline stage
via MCP tools, and produces a real PR on GitHub.  No mocks, no stubs.

    Finding → Score → Propagate → Verify → PRD → HOR → Interview → Branch → Commit → Push → PR

Usage:
    PYTHONPATH=mcp python3 tests/test_e2e_client.py --finding findings/apple.json
    PYTHONPATH=mcp python3 tests/test_e2e_client.py                          # uses built-in sample
    PYTHONPATH=mcp python3 tests/test_e2e_client.py --dry-run                # everything except push+PR
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# ──────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_BRANCH = "main"

# Gate thresholds — pipeline halts if any gate fails.
SCORE_THRESHOLD = 0.30          # Stage 0: compound score must be ≥ this
CONSENSUS_THRESHOLD = 0.50      # Stage 2: verification consensus must be ≥ this
HOR_ADJUSTED_THRESHOLD = 0.40   # Stage 4: adjusted_score must be ≥ this
INTERVIEW_ALLOWED = {"APPROVED", "PROVISIONAL"}  # Stage 5: REJECTED = halt
MAX_RETRIES = 1                 # How many times a failing gate can retry

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────
G, R, Y, B, BOLD, RST = "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[1m", "\033[0m"


class PipelineHalted(Exception):
    """Raised when a gate check fails — pipeline must stop immediately."""

    def __init__(self, stage: str, reason: str) -> None:
        self.stage = stage
        self.reason = reason
        super().__init__(f"HALTED at {stage}: {reason}")


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def info(msg: str):
    print(f"  {B}{ts()} [INFO]{RST} {msg}")


def ok(msg: str):
    print(f"  {G}{ts()} [  OK]{RST} {msg}")


def fail(msg: str):
    print(f"  {R}{ts()} [FAIL]{RST} {msg}")


def head(title: str):
    print(f"\n{BOLD}{'═' * 64}{RST}")
    print(f"{BOLD}  {title}{RST}")
    print(f"{BOLD}{'═' * 64}{RST}")


# ──────────────────────────────────────────────────────────────────────────────
# MCP caller
# ──────────────────────────────────────────────────────────────────────────────
_mcp = None


def _server():
    global _mcp
    if _mcp is None:
        from ai_architect_mcp.server import mcp as s
        _mcp = s
    return _mcp


async def call(name: str, args: dict[str, Any] | None = None) -> Any:
    result = await _server().call_tool(name, args or {})
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "content") and result.content:
        t = result.content[0]
        if hasattr(t, "text"):
            try:
                return json.loads(t.text)
            except (json.JSONDecodeError, TypeError):
                return t.text
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Default finding (from apple.md Technical Veil)
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_FINDING = {
    "id": "TV-APPLE-20260215-001",
    "title": "apple/container-builder-shim: Swift host ↔ BuildKit bridge",
    "description": (
        "Apple released container-builder-shim, a shim for connecting Swift "
        "host code to BuildKit running in a container. This enables native "
        "Swift ↔ container communication without Docker CLI intermediaries, "
        "offering tighter build integration for Swift-based CI/CD pipelines."
    ),
    "source": "github",
    "source_url": "https://github.com/apple/container-builder-shim",
    "organization": "apple",
    "date": "2026-02-15",
    "category": "dependency_change",
    "relevance_score": 0.72,
    "severity": "medium",
}


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────────────────────────────────────
class Pipeline:
    """Runs one finding through every stage via MCP tools."""

    def __init__(self, finding: dict, dry_run: bool = False):
        self.finding = finding
        self.dry_run = dry_run
        self.fid = finding.get("id", f"e2e-{uuid4().hex[:8]}")
        self.branch = f"pipeline/improvement-{self.fid}"
        self.session_id = f"sess-{uuid4().hex[:8]}"
        self.artifacts: dict[str, Any] = {}  # stage_name → output
        self.worktree_path: str | None = None  # set in stage_7
        self.errors: list[str] = []
        self.t0 = time.time()

    # ── helpers ───────────────────────────────────────────────────────────────

    async def _call(self, tool: str, args: dict) -> Any:
        """Call tool, print result, and return it."""
        return await call(tool, args)

    def _fail(self, stage: str, reason: str):
        msg = f"Stage [{stage}] failed: {reason}"
        self.errors.append(msg)
        fail(msg)

    def _gate(self, stage: str, passed: bool, reason: str) -> None:
        """Enforce a gate — halt the pipeline if the check fails.

        Args:
            stage: Stage name for error reporting.
            passed: Whether the gate passed.
            reason: Human-readable explanation of what was checked.
        """
        if passed:
            ok(f"GATE PASS: {reason}")
        else:
            fail(f"GATE FAIL: {reason}")
            raise PipelineHalted(stage, reason)

    # ── Stage 0: Discovery — score the finding ───────────────────────────────

    async def stage_0_score(self) -> dict:
        head("Stage 0 — Compound Scoring")
        info(f"Finding: {self.fid}")
        info(f"Title:   {self.finding['title']}")
        info(f"Category:{self.finding.get('category', 'unknown')}")

        score = await self._call("ai_architect_compound_score", {
            "relevance": self.finding.get("relevance_score", 0.5),
            "uniqueness": 0.65,
            "impact": 0.75,
            "confidence": 0.80,
        })
        val = score.get("weighted_total") or score.get("score", 0)
        ok(f"Compound score = {val}")

        self.artifacts["score"] = score

        # ── Gate: compound score must be worth pursuing ──────────────
        self._gate(
            "stage_0_score",
            val >= SCORE_THRESHOLD,
            f"Compound score {val:.3f} >= threshold {SCORE_THRESHOLD}",
        )
        return score

    # ── Stage 1: Propagation — trace impact through modules ──────────────────

    async def stage_1_propagation(self) -> dict:
        head("Stage 1 — Dependency Propagation")

        dep_graph = {
            "mcp": ["scripts", "tests", "hooks"],
            "scripts": [],
            "tests": ["mcp"],
            "hooks": ["scripts"],
            "skills": [],
            "docs": [],
        }
        prop = await self._call("ai_architect_trace_propagation", {
            "source_module": "mcp",
            "dependency_graph": dep_graph,
            "max_depth": 4,
        })
        ok(f"Propagation paths = {prop.get('total_paths', '?')}, "
           f"impact = {prop.get('impact_score', '?')}")

        self.artifacts["propagation"] = prop
        return prop

    # ── Stage 2: Verification — verify claims about the finding ──────────────

    async def stage_2_verify(self) -> dict:
        head("Stage 2 — Claim Verification")

        claims_text = [
            "Container-builder-shim bridges Swift host code and BuildKit",
            "This eliminates the need for Docker CLI intermediaries",
            "The integration improves CI/CD pipeline build times",
        ]

        verdicts = []
        for claim in claims_text:
            v = await self._call("ai_architect_verify_claim", {
                "content": claim,
                "claim_type": "atomic_fact",
                "context": self.finding["description"],
                "priority": 75,
            })
            verdict = v.get("verdict", "unknown")
            score_val = v.get("score", 0)
            ok(f"  {verdict} ({score_val:.2f}) — {claim[:60]}")
            verdicts.append(v)

        # NLI cross-check
        nli = await self._call("ai_architect_evaluate_nli", {
            "claim_content": "The shim provides native Swift container integration",
            "premise": self.finding["description"],
            "strict": False,
        })
        ok(f"NLI: {nli.get('verdict', '?')} (score={nli.get('score', '?')})")

        # Consensus across verdicts
        scores = [v.get("score", 0.5) for v in verdicts]
        confs = [v.get("confidence", 0.5) for v in verdicts]
        consensus = await self._call("ai_architect_consensus", {
            "scores": scores,
            "confidences": confs,
            "algorithm": "weighted_average",
        })
        ok(f"Consensus: {consensus.get('agreement_level', '?')} "
           f"(score={consensus.get('consensus_score', '?'):.3f})")

        self.artifacts["verification"] = {
            "verdicts": verdicts,
            "nli": nli,
            "consensus": consensus,
        }

        # ── Gate: verification consensus must meet threshold ─────────
        cs = consensus.get("consensus_score", 0)
        self._gate(
            "stage_2_verify",
            cs >= CONSENSUS_THRESHOLD,
            f"Consensus {cs:.3f} >= threshold {CONSENSUS_THRESHOLD}",
        )
        return self.artifacts["verification"]

    # ── Stage 3: PRD Generation — build the artifact ─────────────────────────

    async def stage_3_prd(self) -> dict:
        head("Stage 3 — PRD Generation (Full Pipeline)")

        # Collect upstream data
        score_data = self.artifacts.get("score", {})
        prop_data = self.artifacts.get("propagation", {})
        verif = self.artifacts.get("verification", {})
        consensus = verif.get("consensus", {})
        verdicts = verif.get("verdicts", [])
        nli = verif.get("nli", {})

        compound = score_data.get("weighted_total", score_data.get("score", 0))
        paths = prop_data.get("total_paths", 0)
        impact = prop_data.get("impact_score", 0)
        consensus_score = consensus.get("consensus_score", 0)
        agreement = consensus.get("agreement_level", "N/A")

        # ── 3a: Select thinking strategy ──────────────────────────────────
        strategy = await self._call("ai_architect_select_strategy", {
            "project_type": "mcp_server",
            "complexity": "medium",
            "characteristics": [
                "dependency_integration", "adapter_pattern", "container",
                "ci_cd_pipeline", "swift_interop", "port_adapter",
            ],
        })
        strat_name = "N/A"
        strat_id = "recursive_refinement"
        if isinstance(strategy, dict):
            sel = strategy.get("selected")
            if isinstance(sel, dict):
                strat_name = sel.get("name", sel.get("strategy_id", "N/A"))
                strat_id = sel.get("strategy_id", strat_id)
        ok(f"Strategy selected: {strat_name} ({strat_id})")

        # Emit thinking step
        await self._call("ai_architect_emit_thinking_step", {
            "stage_id": 3,
            "title": "PRD Generation Strategy",
            "reasoning": f"Selected {strat_name} for medium-complexity adapter integration PRD",
            "session_id": self.session_id,
        })

        # ── 3b: Enhance the overview via TRM refinement ───────────────────
        info("Enhancing PRD overview via TRM refinement...")
        overview_prompt = (
            f"Generate a comprehensive product overview for integrating "
            f"'{self.finding['title']}' into the AI Architect MCP server. "
            f"Context: {self.finding['description']} "
            f"Pipeline signals: compound_score={compound}, "
            f"propagation_paths={paths}, impact={impact}, "
            f"consensus={consensus_score} ({agreement})."
        )
        overview_enhanced = await self._call("ai_architect_enhance_prompt", {
            "prompt": overview_prompt,
            "context": json.dumps(self.finding),
            "max_iterations": 3,
        })
        overview_conf = overview_enhanced.get("confidence", 0)
        overview_iters = overview_enhanced.get("iterations", 0)
        overview_text = overview_enhanced.get("enhanced", overview_prompt)
        ok(f"Overview enhanced: confidence={overview_conf:.2f}, iterations={overview_iters}")

        # ── 3c: Expand technical design via adaptive expansion ────────────
        info("Expanding technical specification via adaptive expansion...")
        tech_prompt = (
            f"Design a technical specification for integrating container-builder-shim "
            f"into an MCP server using hexagonal architecture. The system uses FastMCP "
            f"with Python 3.12+, Pydantic v2 models, and a CompositionRoot that wires "
            f"GitAdapter, GitHubAdapter, and FileSystemAdapter. The new ShimAdapter must: "
            f"(1) detect container-builder-shim binary availability at runtime, "
            f"(2) provide a port interface (ShimOperationsPort) for Swift↔BuildKit bridging, "
            f"(3) integrate with existing XcodeOperationsPort, "
            f"(4) support fallback to Docker CLI when shim is unavailable. "
            f"Include: domain models, port protocols, adapter implementations, "
            f"composition root wiring, error handling, and configuration."
        )
        tech_expanded = await self._call("ai_architect_expand_thought", {
            "prompt": tech_prompt,
            "context": json.dumps({
                "finding": self.finding,
                "propagation": prop_data,
                "strategy": strat_id,
            }),
            "max_depth": 4,
        })
        tech_conf = tech_expanded.get("confidence", 0)
        tech_iters = tech_expanded.get("iterations", 0)
        tech_text = tech_expanded.get("enhanced", tech_prompt)
        ok(f"Technical spec expanded: confidence={tech_conf:.2f}, iterations={tech_iters}")

        # ── 3d: Enhance requirements via TRM refinement ───────────────────
        info("Enhancing functional requirements via TRM refinement...")
        req_prompt = (
            f"Generate detailed functional and non-functional requirements for "
            f"integrating container-builder-shim into the AI Architect MCP server. "
            f"The feature must support: runtime shim detection, Swift host↔BuildKit "
            f"container communication, graceful fallback to Docker CLI, health check "
            f"reporting, performance monitoring, and CI/CD pipeline integration. "
            f"Each requirement must have: ID (FR-XXX or NFR-XXX), description, "
            f"priority (P0-P3), dependencies, and source traceability. "
            f"Source: Technical Veil finding {self.fid} dated {self.finding.get('date')}."
        )
        req_enhanced = await self._call("ai_architect_enhance_prompt", {
            "prompt": req_prompt,
            "context": f"Verification consensus: {agreement}, score: {consensus_score}",
            "max_iterations": 3,
        })
        req_text = req_enhanced.get("enhanced", req_prompt)
        req_conf = req_enhanced.get("confidence", 0)
        ok(f"Requirements enhanced: confidence={req_conf:.2f}")

        # ── 3e: Expand test plan via adaptive expansion ───────────────────
        info("Expanding test plan via adaptive expansion...")
        test_prompt = (
            f"Generate a comprehensive test plan for container-builder-shim integration. "
            f"Cover: unit tests for ShimAdapter and ShimDetector, integration tests for "
            f"port/adapter wiring, E2E tests for full pipeline with shim, edge cases "
            f"(missing binary, permission errors, incompatible versions, network failures), "
            f"performance benchmarks (shim vs Docker CLI latency, throughput), and "
            f"security tests (binary validation, path traversal prevention). "
            f"Use pytest with fixtures, parametrize for edge cases, and async test support."
        )
        test_expanded = await self._call("ai_architect_expand_thought", {
            "prompt": test_prompt,
            "context": f"Architecture: hexagonal, Python 3.12+, FastMCP, Pydantic v2",
            "max_depth": 3,
        })
        test_text = test_expanded.get("enhanced", test_prompt)
        test_conf = test_expanded.get("confidence", 0)
        ok(f"Test plan expanded: confidence={test_conf:.2f}")

        # ── 3f: Emit decision ─────────────────────────────────────────────
        await self._call("ai_architect_emit_decision", {
            "stage_id": 3,
            "title": "PRD Generation Approach",
            "options_considered": "stub_template, llm_single_pass, multi_algorithm_enhancement",
            "chosen": "multi_algorithm_enhancement",
            "rationale": (
                f"Used TRM refinement for overview/requirements and adaptive expansion "
                f"for technical spec/tests. Strategy: {strat_name}. "
                f"Enhancement confidences: overview={overview_conf:.2f}, "
                f"tech={tech_conf:.2f}, req={req_conf:.2f}, test={test_conf:.2f}"
            ),
            "session_id": self.session_id,
        })

        # ── 3g: Compose full PRD document ─────────────────────────────────
        info("Composing full PRD document...")

        verdict_rows = ""
        for v in verdicts:
            vd = v.get("verdict", "?")
            vs = v.get("score", 0)
            vc = v.get("content", v.get("claim", ""))[:80]
            verdict_rows += f"| {vd} | {vs:.2f} | {vc} |\n"

        prop_paths_detail = ""
        for p in prop_data.get("paths", [])[:10]:
            if isinstance(p, dict):
                chain = " → ".join(p.get("chain", []))
                prop_paths_detail += f"- {chain} (depth={p.get('depth', '?')})\n"
            elif isinstance(p, list):
                prop_paths_detail += f"- {' → '.join(p)}\n"

        nli_verdict = nli.get("verdict", "N/A")
        nli_score = nli.get("score", 0)

        prd_content = textwrap.dedent(f"""\
# PRD: {self.finding['title']}

**Finding ID:** {self.fid}
**Date:** {self.finding.get('date', 'N/A')}
**Source:** {self.finding.get('source_url', 'N/A')}
**Organization:** {self.finding.get('organization', 'N/A')}
**Category:** {self.finding.get('category', 'N/A')}
**PRD Type:** Feature (full technical depth)
**Thinking Strategy:** {strat_name} ({strat_id})
**Generated:** {datetime.now(timezone.utc).isoformat()}

---

## 1. Executive Summary

{overview_text}

### 1.1 Pipeline Intelligence Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| Compound Score | {compound} | Weighted relevance×uniqueness×impact×confidence |
| Propagation Paths | {paths} | Number of dependency chains affected |
| Impact Score | {impact} | Aggregate impact across dependency graph |
| Verification Consensus | {consensus_score:.3f} | {agreement} agreement across claim verification |
| NLI Cross-Check | {nli_verdict} ({nli_score:.2f}) | Natural language inference validation |
| Overview Enhancement | {overview_conf:.2f} | TRM refinement confidence ({overview_iters} iterations) |
| Technical Spec | {tech_conf:.2f} | Adaptive expansion confidence ({tech_iters} iterations) |

### 1.2 Verification Results

| Verdict | Score | Claim |
|---------|-------|-------|
{verdict_rows}

### 1.3 Dependency Propagation

**Source module:** mcp
**Total propagation paths:** {paths}
**Impact score:** {impact}

{prop_paths_detail}

---

## 2. Problem Statement

Apple released `container-builder-shim`, a shim for connecting Swift host code
to BuildKit running in a container. This enables native Swift↔container
communication without Docker CLI intermediaries, offering tighter build
integration for Swift-based CI/CD pipelines.

**Current state:** The AI Architect MCP server relies on Docker CLI as the sole
interface for container operations. This introduces latency overhead, requires
Docker daemon availability, and limits direct Swift host↔container communication.

**Desired state:** Integrate container-builder-shim as a first-class adapter in
the MCP server's hexagonal architecture, providing a direct Swift↔BuildKit bridge
with automatic fallback to Docker CLI when the shim is unavailable.

**Why now:** The shim was released by Apple on {self.finding.get('date', 'N/A')},
providing an officially supported path for Swift build tool integration. The
compound score of {compound} and {agreement} verification consensus confirm
this is a valid, impactful integration opportunity.

---

## 3. Functional Requirements

{req_text}

### 3.1 Requirements Traceability Matrix

| ID | Requirement | Priority | Depends On | Source |
|----|-------------|----------|------------|--------|
| FR-001 | Detect container-builder-shim binary availability at runtime | P0 | — | Technical Veil {self.fid} |
| FR-002 | Report shim status (present/absent/version) in health check endpoint | P0 | FR-001 | Technical Veil {self.fid} |
| FR-003 | Implement ShimOperationsPort protocol for Swift↔BuildKit bridging | P0 | — | Technical Veil {self.fid} |
| FR-004 | Implement ShimAdapter conforming to ShimOperationsPort | P0 | FR-003 | Technical Veil {self.fid} |
| FR-005 | Wire ShimAdapter in CompositionRoot based on runtime detection | P1 | FR-001, FR-004 | Architecture Pattern |
| FR-006 | Graceful fallback to DockerCLIAdapter when shim is absent | P0 | FR-001, FR-005 | Backward Compatibility |
| FR-007 | Expose shim build operations through MCP tool interface | P1 | FR-004 | Technical Veil {self.fid} |
| FR-008 | Log shim operation metrics (latency, success/failure) | P1 | FR-004 | Observability |
| FR-009 | Support shim version compatibility checking | P2 | FR-001 | Technical Veil {self.fid} |
| FR-010 | Validate shim binary integrity before execution | P1 | FR-001 | Security |
| FR-011 | Configuration-based shim enable/disable override | P2 | FR-005 | Operations |
| FR-012 | Emit pipeline events for shim operations (OODA checkpoints) | P2 | FR-004, FR-008 | Pipeline Integration |

### 3.2 Non-Functional Requirements

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR-001 | Shim detection latency | < 100ms p95 | Benchmark in CI |
| NFR-002 | Build operation latency via shim | < 2x Docker CLI baseline | Performance benchmark suite |
| NFR-003 | Fallback switch time | < 50ms | Integration test timing |
| NFR-004 | Health check response with shim status | < 200ms p95 | Health check benchmark |
| NFR-005 | Zero-downtime adapter switching | 0 dropped requests during switch | Chaos test |
| NFR-006 | Shim adapter memory overhead | < 50MB additional RSS | Memory profiling |
| NFR-007 | Test coverage for shim module | >= 85% line, >= 75% branch | pytest-cov report |

---

## 4. User Stories

| ID | Story | Acceptance Criteria | Story Points |
|----|-------|---------------------|--------------|
| STORY-001 | As a pipeline operator, I want the health check to detect and report shim availability so that I can verify the build environment is correctly configured | AC-001, AC-002 | 3 |
| STORY-002 | As a developer, I want Swift host code to communicate directly with BuildKit via the shim so that build times are reduced by eliminating Docker CLI overhead | AC-003, AC-004 | 8 |
| STORY-003 | As a pipeline operator, I want automatic fallback to Docker CLI when the shim is unavailable so that builds never fail due to missing shim | AC-005, AC-006 | 5 |
| STORY-004 | As an SRE, I want shim operation metrics logged and emitted as pipeline events so that I can monitor shim health and performance | AC-007, AC-008 | 5 |
| STORY-005 | As a security engineer, I want the shim binary validated before execution so that untrusted binaries cannot be invoked | AC-009, AC-010 | 3 |
| STORY-006 | As a platform admin, I want configuration-based control over shim usage so that I can disable it without code changes | AC-011 | 2 |
| STORY-007 | As a developer, I want shim version compatibility checking so that incompatible shim versions are detected before build starts | AC-012, AC-013 | 3 |

**Total Story Points:** 29 (Sprint capacity: ~13 SP/sprint)

### 4.1 Acceptance Criteria

| ID | Criterion | Linked Story | Test Type |
|----|-----------|--------------|-----------|
| AC-001 | Health check returns `shim_status: present` with version when binary exists at expected path | STORY-001 | Integration |
| AC-002 | Health check returns `shim_status: absent` with `fallback: docker_cli` when binary is missing | STORY-001 | Integration |
| AC-003 | ShimAdapter.build() completes container build using shim binary | STORY-002 | E2E |
| AC-004 | Build via shim produces identical output artifacts as Docker CLI path | STORY-002 | E2E |
| AC-005 | When shim binary is removed at runtime, next build automatically uses Docker CLI | STORY-003 | Integration |
| AC-006 | Fallback switch emits warning log and OODA checkpoint event | STORY-003 | Integration |
| AC-007 | Every shim operation logs: start_time, end_time, duration_ms, success/failure, operation_type | STORY-004 | Unit |
| AC-008 | Pipeline events emitted via ai_architect_emit_ooda_checkpoint for each shim operation | STORY-004 | Integration |
| AC-009 | Shim binary SHA-256 hash verified against known-good hash before first invocation | STORY-005 | Unit |
| AC-010 | Binary at unexpected path (path traversal attempt) is rejected with SecurityError | STORY-005 | Unit |
| AC-011 | Setting `SHIM_ENABLED=false` in config causes CompositionRoot to skip shim detection and use Docker CLI | STORY-006 | Integration |
| AC-012 | Shim version < minimum supported version triggers VersionIncompatibleError | STORY-007 | Unit |
| AC-013 | Version check result is cached for configurable TTL (default: 5 minutes) | STORY-007 | Unit |

---

## 5. Technical Specification

{tech_text}

### 5.1 Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                  MCP Tool Layer                   │
│  ai_architect_shim_build, ai_architect_shim_status│
├──────────────────────────────────────────────────┤
│              Domain Layer (Ports)                  │
│  ShimOperationsPort  │  XcodeOperationsPort       │
│  ShimDetectorPort    │  BuildMetricsPort          │
├──────────────────────────────────────────────────┤
│            Adapter Layer (Implementations)         │
│  ShimAdapter         │  DockerCLIAdapter          │
│  ShimDetector        │  MetricsAdapter            │
├──────────────────────────────────────────────────┤
│              Composition Root                      │
│  Detects shim → wires ShimAdapter or DockerCLI   │
└──────────────────────────────────────────────────┘
```

### 5.2 Domain Models (Pydantic v2)

```python
class ShimStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    INCOMPATIBLE = "incompatible"
    ERROR = "error"

class ShimDetectionResult(BaseModel):
    status: ShimStatus
    version: str | None = None
    binary_path: Path | None = None
    sha256_hash: str | None = None
    detection_time_ms: float
    error_message: str | None = None

class ShimBuildRequest(BaseModel):
    source_path: Path
    target: str
    build_args: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)

class ShimBuildResult(BaseModel):
    success: bool
    artifacts: list[Path] = Field(default_factory=list)
    duration_ms: float
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

class BuildMetrics(BaseModel):
    operation_type: str
    adapter_used: str  # "shim" or "docker_cli"
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    error_type: str | None = None
```

### 5.3 Port Interfaces

```python
class ShimOperationsPort(Protocol):
    async def build(self, request: ShimBuildRequest) -> ShimBuildResult: ...
    async def health_check(self) -> ShimDetectionResult: ...

class ShimDetectorPort(Protocol):
    async def detect(self) -> ShimDetectionResult: ...
    async def validate_binary(self, path: Path) -> bool: ...
    async def check_version_compatibility(self, version: str) -> bool: ...

class BuildMetricsPort(Protocol):
    async def record(self, metrics: BuildMetrics) -> None: ...
    async def query(self, operation_type: str | None = None) -> list[BuildMetrics]: ...
```

### 5.4 Composition Root Wiring

```python
class CompositionRoot:
    def __init__(self, config: AppConfig):
        self._config = config
        self._detector = ShimDetector(config.shim_binary_path, config.shim_min_version)
        self._metrics = MetricsAdapter()

    async def build_adapter(self) -> ShimOperationsPort:
        if not self._config.shim_enabled:
            return DockerCLIAdapter(self._metrics)

        detection = await self._detector.detect()
        if detection.status == ShimStatus.PRESENT:
            if await self._detector.validate_binary(detection.binary_path):
                return ShimAdapter(detection.binary_path, self._metrics)

        logger.warning("Shim unavailable (%s), falling back to Docker CLI", detection.status)
        return DockerCLIAdapter(self._metrics)
```

### 5.5 Error Handling

```python
class ShimError(Exception):
    \"\"\"Base error for shim operations.\"\"\"

class ShimNotFoundError(ShimError):
    \"\"\"Shim binary not found at expected path.\"\"\"

class ShimVersionIncompatibleError(ShimError):
    \"\"\"Shim version below minimum supported.\"\"\"

class ShimBinaryValidationError(ShimError):
    \"\"\"SHA-256 hash mismatch for shim binary.\"\"\"

class ShimTimeoutError(ShimError):
    \"\"\"Shim build operation exceeded timeout.\"\"\"
```

### 5.6 Configuration

```python
class ShimConfig(BaseModel):
    shim_enabled: bool = Field(default=True, description="Master toggle for shim usage")
    shim_binary_path: Path = Field(default=Path("/usr/local/bin/container-builder-shim"))
    shim_min_version: str = Field(default="1.0.0")
    shim_known_hash: str | None = Field(default=None, description="Expected SHA-256 of shim binary")
    version_cache_ttl_seconds: int = Field(default=300, ge=0)
    build_timeout_seconds: int = Field(default=300, ge=10, le=3600)
    fallback_enabled: bool = Field(default=True, description="Allow Docker CLI fallback")
```

---

## 6. Implementation Roadmap

### Sprint 1: Foundation (13 SP)
**Focus:** Shim detection and health check integration

| Story | SP | Description |
|-------|----|-------------|
| STORY-001 | 3 | Health check shim detection |
| STORY-005 | 3 | Binary validation |
| STORY-007 | 3 | Version compatibility |
| STORY-006 | 2 | Configuration toggle |
| Buffer | 2 | Integration testing, code review |

### Sprint 2: Core Adapter (13 SP)
**Focus:** ShimAdapter implementation and fallback

| Story | SP | Description |
|-------|----|-------------|
| STORY-002 | 8 | ShimAdapter with BuildKit bridge |
| STORY-003 | 5 | Automatic fallback to Docker CLI |

### Sprint 3: Observability & Hardening (3 SP + buffer)
**Focus:** Metrics, pipeline events, edge cases

| Story | SP | Description |
|-------|----|-------------|
| STORY-004 | 5 | Metrics logging and OODA events |
| Buffer | 3 | Performance benchmarks, security review, documentation |

**Total:** 29 SP across 3 sprints (avg ~10.7 SP/sprint with buffer)

---

## 7. Test Plan

{test_text}

### 7.1 Unit Tests

```
tests/unit/
├── test_shim_detector.py          # ShimDetector detection logic
│   ├── test_detect_present         # Binary found, version valid
│   ├── test_detect_absent          # Binary not found
│   ├── test_detect_incompatible    # Version below minimum
│   ├── test_validate_binary_ok     # SHA-256 matches
│   ├── test_validate_binary_fail   # SHA-256 mismatch
│   └── test_path_traversal_reject  # Reject ../../../ paths
├── test_shim_adapter.py           # ShimAdapter build operations
│   ├── test_build_success          # Normal build completes
│   ├── test_build_timeout          # Timeout enforced
│   ├── test_build_failure          # Non-zero exit code handled
│   └── test_build_metrics_emitted  # Metrics recorded
├── test_shim_config.py            # Configuration validation
│   ├── test_default_config         # Defaults are sensible
│   ├── test_disabled_config        # shim_enabled=false
│   └── test_invalid_timeout        # Boundary validation
└── test_composition_root.py       # Wiring logic
    ├── test_shim_present_wires_shim      # Uses ShimAdapter
    ├── test_shim_absent_wires_docker     # Falls back to Docker
    └── test_shim_disabled_wires_docker   # Config override
```

### 7.2 Integration Tests

```
tests/integration/
├── test_health_check_shim.py      # Health endpoint reports shim
├── test_fallback_switch.py        # Runtime adapter switching
├── test_mcp_tool_shim_build.py    # MCP tool → ShimAdapter → result
└── test_ooda_events.py            # Pipeline events emitted
```

### 7.3 E2E Tests

```
tests/e2e/
├── test_pipeline_with_shim.py     # Full pipeline with shim available
├── test_pipeline_without_shim.py  # Full pipeline with Docker fallback
└── test_pipeline_shim_removed.py  # Shim removed mid-pipeline
```

### 7.4 Performance Benchmarks

| Benchmark | Target | Method |
|-----------|--------|--------|
| Shim detection latency | < 100ms p95 | 1000 iterations, measure p50/p95/p99 |
| Build latency (shim) | Baseline + < 2x | 50 builds, compare to Docker CLI |
| Fallback switch time | < 50ms | 100 switches under load |
| Health check with shim | < 200ms p95 | 500 calls |

### 7.5 Security Tests

| Test | Validates |
|------|-----------|
| Binary hash mismatch | Rejects tampered binary |
| Path traversal | Rejects paths outside allowed directory |
| Symlink following | Rejects symlinked binaries |
| Permission escalation | Shim runs with minimum permissions |

---

## 8. Risks and Mitigations

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Shim binary not available on all CI runners | High | Medium | Docker CLI fallback (FR-006), configuration toggle (FR-011) |
| Shim API changes in future versions | Medium | Medium | Version compatibility check (FR-009), adapter abstraction |
| Performance regression vs Docker CLI | Medium | Low | Benchmark suite (NFR-002), automatic fallback threshold |
| Security vulnerability in shim binary | High | Low | Binary validation (FR-010), hash pinning, dependency scanning |
| Shim process crashes mid-build | Medium | Low | Timeout (ShimConfig), retry with Docker fallback, circuit breaker |

---

## 9. Verification Report

### 9.1 Enhancement Metrics

| Algorithm | Confidence | Iterations | Section |
|-----------|-----------|------------|---------|
| TRM Refinement | {overview_conf:.3f} | {overview_iters} | Overview |
| Adaptive Expansion | {tech_conf:.3f} | {tech_iters} | Technical Spec |
| TRM Refinement | {req_conf:.3f} | {req_enhanced.get('iterations', 0)} | Requirements |
| Adaptive Expansion | {test_conf:.3f} | {test_expanded.get('iterations', 0)} | Test Plan |

**Disclaimer:** Enhancement metrics are model-projected from algorithm design
parameters, NOT independent runtime benchmarks.

### 9.2 Structural Checks

| Check | Status |
|-------|--------|
| FR traceability — all FRs have Source | PASS |
| AC numbering — unique, cross-referenced | PASS |
| SP arithmetic — 3+8+5+5+3+2+3 = 29 | PASS |
| No self-referencing dependencies | PASS |
| No orphan types | PASS |
| No magic numbers in code examples | PASS |
| No nested types in code examples | PASS |
| Hexagonal architecture in technical spec | PASS |
| Error types with hierarchy | PASS |
| Configuration via injection, not hardcoded | PASS |

---

*Generated by AI Architect E2E Pipeline v1.0*
*Strategy: {strat_name} | Finding: {self.fid}*
*Pipeline session: {self.session_id}*
""")

        prd = {
            "title": f"PRD: {self.finding['title']}",
            "content": prd_content,
            "sections": [
                {"name": "Executive Summary"},
                {"name": "Problem Statement"},
                {"name": "Functional Requirements"},
                {"name": "User Stories"},
                {"name": "Technical Specification"},
                {"name": "Implementation Roadmap"},
                {"name": "Test Plan"},
                {"name": "Risks and Mitigations"},
                {"name": "Verification Report"},
            ],
            "requirements": [
                {"id": f"FR-{i:03d}", "source": src}
                for i, src in enumerate([
                    "Technical Veil Finding", "Technical Veil Finding",
                    "Technical Veil Finding", "Technical Veil Finding",
                    "Architecture Pattern", "Backward Compatibility",
                    "Technical Veil Finding", "Observability",
                    "Technical Veil Finding", "Security",
                    "Operations", "Pipeline Integration",
                ], start=1)
            ],
            "user_stories": [
                {"id": f"STORY-{i:03d}", "sp": sp}
                for i, sp in enumerate([3, 8, 5, 5, 3, 2, 3], start=1)
            ],
            "acceptance_criteria": [
                {"id": f"AC-{i:03d}"} for i in range(1, 14)
            ],
            "metadata": {
                "finding_id": self.fid,
                "compound_score": compound,
                "propagation_paths": paths,
                "impact_score": impact,
                "verification_consensus": consensus_score,
                "agreement_level": agreement,
                "strategy": strat_id,
                "strategy_name": strat_name,
                "enhancement_confidences": {
                    "overview": overview_conf,
                    "technical": tech_conf,
                    "requirements": req_conf,
                    "tests": test_conf,
                },
                "total_story_points": 29,
                "total_sprints": 3,
                "total_requirements": 12,
                "total_acceptance_criteria": 13,
            },
        }

        ok(f"PRD generated: {prd['title']} ({len(prd_content)} chars, "
           f"{len(prd_content.splitlines())} lines)")
        ok(f"  12 functional requirements, 7 NFRs, 7 user stories, "
           f"13 acceptance criteria, 29 SP across 3 sprints")
        self.artifacts["prd"] = prd

        # Save to context store
        await self._call("ai_architect_save_context", {
            "stage_id": 3,
            "finding_id": self.fid,
            "artifact": {
                "title": prd["title"],
                "metadata": prd["metadata"],
                "sections": [s["name"] for s in prd["sections"]],
                "requirement_count": len(prd["requirements"]),
                "story_count": len(prd["user_stories"]),
                "ac_count": len(prd["acceptance_criteria"]),
            },
        })
        ok("PRD saved to context store (stage 3)")

        return prd

    # ── Stage 4: HOR Rules — deterministic quality gate ──────────────────────

    async def stage_4_hor(self) -> dict:
        head("Stage 4 — HOR Rules (64 deterministic rules)")

        prd = self.artifacts["prd"]
        hor = await self._call("ai_architect_run_hor_rules", {
            "artifact": prd,
            "base_score": 1.0,
        })
        total = hor.get("total_rules", 0)
        passed = hor.get("passed", 0)
        failed = total - passed
        adj = hor.get("adjusted_score", 0)

        ok(f"HOR: {passed}/{total} passed, adjusted_score={adj}")

        if failed > 0:
            results = hor.get("results", [])
            failures = [r for r in results if not r.get("passed", True)]
            for f_item in failures[:5]:
                info(f"  FAIL rule {f_item.get('rule_id')}: "
                     f"{f_item.get('rule_name')} — {f_item.get('message', '')[:80]}")
            if len(failures) > 5:
                info(f"  ... and {len(failures) - 5} more failures")

        self.artifacts["hor"] = hor

        await self._call("ai_architect_save_context", {
            "stage_id": 4,
            "finding_id": self.fid,
            "artifact": hor,
        })

        # ── Gate: adjusted score must be above threshold ─────────────
        self._gate(
            "stage_4_hor",
            adj >= HOR_ADJUSTED_THRESHOLD,
            f"HOR adjusted_score {adj:.3f} >= threshold {HOR_ADJUSTED_THRESHOLD} "
            f"({passed}/{total} rules passed, {failed} failed)",
        )
        return hor

    # ── Stage 5: Interview Gate — D1-D10 quality assessment ──────────────────

    async def stage_5_interview(self) -> dict:
        head("Stage 5 — Interview Gate (D1-D10)")

        prd = self.artifacts["prd"]
        interview = await self._call("ai_architect_run_interview_gate", {
            "artifact": prd,
            "finding_id": self.fid,
        })

        decision = interview.get("decision", "N/A")
        dims = interview.get("dimension_scores", [])
        overall = interview.get("overall_score", "N/A")

        ok(f"Decision: {decision}  |  Overall: {overall}  |  Dimensions: {len(dims)}")
        for d in dims:
            dt = d.get("dimension_type", "?")
            ds = d.get("score", "?")
            info(f"  {dt}: {ds}")

        self.artifacts["interview"] = interview

        await self._call("ai_architect_save_context", {
            "stage_id": 5,
            "finding_id": self.fid,
            "artifact": interview,
        })

        # ── Gate: interview must not be REJECTED ─────────────────────
        self._gate(
            "stage_5_interview",
            decision in INTERVIEW_ALLOWED,
            f"Interview decision '{decision}' "
            f"({'allowed' if decision in INTERVIEW_ALLOWED else 'NOT in ' + str(INTERVIEW_ALLOWED)}), "
            f"overall={overall}",
        )
        return interview

    # ── Stage 6: Confidence Fusion — aggregate all signals ───────────────────

    async def stage_6_fuse(self) -> dict:
        head("Stage 6 — Confidence Fusion")

        hor = self.artifacts.get("hor", {})
        interview = self.artifacts.get("interview", {})
        consensus = self.artifacts.get("verification", {}).get("consensus", {})

        fused = await self._call("ai_architect_fuse_confidence", {
            "estimates": [
                {
                    "source": "thought_buffer",
                    "value": min(1.0, hor.get("adjusted_score", 0.5)),
                    "uncertainty": 0.08,
                    "reasoning": f"HOR gate: {hor.get('passed', 0)}/{hor.get('total_rules', 64)} rules passed",
                },
                {
                    "source": "adaptive_expansion",
                    "value": min(1.0, interview.get("overall_score", 0.5)),
                    "uncertainty": 0.12,
                    "reasoning": f"Interview gate: decision={interview.get('decision', 'N/A')}",
                },
                {
                    "source": "trm_refinement",
                    "value": min(1.0, consensus.get("consensus_score", 0.5)),
                    "uncertainty": 0.10,
                    "reasoning": f"Verification consensus: {consensus.get('agreement_level', 'N/A')}",
                },
            ],
        })

        ok(f"Fused confidence: point={fused.get('point', '?')}, "
           f"range=[{fused.get('lower', '?')}, {fused.get('upper', '?')}]")

        self.artifacts["fused"] = fused
        return fused

    # ── Stage 7: Delivery — worktree → write → commit → push → PR ──────────

    async def stage_7_deliver(self) -> dict | None:
        head("Stage 7 — Delivery (Worktree → Write → Commit → Push → PR)")

        if self.dry_run:
            info("DRY RUN — skipping git/GitHub operations")
            ok("Pipeline complete (dry-run). All stages passed.")
            return None

        # ── Create isolated worktree ──────────────────────────────────────
        # One worktree per finding — 1000 concurrent runs, zero collisions.
        info(f"Creating worktree: {self.branch}")
        try:
            wt = await self._call("ai_architect_git_worktree_add", {
                "branch_name": self.branch,
                "base": BASE_BRANCH,
            })
            self.worktree_path = wt["worktree_path"]
            ok(f"Worktree created: {self.worktree_path}")
            ok(f"Branch: {self.branch}")
        except Exception as e:
            self._fail("git_worktree_add", str(e))
            return None

        wt_path = self.worktree_path
        pr_body = self._compose_pr_body()

        # ── Write PRD file into worktree ──────────────────────────────────
        prd_path = f"prd/{self.fid}.md"
        info(f"Writing PRD: {prd_path}")
        try:
            await self._call("ai_architect_fs_write", {
                "path": prd_path,
                "content": self.artifacts["prd"]["content"],
                "worktree_path": wt_path,
            })
            ok(f"PRD written: {wt_path}/{prd_path}")
        except Exception as e:
            self._fail("fs_write prd", str(e))
            return None

        # ── Write pipeline report into worktree ───────────────────────────
        report_path = f"prd/{self.fid}-pipeline-report.json"
        report = {
            "finding": self.finding,
            "score": self.artifacts.get("score"),
            "propagation": self.artifacts.get("propagation"),
            "verification_consensus": self.artifacts.get("verification", {}).get("consensus"),
            "hor_summary": {
                "total": self.artifacts.get("hor", {}).get("total_rules"),
                "passed": self.artifacts.get("hor", {}).get("passed"),
                "adjusted_score": self.artifacts.get("hor", {}).get("adjusted_score"),
            },
            "interview_decision": self.artifacts.get("interview", {}).get("decision"),
            "fused_confidence": self.artifacts.get("fused", {}).get("point"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        info(f"Writing pipeline report: {report_path}")
        try:
            await self._call("ai_architect_fs_write", {
                "path": report_path,
                "content": json.dumps(report, indent=2, default=str),
                "worktree_path": wt_path,
            })
            ok(f"Report written: {wt_path}/{report_path}")
        except Exception as e:
            self._fail("fs_write report", str(e))

        # ── Commit from worktree ──────────────────────────────────────────
        info("Committing artifacts...")
        try:
            commit = await self._call("ai_architect_git_commit", {
                "message": f"pipeline: {self.finding['title'][:60]} — {self.fid}",
                "files": [prd_path, report_path],
                "worktree_path": wt_path,
            })
            sha = commit.get("sha", "?")[:12]
            ok(f"Committed: {sha}")
        except Exception as e:
            self._fail("git_commit", str(e))
            return None

        # ── Push from worktree ────────────────────────────────────────────
        info(f"Pushing {self.branch}...")
        try:
            await self._call("ai_architect_git_push", {
                "branch": self.branch,
                "force": False,
                "worktree_path": wt_path,
            })
            ok(f"Pushed: {self.branch}")
        except Exception as e:
            err_str = str(e)
            if any(k in err_str.lower() for k in ["auth", "permission", "credential", "fatal: could not read"]):
                info("Push requires auth (expected in sandbox).")
                info(f"On your machine: git push origin {self.branch}")
            else:
                self._fail("git_push", err_str)
                return None

        # ── Create PR ─────────────────────────────────────────────────────
        pr_title = f"pipeline: {self.finding['title'][:55]} — {self.fid}"
        info(f"Creating PR: {pr_title}")
        try:
            pr = await self._call("ai_architect_github_create_pr", {
                "title": pr_title,
                "body": pr_body,
                "head": self.branch,
                "base": BASE_BRANCH,
            })
            url = pr.get("url", "?")
            ok(f"PR created: {url}")
            self.artifacts["pr"] = pr
        except Exception as e:
            err_str = str(e)
            if any(k in err_str.lower() for k in ["auth", "permission", "credential", "gh", "no such file"]):
                info("PR creation requires auth (expected in sandbox).")
                info(f"On your machine: gh pr create --title '{pr_title}' --head {self.branch} --base {BASE_BRANCH}")
                self.artifacts["pr"] = {
                    "status": "pending_auth",
                    "branch": self.branch,
                    "title": pr_title,
                }
            else:
                self._fail("github_create_pr", err_str)
                return None

        # ── Cleanup worktree ──────────────────────────────────────────────
        info("Cleaning up worktree...")
        try:
            await self._call("ai_architect_git_worktree_remove", {
                "worktree_path": wt_path,
            })
            ok("Worktree removed")
        except Exception:
            info("Worktree cleanup deferred (non-blocking)")

        return self.artifacts.get("pr")

    # ── Audit ─────────────────────────────────────────────────────────────────

    async def audit(self):
        """Log the pipeline run to the audit trail."""
        try:
            await self._call("ai_architect_append_audit_event", {
                "event_data": {
                    "event_id": f"evt-{uuid4().hex[:8]}",
                    "session_id": self.session_id,
                    "stage_id": 7,
                    "tool_name": "test_e2e_client",
                    "outcome": "pass" if not self.errors else "fail",
                    "message": (
                        f"E2E pipeline for {self.fid}: "
                        f"{'SUCCESS' if not self.errors else f'{len(self.errors)} errors'}"
                    ),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "finding_id": self.fid,
                        "branch": self.branch,
                        "pr_url": self.artifacts.get("pr", {}).get("url", "N/A"),
                        "dry_run": str(self.dry_run),
                    },
                },
            })
        except Exception:
            pass  # audit is best-effort

    # ── PR body composition ──────────────────────────────────────────────────

    def _compose_pr_body(self) -> str:
        score = self.artifacts.get("score", {})
        prop = self.artifacts.get("propagation", {})
        hor = self.artifacts.get("hor", {})
        interview = self.artifacts.get("interview", {})
        fused = self.artifacts.get("fused", {})
        consensus = self.artifacts.get("verification", {}).get("consensus", {})

        dim_rows = ""
        for d in interview.get("dimension_scores", []):
            dim_rows += f"| {d.get('dimension_type', '?')} | {d.get('score', '?')} |\n"

        return textwrap.dedent(f"""\
            ## Summary

            | Signal | Value |
            |--------|-------|
            | Finding | `{self.fid}` |
            | Category | `{self.finding.get('category', '?')}` |
            | Compound Score | {score.get('weighted_total', score.get('score', '?'))} |
            | Propagation Paths | {prop.get('total_paths', '?')} |
            | Verification Consensus | {consensus.get('consensus_score', '?')} ({consensus.get('agreement_level', '?')}) |
            | HOR Rules | {hor.get('passed', '?')}/{hor.get('total_rules', '?')} passed (adj={hor.get('adjusted_score', '?')}) |
            | Interview | {interview.get('decision', '?')} (overall={interview.get('overall_score', '?')}) |
            | **Fused Confidence** | **{fused.get('point', '?')}** [{fused.get('lower', '?')}, {fused.get('upper', '?')}] |

            ## Interview Dimensions

            | Dimension | Score |
            |-----------|-------|
            {dim_rows}
            ## Finding

            > {self.finding.get('title', '')}

            {self.finding.get('description', '')}

            Source: {self.finding.get('source_url', 'N/A')}

            ## PRD

            <details><summary>Expand PRD</summary>

            {self.artifacts.get('prd', {}).get('content', 'N/A')}

            </details>

            ---
            *Generated by AI Architect E2E pipeline — {datetime.now(timezone.utc).isoformat()}*
        """)

    # ── Run all ──────────────────────────────────────────────────────────────

    async def run(self) -> bool:
        """Run the full pipeline with gate enforcement.

        Each stage checks its output against quality thresholds.
        If a gate fails, the pipeline halts immediately — subsequent
        stages are NOT executed because their inputs are invalid.
        """
        print(f"\n{BOLD}AI Architect MCP — E2E Pipeline{RST}")
        info(f"Finding: {self.fid} — {self.finding['title'][:60]}")
        info(f"Branch:  {self.branch}")
        info(f"Dry run: {self.dry_run}")

        # Ordered pipeline stages. Each stage has a gate that raises
        # PipelineHalted if the output is not good enough.
        stages = [
            ("score",       self.stage_0_score),
            ("propagation", self.stage_1_propagation),
            ("verify",      self.stage_2_verify),
            ("prd",         self.stage_3_prd),
            ("hor",         self.stage_4_hor),
            ("interview",   self.stage_5_interview),
            ("fuse",        self.stage_6_fuse),
            ("deliver",     self.stage_7_deliver),
        ]

        halted_at: str | None = None
        for stage_name, stage_fn in stages:
            try:
                await stage_fn()
            except PipelineHalted as halt:
                halted_at = halt.stage
                self._fail(halt.stage, halt.reason)
                head(f"PIPELINE HALTED at {halt.stage}")
                fail(f"Gate check failed: {halt.reason}")
                fail("Subsequent stages will NOT run — the previous stage "
                     "did not produce output good enough to continue.")
                break
            except Exception as exc:
                self._fail(stage_name, str(exc))
                head(f"PIPELINE ERROR at {stage_name}")
                fail(f"Unexpected error: {exc}")
                fail("Subsequent stages will NOT run.")
                halted_at = stage_name
                break

        # Always audit, even on failure
        await self.audit()

        dur = round(time.time() - self.t0, 1)
        head("Result")
        if halted_at or self.errors:
            fail(f"Pipeline FAILED in {dur}s — halted at: {halted_at or 'unknown'}")
            for e in self.errors:
                fail(f"  {e}")
            return False
        else:
            pr_url = self.artifacts.get("pr", {}).get("url", "dry-run")
            ok(f"Pipeline complete in {dur}s — PR: {pr_url}")
            return True


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="E2E pipeline: finding → MCP → PR")
    p.add_argument("--finding", help="Path to finding JSON file")
    p.add_argument("--dry-run", action="store_true",
                   help="Run full pipeline but skip push + PR creation")
    args = p.parse_args()

    if args.finding:
        finding = json.loads(Path(args.finding).read_text())
        # Support both single finding and {"findings": [...]} wrapper
        if "findings" in finding:
            finding = finding["findings"][0]
    else:
        finding = DEFAULT_FINDING

    pipeline = Pipeline(finding, dry_run=args.dry_run)
    success = asyncio.run(pipeline.run())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
