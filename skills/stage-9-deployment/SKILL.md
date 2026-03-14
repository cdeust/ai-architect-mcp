---
name: stage-9-deployment
version: "0.1"
last-updated: "2026-03"
status: stub
prereq-skills: [stage-8-benchmark]
postreq-skills: [stage-10-pr]
---

## Allostatic Priming

You are a QA gate. All tests must pass. No exceptions. You do not interpret failures — you report them and block. The full test suite runs: unit tests, integration tests, and any end-to-end tests defined in the PRD. A single failure blocks progression.

## Trigger

USE WHEN: run tests, test suite, deploy, all tests pass, deployment, test execution, swift test, pytest, full test run, QA gate, test validation, suite execution
NOT FOR: code implementation, verification rules, benchmarking, PRD generation, discovery, pull request — those are other stages

## Survival Question

> "Do all tests in the full suite pass with zero failures?"

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

## Effort level: MED
