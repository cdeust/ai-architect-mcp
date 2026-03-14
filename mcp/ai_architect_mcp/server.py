"""AI Architect MCP Server entry point.

FastMCP server exposing four tool groups:
- Verification: 5 evaluation algorithms + 2 consensus methods + 64 HOR rules
- Prompting: 5 enhancement algorithms + 15 thinking strategies
- Context: StageContext load/save/query + HandoffDocument management
- Adapters: Git, Xcode, GitHub, FileSystem operations via port interfaces

All tools are prefixed with ai_architect_ and annotated with:
readOnlyHint, destructiveHint, idempotentHint, openWorldHint.
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("ai-architect")


# ── Verification Tools ────────────────────────────────────────────────────────
# 5 evaluation algorithms:
#   1. KS Adaptive Stability Consensus
#   2. Multi-Agent Debate
#   3. Zero-LLM Graph Verification
#   4. NLI Entailment Evaluator
#   5. Weighted Average Consensus
#
# 64 HOR (Higher-Order Reasoning) rules for deterministic verification.
# 3 pipeline gates (not HOR rules).
#
# TODO: Register tools from _verification/ when algorithms are implemented.


# ── Prompting Tools ──────────────────────────────────────────────────────────
# 5 enhancement algorithms:
#   1. Adaptive Expansion (ToT/GoT)
#   2. Metacognitive
#   3. Collaborative Inference
#   4. Signal-Aware Thought Buffer
#   5. Confidence Fusion
#
# 15 thinking strategies auto-selected by project type.
#
# TODO: Register tools from _prompting/ when algorithms are implemented.


# ── Context Tools ────────────────────────────────────────────────────────────
# StageContext: load, save, query per finding per stage.
# HandoffDocument: session boundary persistence.
# Progressive disclosure: config (500t) → summaries (300t) → full docs (3Kt).
#
# TODO: Register tools from _context/ when context engine is implemented.


# ── Adapter Tools ────────────────────────────────────────────────────────────
# Git: branch, commit, push, diff, log via GitOperationsPort.
# Xcode: build, test, preview via XcodeOperationsPort.
# GitHub: PR create, review, merge via GitHubOperationsPort.
# FileSystem: read, write, list via FileSystemPort.
#
# TODO: Register tools from _adapters/ when adapters are implemented.


def main() -> None:
    """Start the AI Architect MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
