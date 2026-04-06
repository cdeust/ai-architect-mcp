# Technical Specification — FIND-001

## Architecture
The cache is implemented as a module-level `_LRUCache` class in `sampling_client.py`. It wraps an `OrderedDict` with maxsize enforcement. The `_SamplingMessages.create()` method checks the cache before making a sampling call and stores results after.

## Cache Key Generation
```python
import hashlib
import json

def _cache_key(messages: list[dict], system: str, model: str, temperature: float) -> str:
    content = json.dumps({"m": messages, "s": system, "mod": model, "t": temperature}, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

## Integration Point
- File: `mcp/ai_architect_mcp/_adapters/sampling_client.py`
- Class: `_SamplingMessages` — modify `create()` method
- No changes to: `SamplingClient`, `CompositionRoot`, or any algorithm file

## Dependency Direction
`_LRUCache` is private to `sampling_client.py`. No new imports. No new packages. Dependency direction unchanged: algorithms -> SamplingClient -> ctx.sample().

## Thread Safety
`asyncio.Lock` guards cache reads and writes. The lock is per-cache-instance (module singleton).
