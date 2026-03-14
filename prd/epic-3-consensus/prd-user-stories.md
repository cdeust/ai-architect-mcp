# User Stories: Epic 3 — Consensus Algorithm Completion

**Epic:** E3-CONSENSUS
**Total SP:** 10 (Fibonacci: 3 + 3 + 1 + 1 + 2)
**Last Updated:** 2026-03-14

---

## STORY-E3-001: Implement Bayesian Consensus Algorithm
**Story ID:** STORY-E3-001
**Title:** Implement Bayesian Consensus Algorithm
**Epic:** E3-CONSENSUS
**Size (SP):** 3
**Priority:** P0
**Assignee:** TBD
**Status:** Backlog

### Description
As an AI Architect verification engineer, I want to implement the Bayesian Consensus algorithm so that I can leverage Bayesian inference with Beta priors for probabilistic consensus decisions.

### Acceptance Criteria

**AC-E3-001: Beta Prior Initialization**
- GIVEN a BayesianConsensus instance with default configuration
- WHEN the instance is created
- THEN the Beta prior is initialized with α=2, β=2
- AND prior parameters can be overridden via constructor kwargs
- AND prior values are validated (α > 0, β > 0)

**AC-E3-002: Posterior Calculation via Beta-Binomial Conjugacy**
- GIVEN an input array of scores [0.8, 0.7, 0.6, 0.4] and threshold=0.5
- WHEN compute() is called
- THEN successes = 3 (scores >= 0.5), failures = 1 (scores < 0.5)
- AND posterior α' = 2 + 3 = 5, β' = 2 + 1 = 3
- AND posterior mean = 5 / (5 + 3) = 0.625
- AND consensus_score = 0.625 (exact match, no rounding)

**AC-E3-003: Credible Interval from Posterior**
- GIVEN a posterior with α'=5, β'=3
- WHEN credible_interval() is called
- THEN return (lower, upper) from scipy.stats.beta(5, 3).ppf([0.025, 0.975])
- AND interval is a tuple of floats, bounds are [0.25, 0.95] (approximate)
- AND handle uniform posterior edge case (α'=1, β'=1)

**AC-E3-004: Consensus Result with Confidence**
- GIVEN scores and prior
- WHEN compute() returns
- THEN ConsensusResult.algorithm == ConsensusAlgorithm.BAYESIAN
- AND ConsensusResult.consensus_score is posterior mean
- AND ConsensusResult.consensus_confidence is derived from credible interval width: 1.0 - (upper - lower)
- AND ConsensusResult.agreement_level matches variance: HIGH if variance <0.05, etc.
- AND ConsensusResult.individual_scores = input scores (unchanged)

**AC-E3-005: Error Handling**
- GIVEN empty scores array
- WHEN compute() is called
- THEN raise ValueError with message "Scores array cannot be empty"
- AND exception is logged

### Definition of Done
- [ ] Code written, formatted with black
- [ ] Type hints 100% coverage (mypy --strict pass)
- [ ] Docstrings in Google style
- [ ] Unit tests >90% coverage
- [ ] Peer review approved
- [ ] Benchmark <5ms mean for 20 scores
- [ ] Merged to main branch

### Related Requirements
- FR-E3-001, FR-E3-002, FR-E3-003, FR-E3-004

---

## STORY-E3-002: Implement Majority Voting Consensus Algorithm
**Story ID:** STORY-E3-002
**Title:** Implement Majority Voting Consensus Algorithm
**Epic:** E3-CONSENSUS
**Size (SP):** 3
**Priority:** P0
**Assignee:** TBD
**Status:** Backlog

### Description
As an AI Architect verification engineer, I want to implement the Majority Voting consensus algorithm so that I can provide deterministic majority-based consensus with configurable tie-breaking.

### Acceptance Criteria

**AC-E3-006: Voting Threshold Configuration**
- GIVEN a MajorityVoting instance with default threshold=0.5
- WHEN the instance is created
- THEN threshold is stored as 0.5
- AND threshold can be overridden (e.g., supermajority 0.66)
- AND threshold must be in range (0.0, 1.0), exclusive

**AC-E3-007: Vote Aggregation — Majority Rule**
- GIVEN scores [0.8, 0.7, 0.2, 0.1] with threshold=0.5
- WHEN compute() is called
- THEN vote_yes = 2 (scores >= 0.5), vote_no = 2 (scores < 0.5)
- AND majority ratio = 2 / 4 = 0.5
- AND check ratio >= threshold: 0.5 >= 0.5 is true → ACCEPT

**AC-E3-008: Consensus Score and Confidence**
- GIVEN vote_yes=3, vote_no=1, total=4
- WHEN compute() returns
- THEN consensus_score = 1.0 (ACCEPT, majority > threshold)
- AND consensus_confidence = (abs(vote_yes - vote_no) / total) = 0.5
- AND agreement_level = HIGH (confidence 0.5 > 0.15 threshold)

**AC-E3-009: Tie-Breaking — Three Strategies**
- GIVEN scores [0.8, 0.2] (vote_yes=1, vote_no=1, tie)
- WHEN compute() is called with tie_breaker=TieBreaker.HIGHEST_CONFIDENCE
- THEN deterministically pick the vote (0.8 > 0.2) → ACCEPT, confidence=1.0
- WHEN tie_breaker=TieBreaker.RANDOM_SEEDED
- THEN use seeded RNG (hash of scores) → deterministic outcome
- WHEN tie_breaker=TieBreaker.ESCALATE_TO_DEBATE
- THEN resolution = DisagreementResolution.FLAG_FOR_REVIEW, defer decision

**AC-E3-010: Edge Cases**
- GIVEN single score [0.7]
- WHEN compute() is called
- THEN consensus_score = 1.0, consensus_confidence = 1.0
- GIVEN empty scores
- WHEN compute() is called
- THEN raise ValueError "Scores array cannot be empty"

### Definition of Done
- [ ] Code written, formatted with black
- [ ] Type hints 100% coverage (mypy --strict pass)
- [ ] Docstrings in Google style
- [ ] TieBreaker enum implemented
- [ ] Unit tests >90% coverage, all tie-breaking paths tested
- [ ] Peer review approved
- [ ] Benchmark <5ms mean for 20 scores
- [ ] Merged to main branch

### Related Requirements
- FR-E3-005, FR-E3-006, FR-E3-007, FR-E3-008

---

## STORY-E3-003: Integrate ConsensusAlgorithm Enum Routing
**Story ID:** STORY-E3-003
**Title:** Integrate ConsensusAlgorithm Enum Routing
**Epic:** E3-CONSENSUS
**Size (SP):** 1
**Priority:** P0
**Assignee:** TBD
**Status:** Backlog

### Description
As an AI Architect developer, I want to integrate both Bayesian and Majority Voting algorithms into the ConsensusAlgorithm enum and routing engine so that the verification system can dispatch to them correctly.

### Acceptance Criteria

**AC-E3-011: Enum Rename — BAYESIAN_STUB → BAYESIAN**
- GIVEN ConsensusAlgorithm enum in `_models/consensus.py`
- WHEN BAYESIAN_STUB is renamed to BAYESIAN
- THEN all references are updated (no orphaned stub value)
- AND existing code (WEIGHTED_AVERAGE, ADAPTIVE_STABILITY) unchanged

**AC-E3-012: Enum Rename — MAJORITY_VOTING_STUB → MAJORITY_VOTING**
- GIVEN ConsensusAlgorithm enum
- WHEN MAJORITY_VOTING_STUB is renamed to MAJORITY_VOTING
- THEN all references are updated
- AND no breaking changes

**AC-E3-013: Router Integration**
- GIVEN ConsensusAlgorithm enum with BAYESIAN and MAJORITY_VOTING
- WHEN verification engine calls get_algorithm(ConsensusAlgorithm.BAYESIAN)
- THEN returns BayesianConsensus instance
- WHEN verification engine calls get_algorithm(ConsensusAlgorithm.MAJORITY_VOTING)
- THEN returns MajorityVoting instance
- AND all four algorithms (WEIGHTED_AVERAGE, ADAPTIVE_STABILITY, BAYESIAN, MAJORITY_VOTING) are routable

**AC-E3-014: No Breaking Changes**
- GIVEN existing consensus verification workflows
- WHEN new algorithms are integrated
- THEN all existing tests pass
- AND existing workflows continue to work unchanged

### Definition of Done
- [ ] Enum updated, all references fixed
- [ ] Router updated to support both new algorithms
- [ ] Existing test suite passes 100%
- [ ] Code review approved
- [ ] Merged to main branch

### Related Requirements
- FR-E3-009

---

## STORY-E3-004: Write ALG Decision Documents (ALG-011, ALG-012)
**Story ID:** STORY-E3-004
**Title:** Write ALG Decision Documents (ALG-011, ALG-012)
**Epic:** E3-CONSENSUS
**Size (SP):** 1
**Priority:** P0
**Assignee:** TBD
**Status:** Backlog

### Description
As an AI Architect documentation owner, I want to create ALG-011 and ALG-012 decision documents so that future engineers understand the design rationale and trade-offs of these algorithms.

### Acceptance Criteria

**AC-E3-015: ALG-011 — Bayesian Consensus Design Document**
- GIVEN ALG-011 document template
- WHEN completed
- THEN includes: algorithm design, Beta prior rationale, use cases, trade-offs, limitations
- AND includes pseudocode and references to scipy.stats.beta
- AND stored at `_architecture/alg/ALG-011-bayesian-consensus.md`

**AC-E3-016: ALG-012 — Majority Voting Design Document**
- GIVEN ALG-012 document template
- WHEN completed
- THEN includes: majority voting logic, three tie-breaking strategies, use cases, examples
- AND stored at `_architecture/alg/ALG-012-majority-voting.md`

**AC-E3-017: Cross-Links and References**
- GIVEN both ALG documents
- WHEN reviewed
- THEN ALG-011 and ALG-012 are linked in epic PRD
- AND each document references the other where applicable
- AND links to code (class names, file paths) are correct

### Definition of Done
- [ ] Both ALG documents written and reviewed
- [ ] All cross-references verified
- [ ] Stored in correct directory
- [ ] Peer review approved
- [ ] Merged to main branch

### Related Requirements
- FR-E3-010

---

## STORY-E3-005: Comprehensive Test Suite with Deterministic Fixtures
**Story ID:** STORY-E3-005
**Title:** Comprehensive Test Suite with Deterministic Fixtures
**Epic:** E3-CONSENSUS
**Size (SP):** 2
**Priority:** P0
**Assignee:** TBD
**Status:** Backlog

### Description
As an AI Architect QA engineer, I want to implement a comprehensive test suite with deterministic fixtures so that both algorithms are reliable and output is reproducible across runs.

### Acceptance Criteria

**AC-E3-018: Bayesian Consensus Tests**
- GIVEN test_bayesian_consensus.py
- WHEN tests run
- THEN cover: default prior initialization, posterior calculation, credible intervals, edge cases
- AND use deterministic fixtures with known inputs/outputs
- AND verify bit-for-bit output matching (no floating-point rounding)
- AND include fixtures: [scores, threshold, expected_posterior, expected_confidence]

**AC-E3-019: Majority Voting Tests**
- GIVEN test_majority_voting.py
- WHEN tests run
- THEN cover: vote aggregation, threshold rules, all three tie-breakers
- AND verify deterministic output with seeded RNG
- AND test edge cases: empty array, single vote, all votes same, ties
- AND confidence calculations are correct

**AC-E3-020: Consensus Routing Tests**
- GIVEN test_consensus_routing.py
- WHEN enum-based routing is tested
- THEN verify BAYESIAN and MAJORITY_VOTING enums resolve to correct instances
- AND all four algorithms are callable
- AND no cross-talk between algorithms

**AC-E3-021: Deterministic Fixture Data**
- GIVEN fixture file fixtures/consensus_test_data.json
- WHEN tests use this data
- THEN all tests produce identical output across runs
- AND fixture includes: score arrays, expected results, tie-breaking scenarios
- AND seeded RNG ensures reproducibility

**AC-E3-022: Coverage and Performance**
- GIVEN all tests
- WHEN pytest-cov is run
- THEN code coverage >90% for both algorithms
- WHEN pytest-benchmark is run
- THEN mean computation time <5ms for 20 scores, p99 <10ms

### Definition of Done
- [ ] All tests written and passing
- [ ] Coverage >90% verified
- [ ] Deterministic fixtures created
- [ ] Benchmark results documented
- [ ] All tests pass on CI/CD
- [ ] Peer review approved
- [ ] Merged to main branch

### Related Requirements
- NFR-E3-001, NFR-E3-002, NFR-E3-005

---

## Story Dependency Graph

```
STORY-E3-001 (3 SP) ─────────┐
                             ├─→ STORY-E3-003 (1 SP) ─┐
STORY-E3-002 (3 SP) ─────────┘                       ├─→ STORY-E3-005 (2 SP)
                                                     │
STORY-E3-004 (1 SP) ──────────────────────────────────┘
(No dependencies, parallel)

Total: 10 SP
```

**Critical Path:** STORY-E3-001 → STORY-E3-003 → STORY-E3-005 (6 days)
**Parallel:** STORY-E3-004 (1 day)

