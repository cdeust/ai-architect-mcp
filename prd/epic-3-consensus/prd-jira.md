# JIRA Tickets: Epic 3 — Consensus Algorithm Completion

**Epic ID:** E3-CONSENSUS
**JIRA Project:** AIARCH
**Total Tickets:** 5
**Total SP:** 10
**Created:** 2026-03-14

---

## JIRA Ticket Summary

| Ticket ID | Title | Story | Type | SP | Assignee | Status |
|-----------|-------|-------|------|-----|----------|--------|
| AIARCH-1001 | Implement Bayesian Consensus Algorithm | STORY-E3-001 | Story | 3 | TBD | Backlog |
| AIARCH-1002 | Implement Majority Voting Consensus Algorithm | STORY-E3-002 | Story | 3 | TBD | Backlog |
| AIARCH-1003 | Integrate ConsensusAlgorithm Enum Routing | STORY-E3-003 | Story | 1 | TBD | Backlog |
| AIARCH-1004 | Write ALG Decision Documents (ALG-011, ALG-012) | STORY-E3-004 | Story | 1 | TBD | Backlog |
| AIARCH-1005 | Comprehensive Test Suite with Deterministic Fixtures | STORY-E3-005 | Story | 2 | TBD | Backlog |

---

## Detailed Ticket Definitions

### AIARCH-1001: Implement Bayesian Consensus Algorithm

**Ticket Type:** Story
**Epic:** E3-CONSENSUS
**Story Points:** 3
**Priority:** High
**Status:** Backlog
**Related Story:** STORY-E3-001

#### Description
Implement the Bayesian Consensus algorithm using Beta-Binomial conjugacy. This algorithm leverages Bayesian inference with configurable Beta priors to update beliefs based on observed agreement scores.

#### Acceptance Criteria
- [ ] BayesianConsensus class created in `_verification/algorithms/bayesian_consensus.py`
- [ ] Beta prior initialization (default α=2, β=2, customizable)
- [ ] Prior parameter validation (α > 0, β > 0)
- [ ] Posterior calculation via Beta-Binomial conjugacy
- [ ] Credible interval computation (95%, scipy.stats.beta)
- [ ] Consensus score as posterior mean (α' / (α' + β'))
- [ ] Confidence score from credible interval width
- [ ] Agreement level classification (variance-based)
- [ ] Error handling (empty input → ValueError)
- [ ] Unit tests with >90% coverage
- [ ] Deterministic fixtures for known inputs/outputs
- [ ] Docstrings (Google style)
- [ ] Type hints (100% coverage, mypy --strict)
- [ ] Code formatted with black
- [ ] Performance: <5ms mean for 20 scores
- [ ] Peer review approved

#### Tasks
- [ ] Create `bayesian_consensus.py` module
- [ ] Implement BayesianConsensus class with __init__ and compute() methods
- [ ] Implement _credible_interval() helper method
- [ ] Implement _agreement_level() helper method
- [ ] Write unit tests (test_bayesian_consensus.py)
- [ ] Create deterministic test fixtures
- [ ] Add docstrings and type hints
- [ ] Run pytest-cov (target >90%)
- [ ] Run pytest-benchmark (target <5ms mean)
- [ ] Code review

#### Dependencies
- Requires: scipy library (scipy.stats.beta)
- Requires: numpy
- Requires: ConsensusResult model (already exists)

#### Related Issues
- Related to: AIARCH-1003 (enum integration)
- Related to: AIARCH-1005 (test suite)
- Blocked by: None

#### Sprint
Sprint 1 (Week 1)

#### Estimate Breakdown
- Implementation: 2 SP
- Testing & debugging: 0.5 SP
- Code review & refinement: 0.5 SP

---

### AIARCH-1002: Implement Majority Voting Consensus Algorithm

**Ticket Type:** Story
**Epic:** E3-CONSENSUS
**Story Points:** 3
**Priority:** High
**Status:** Backlog
**Related Story:** STORY-E3-002

#### Description
Implement the Majority Voting consensus algorithm with configurable voting threshold and three tie-breaking strategies. This algorithm provides deterministic threshold-based consensus without probabilistic reasoning.

#### Acceptance Criteria
- [ ] MajorityVoting class created in `_verification/algorithms/majority_voting.py`
- [ ] TieBreaker enum (HIGHEST_CONFIDENCE, RANDOM_SEEDED, ESCALATE_TO_DEBATE)
- [ ] Voting threshold configuration (default 0.5, range (0, 1))
- [ ] Binary vote classification (score >= 0.5 → YES, else NO)
- [ ] Vote aggregation and majority rule logic
- [ ] Confidence calculation (margin / total)
- [ ] Agreement level classification (variance-based)
- [ ] HIGHEST_CONFIDENCE tie-breaking (deterministic, highest mean wins)
- [ ] RANDOM_SEEDED tie-breaking (deterministic PRNG, hash of scores)
- [ ] ESCALATE_TO_DEBATE tie-breaking (FLAG_FOR_REVIEW)
- [ ] Error handling (empty input, invalid threshold)
- [ ] Unit tests with >90% coverage, all tie-breakers tested
- [ ] Deterministic fixtures
- [ ] Docstrings (Google style)
- [ ] Type hints (100% coverage, mypy --strict)
- [ ] Code formatted with black
- [ ] Performance: <5ms mean for 20 scores
- [ ] Peer review approved

#### Tasks
- [ ] Create `majority_voting.py` module
- [ ] Implement TieBreaker enum
- [ ] Implement MajorityVoting class with __init__ and compute() methods
- [ ] Implement _resolve_tie() helper method
- [ ] Implement _agreement_level() helper method
- [ ] Write unit tests (test_majority_voting.py)
- [ ] Test all three tie-breaking strategies
- [ ] Test edge cases (single vote, all same, empty)
- [ ] Create deterministic test fixtures
- [ ] Add docstrings and type hints
- [ ] Run pytest-cov (target >90%)
- [ ] Run pytest-benchmark (target <5ms mean)
- [ ] Code review

#### Dependencies
- Requires: numpy
- Requires: hashlib (for seeded RNG)
- Requires: ConsensusResult model (already exists)

#### Related Issues
- Related to: AIARCH-1003 (enum integration)
- Related to: AIARCH-1005 (test suite)
- Blocked by: None

#### Sprint
Sprint 1 (Week 1)

#### Estimate Breakdown
- Implementation: 2 SP
- Testing & debugging: 0.5 SP
- Code review & refinement: 0.5 SP

---

### AIARCH-1003: Integrate ConsensusAlgorithm Enum Routing

**Ticket Type:** Story
**Epic:** E3-CONSENSUS
**Story Points:** 1
**Priority:** High
**Status:** Backlog
**Related Story:** STORY-E3-003

#### Description
Integrate both new consensus algorithms (Bayesian and Majority Voting) into the ConsensusAlgorithm enum and routing engine. This includes renaming stubs and updating the dispatch logic.

#### Acceptance Criteria
- [ ] Enum value BAYESIAN_STUB renamed to BAYESIAN in `_models/consensus.py`
- [ ] Enum value MAJORITY_VOTING_STUB renamed to MAJORITY_VOTING
- [ ] All references to old enum values updated (no orphaned references)
- [ ] ConsensusRouter updated with dispatch logic for BAYESIAN
- [ ] ConsensusRouter updated with dispatch logic for MAJORITY_VOTING
- [ ] Router accepts optional config dict for algorithm initialization
- [ ] Both new algorithms routable via enum
- [ ] All four algorithms (WEIGHTED_AVERAGE, ADAPTIVE_STABILITY, BAYESIAN, MAJORITY_VOTING) routable
- [ ] Integration tests verify routing (test_consensus_routing.py)
- [ ] No breaking changes to existing code
- [ ] All existing tests pass (regression verification)
- [ ] Code review approved

#### Tasks
- [ ] Update ConsensusAlgorithm enum (rename BAYESIAN_STUB → BAYESIAN)
- [ ] Update ConsensusAlgorithm enum (rename MAJORITY_VOTING_STUB → MAJORITY_VOTING)
- [ ] Search codebase for all references to old enum values
- [ ] Update all references
- [ ] Update ConsensusRouter dispatch logic
- [ ] Add routing for BAYESIAN (instantiate BayesianConsensus)
- [ ] Add routing for MAJORITY_VOTING (instantiate MajorityVoting)
- [ ] Write integration tests (routing, no breaking changes)
- [ ] Run full test suite (regression verification)
- [ ] Code review

#### Dependencies
- Blocked by: AIARCH-1001 (Bayesian implementation)
- Blocked by: AIARCH-1002 (Majority Voting implementation)

#### Related Issues
- Related to: AIARCH-1005 (test suite)

#### Sprint
Sprint 2 (Week 2)

#### Estimate Breakdown
- Enum updates: 0.3 SP
- Router updates: 0.4 SP
- Testing & verification: 0.3 SP

---

### AIARCH-1004: Write ALG Decision Documents (ALG-011, ALG-012)

**Ticket Type:** Story
**Epic:** E3-CONSENSUS
**Story Points:** 1
**Priority:** Medium
**Status:** Backlog
**Related Story:** STORY-E3-004

#### Description
Create two algorithm decision documents (ALG-011 for Bayesian Consensus, ALG-012 for Majority Voting) that document the design rationale, trade-offs, use cases, and limitations.

#### Acceptance Criteria
- [ ] ALG-011 document created at `_architecture/alg/ALG-011-bayesian-consensus.md`
- [ ] ALG-011 includes: problem statement, algorithm design, Beta prior rationale, use cases, trade-offs, limitations, references, pseudocode
- [ ] ALG-011 references scipy.stats.beta and conjugacy
- [ ] ALG-012 document created at `_architecture/alg/ALG-012-majority-voting.md`
- [ ] ALG-012 includes: problem statement, majority voting logic, three tie-breaking strategies, use cases, examples, trade-offs, limitations
- [ ] Both documents cross-linked (ALG-011 ↔ ALG-012)
- [ ] ALG documents linked in epic PRD (prd-overview.md)
- [ ] Both documents reviewed by team
- [ ] Code references (class names, file paths) verified as correct
- [ ] Documents follow AI Architect documentation style guide

#### Tasks
- [ ] Create ALG-011-bayesian-consensus.md template
- [ ] Write ALG-011 content (design, rationale, use cases)
- [ ] Add pseudocode to ALG-011
- [ ] Create ALG-012-majority-voting.md template
- [ ] Write ALG-012 content (voting logic, tie-breaking)
- [ ] Add examples to ALG-012
- [ ] Add cross-references (ALG-011 ↔ ALG-012)
- [ ] Update prd-overview.md with links to ALG docs
- [ ] Peer review

#### Dependencies
- Blocked by: AIARCH-1001 (Bayesian implementation)
- Blocked by: AIARCH-1002 (Majority Voting implementation)

#### Related Issues
- Related to: Epic PRD (prd-overview.md)

#### Sprint
Sprint 2 (Week 2)

#### Estimate Breakdown
- ALG-011 writing: 0.4 SP
- ALG-012 writing: 0.4 SP
- Review & refinement: 0.2 SP

---

### AIARCH-1005: Comprehensive Test Suite with Deterministic Fixtures

**Ticket Type:** Story
**Epic:** E3-CONSENSUS
**Story Points:** 2
**Priority:** High
**Status:** Backlog
**Related Story:** STORY-E3-005

#### Description
Create a comprehensive test suite covering both new algorithms with deterministic fixtures. This includes unit tests, integration tests, performance benchmarks, and fixture data in JSON format.

#### Acceptance Criteria
- [ ] test_bayesian_consensus.py written with >90% coverage
- [ ] Bayesian tests: prior init, posterior calculation, credible intervals, edge cases, error handling
- [ ] test_majority_voting.py written with >90% coverage
- [ ] Majority Voting tests: vote aggregation, threshold rules, all tie-breakers, edge cases
- [ ] test_consensus_routing.py written for integration testing
- [ ] Routing tests: enum dispatch, all 4 algorithms routable, no breaking changes
- [ ] Deterministic fixtures created (fixtures/consensus_test_data.json)
- [ ] Fixture data format: score arrays, expected results, tie-breaking scenarios
- [ ] All tests passing on CI/CD
- [ ] pytest-cov reports >90% coverage for both algorithms
- [ ] pytest-benchmark reports performance: <5ms mean, <10ms p99 (20 scores)
- [ ] Bit-for-bit output reproducibility verified (identical inputs → identical outputs)
- [ ] Code review approved

#### Tasks
- [ ] Create test_bayesian_consensus.py
- [ ] Write Bayesian unit tests (prior, posterior, credible intervals, edge cases)
- [ ] Create test_majority_voting.py
- [ ] Write Majority Voting unit tests (voting, tie-breaking, edge cases)
- [ ] Create test_consensus_routing.py
- [ ] Write integration tests (routing, no breaking changes)
- [ ] Create fixtures/consensus_test_data.json
- [ ] Add deterministic fixture data (Bayesian + Majority)
- [ ] Run pytest-cov (verify >90% coverage)
- [ ] Run pytest-benchmark (performance targets)
- [ ] Verify determinism (run tests multiple times, identical output)
- [ ] Code review

#### Dependencies
- Blocked by: AIARCH-1001 (Bayesian implementation)
- Blocked by: AIARCH-1002 (Majority Voting implementation)
- Blocked by: AIARCH-1003 (routing integration)

#### Related Issues
- Related to: AIARCH-1001, AIARCH-1002, AIARCH-1003

#### Sprint
Sprint 2 (Week 2)

#### Estimate Breakdown
- Unit tests (Bayesian): 0.6 SP
- Unit tests (Majority Voting): 0.6 SP
- Integration tests: 0.4 SP
- Fixtures + benchmarks: 0.4 SP

---

## JIRA CSV Export

```csv
Ticket ID,Title,Epic,Story,Type,Story Points,Priority,Assignee,Status,Sprint,Dependencies
AIARCH-1001,Implement Bayesian Consensus Algorithm,E3-CONSENSUS,STORY-E3-001,Story,3,High,TBD,Backlog,Sprint 1,None
AIARCH-1002,Implement Majority Voting Consensus Algorithm,E3-CONSENSUS,STORY-E3-002,Story,3,High,TBD,Backlog,Sprint 1,None
AIARCH-1003,Integrate ConsensusAlgorithm Enum Routing,E3-CONSENSUS,STORY-E3-003,Story,1,High,TBD,Backlog,Sprint 2,"AIARCH-1001,AIARCH-1002"
AIARCH-1004,Write ALG Decision Documents (ALG-011 ALG-012),E3-CONSENSUS,STORY-E3-004,Story,1,Medium,TBD,Backlog,Sprint 2,"AIARCH-1001,AIARCH-1002"
AIARCH-1005,Comprehensive Test Suite with Deterministic Fixtures,E3-CONSENSUS,STORY-E3-005,Story,2,High,TBD,Backlog,Sprint 2,"AIARCH-1001,AIARCH-1002,AIARCH-1003"
```

---

## Dependency Map

```
Sprint 1:
  AIARCH-1001 (Bayesian) ──┐
  AIARCH-1002 (Majority)───┤
                           ├─→ AIARCH-1003 (Routing) ─┐
                           │                          ├─→ AIARCH-1005 (Tests)
  AIARCH-1004 (ALG Docs) ──┤                          │
  (Parallel)               └──────────────────────────┘

No circular dependencies.
Critical path: AIARCH-1001 → AIARCH-1003 → AIARCH-1005 (6–7 days)
```

---

## Estimation Justification

| Ticket | SP | Justification |
|--------|-----|---------------|
| AIARCH-1001 | 3 | ~200 lines code, ~300 lines tests, Beta distribution math, deterministic fixtures |
| AIARCH-1002 | 3 | ~200 lines code, ~300 lines tests, three tie-breaking paths, edge cases |
| AIARCH-1003 | 1 | 2 enum renames, ~30 lines routing logic, integration tests (~100 lines) |
| AIARCH-1004 | 1 | Two ALG documents (~800 words each), cross-references, review |
| AIARCH-1005 | 2 | ~500 lines tests, ~400 lines fixtures, coverage + benchmark verification |
| **Total** | **10** | Fibonacci sequence, consistent with epic size S (5–8 SP) |

---

## Ticket Relationships

### Blocking Relationships
- AIARCH-1003 blocks on: AIARCH-1001, AIARCH-1002
- AIARCH-1004 blocks on: AIARCH-1001, AIARCH-1002
- AIARCH-1005 blocks on: AIARCH-1001, AIARCH-1002, AIARCH-1003

### Related Relationships
- AIARCH-1001 related to: AIARCH-1003 (routing), AIARCH-1005 (tests)
- AIARCH-1002 related to: AIARCH-1003 (routing), AIARCH-1005 (tests)
- AIARCH-1003 related to: AIARCH-1005 (integration tests)
- AIARCH-1004 related to: Epic PRD, AIARCH-1001, AIARCH-1002

---

## Definition of Done (Per Ticket)

Each ticket is complete when:
1. ✅ All acceptance criteria met
2. ✅ Code written, formatted (black), and linted (pylint >8.5)
3. ✅ Type hints 100% (mypy --strict pass)
4. ✅ Unit tests >90% coverage
5. ✅ Docstrings (Google style)
6. ✅ Peer review approved
7. ✅ Merged to main branch
8. ✅ CI/CD passing (all checks)

