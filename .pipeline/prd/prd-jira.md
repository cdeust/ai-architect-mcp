# JIRA Tickets — FIND-001

## Epic: FIND-001 — LRU Cache for Prompting LLM Calls

### FIND-001-1: Implement _LRUCache class
- **Type:** Task
- **Priority:** Critical
- **Story Points:** 3
- **Description:** Create bounded LRU cache with OrderedDict, maxsize, asyncio.Lock
- **Acceptance:** AC-005, AC-007

### FIND-001-2: Integrate cache into _SamplingMessages.create()
- **Type:** Task
- **Priority:** Critical
- **Story Points:** 2
- **Description:** Add cache lookup before ctx.sample(), cache store after response
- **Acceptance:** AC-001, AC-008

### FIND-001-3: Write cache tests
- **Type:** Task
- **Priority:** High
- **Story Points:** 3
- **Description:** Unit tests for hit/miss, eviction, invalidation, concurrency, deep copy
- **Acceptance:** AC-002, AC-003, AC-004, AC-006
