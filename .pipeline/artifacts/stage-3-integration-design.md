# Integration Design — FIND-001: LRU Cache for Prompting LLM Calls

## Affected Ports
- `SamplingClient.messages.create()` — the single LLM call entry point

## Design Decision
The LRU cache is implemented at the `_SamplingMessages.create()` level inside `sampling_client.py`. This is the funnel point — all 5 prompting algorithms call through this method. The cache is transparent: no algorithm code changes required.

## Cache Design
- **Key**: `(hash(messages), hash(system), model, temperature)` — deterministic for identical inputs
- **Storage**: Module-level `OrderedDict` with max 128 entries, LRU eviction
- **Scope**: Per-process (shared across all algorithms in a session)
- **Invalidation**: On model change, on explicit clear, on session boundary
- **Thread safety**: `asyncio.Lock` for async context

## Adapter Changes
| File | Change Type | Description |
|------|------------|-------------|
| `sampling_client.py` | Modify | Add `_LRUCache` class and integrate into `_SamplingMessages.create()` |

## No Changes Required (Transparent)
- `trm_refinement.py` — calls through SamplingClient
- `adaptive_expansion.py` — calls through SamplingClient
- `metacognitive.py` — calls through SamplingClient
- `thought_buffer.py` — calls through SamplingClient
- `collaborative_inference.py` — calls through SamplingClient

## Composition Root
No changes needed. SamplingClient is instantiated per-request with `ctx`. The cache is module-level.

## Circular Dependency Check
Graph verification score: 0.9429. No cycles detected.

## New Test File
`tests/test_adapters/test_sampling_cache.py` — cache hit/miss, eviction, invalidation, thread safety
