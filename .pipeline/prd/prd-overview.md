# PRD Overview — FIND-001: LRU Cache for Prompting LLM Calls

## Title
Add LRU Caching to Sampling Client for Prompting Algorithm LLM Calls

## Category
Performance Optimization

## Priority
High

## Summary
Implement a bounded LRU cache at the `_SamplingMessages.create()` level in `sampling_client.py` to eliminate redundant LLM calls when identical prompts are submitted during pipeline retry cycles. All 5 prompting algorithms route through this single method, making it the optimal cache insertion point. Expected savings: 48 seconds per finding (15 eliminated calls at 3.2s each).

## Scope
- Single file modification: `sampling_client.py`
- Transparent to all 5 prompting algorithms (no algorithm code changes)
- Per-process cache with 128-entry bound and LRU eviction
- Cache key: `(hash(messages), hash(system), model, temperature)`

## HUMAN REVIEW REQUIRED
- Cache invalidation strategy may need tuning for production workloads
- 128-entry bound is an estimate; real-world measurement needed

## NEEDS-RUNTIME
- Actual cache hit rate under production pipeline runs
- Memory impact of cached responses at 128 entries
