# Roadmap — FIND-001

## Sprint 1 (Current)
- [ ] Implement `_LRUCache` class in `sampling_client.py`
- [ ] Integrate cache into `_SamplingMessages.create()`
- [ ] Add cache key generation with SHA-256 hashing
- [ ] Add asyncio.Lock for thread safety
- [ ] Add deep copy on cache hit
- [ ] Write unit tests for cache behavior
- [ ] Run full test suite to verify transparency

## Future Considerations
- Cache hit rate metrics emission (observability)
- Configurable maxsize via defaults.toml
- Cache warming for known-good prompts
