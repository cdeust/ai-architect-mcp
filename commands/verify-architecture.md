---
name: verify-architecture
description: Run 64 HOR rules and structural verification on the current codebase
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "[path-to-verify]"
---

# Verify Architecture

## Step 1 — Load Stage 7 skill

Read the verification skill:

```
Read skills/stage-7-verification/SKILL.md
```

This defines the deterministic verification stage — 64 HOR rules, build gate, graph verification. No LLM calls.

## Step 2 — Run HOR rules

```
ai_architect_run_hor_rules(document={codebase_content}, categories=["all"])
```

This runs all 64 deterministic rules across 10 categories:
- Core PRD Structural (23 rules)
- Architecture & Code Quality (7 rules)
- Security (8 rules)
- Data Protection & Compliance (6 rules)
- Error Handling & Resilience (5 rules)
- Concurrency & State Management (3 rules)
- Senior Code Quality Standards (6 rules)
- Comprehensive Testing (6 rules)
- Observability & Monitoring (4 rules)
- Dependency & Supply Chain (2 rules)

## Step 3 — Run verification scripts

```bash
scripts/verify-all.sh
```

This calls all verification scripts: zero-tolerance, swift-rules, 3rs, naming, claude-rules, production-tests, skill, security.

## Step 4 — Report

Report pass/fail per rule category with compound score. If `$ARGUMENTS` specifies a path, verify only that path.
