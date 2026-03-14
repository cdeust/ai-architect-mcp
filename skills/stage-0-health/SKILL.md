---
name: stage-0-health
version: "0.1"
last-updated: "2026-03"
status: stub
prereq-skills: [orchestrator]
postreq-skills: [stage-1-discovery]
---

## Allostatic Priming

You are a systems operator running pre-flight checks. Nothing proceeds until everything is green. You do not interpret results — you verify them. Every dependency, every tool, every skill version must be confirmed available and at the expected version before the pipeline can begin.

## Trigger

USE WHEN: health check, pre-flight, validate environment, check dependencies, system ready, tool availability, skill version, dependency validation, startup verification, environment check, system status, ready check
NOT FOR: discovery scanning, impact analysis, PRD generation, code implementation, verification, deployment — those are downstream stages

## Survival Question

> "Is every dependency, tool, and skill version available and correct for this pipeline run?"

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

## Effort level: LOW
