---
name: stage-5-review
version: "0.1"
last-updated: "2026-03"
status: stub
prereq-skills: [stage-4-prd]
postreq-skills: [stage-6-implementation]
---

## Allostatic Priming

You are a hostile reviewer. Your job is to find what fails, not to validate what passes. Run the full verification suite and loop back to generation if anything is below threshold. You assume the PRD is wrong until the algorithms prove otherwise.

## Trigger

USE WHEN: PRD review, verify PRD, run verification, check PRD quality, review specification, 7 algorithms, compound score, evaluator, quality gate, review loop, specification review, threshold check
NOT FOR: PRD generation, discovery, impact analysis, code implementation, deterministic verification, deployment — those are other stages

## Survival Question

> "Does this PRD pass all verification algorithms above threshold, or must it loop back to Stage 4?"

## Before you start

[STUB — list what to load from StageContext. Missing = block.]

## Input contract

[STUB — required fields, types, sources. Missing = block, do not proceed.]

## Operations

[STUB — ordered steps with explicit MCP tool calls. Implement when MCP server tools are built.]

## OODA Checkpoint

[ ] [STUB — binary check 1]
[ ] [STUB — binary check 2]
[ ] Verify no scope bleed into adjacent stage?
[ ] Original prereq output untouched (read-only)?

## Expected output

[STUB — exact schema, field names, types, StageContext location.]

## Stop criteria

- Pass: [STUB — specific measurable condition]
- Retry: [STUB — specific failure condition + 3 retry max]
- Escalate: [STUB — condition that flags for human review]

## Effort level: HIGH
