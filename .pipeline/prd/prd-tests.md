# Test Plan — FIND-001

## Unit Tests (tests/test_adapters/test_sampling_cache.py)

### test_cache_hit_returns_cached_response
Given identical inputs, verify second call returns cached response and ctx.sample() is called only once.

### test_cache_miss_calls_sampling
Given different inputs, verify ctx.sample() is called for each unique input.

### test_lru_eviction_at_maxsize
Fill cache to 128 entries, add one more, verify oldest entry is evicted.

### test_cache_clear_empties_all
Call clear(), verify all entries removed and next call goes to ctx.sample().

### test_deep_copy_on_hit
Mutate a returned response, verify cache still holds original.

### test_concurrent_access_safety
Run 10 concurrent cache operations, verify no race conditions or corrupted state.

### test_existing_algorithm_tests_pass
Run full prompting test suite, verify zero failures (transparency check).

## Integration Tests
### test_pipeline_retry_uses_cache
Run a simulated 3-retry pipeline cycle, measure cache hit count >= 10.
