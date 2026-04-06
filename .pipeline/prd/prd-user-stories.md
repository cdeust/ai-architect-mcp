# User Stories — FIND-001

## STORY-001: Pipeline Operator — Faster Retry Cycles
As a pipeline operator running findings through stages 4-5 with retries, I want redundant LLM calls to be cached so that retry cycles complete 48 seconds faster per finding.

**Acceptance Criteria:** AC-001, AC-002

## STORY-002: Developer — Transparent Caching
As a developer maintaining prompting algorithms, I want the cache to be transparent so that I do not need to modify any algorithm code to benefit from caching.

**Acceptance Criteria:** AC-003, AC-004

## STORY-003: System — Resource Efficiency
As the MCP server process, I want cached responses to be bounded and evicted so that memory usage stays within acceptable limits.

**Acceptance Criteria:** AC-005, AC-006
