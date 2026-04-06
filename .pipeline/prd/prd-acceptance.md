# Acceptance Criteria — FIND-001

| ID | Criterion | Traces To |
|----|-----------|-----------|
| AC-001 | Given identical (messages, system, model, temperature) inputs, the second call SHALL return the cached response without invoking ctx.sample() | FR-001 |
| AC-002 | Given 3 retry cycles with 5 evaluations each, at least 10 of 15 calls SHALL be cache hits | FR-001, NFR-001 |
| AC-003 | No file in _prompting/algorithms/ SHALL be modified | FR-003 |
| AC-004 | All existing prompting algorithm tests SHALL pass without modification | FR-003 |
| AC-005 | When cache reaches 128 entries, the least recently used entry SHALL be evicted | FR-002 |
| AC-006 | Cache memory SHALL not exceed 50MB with 128 entries of typical LLM responses | NFR-002 |
| AC-007 | Cache operations SHALL be safe under concurrent async access | FR-006 |
| AC-008 | Cache hits SHALL return independent copies (mutations do not affect cache) | FR-007 |
