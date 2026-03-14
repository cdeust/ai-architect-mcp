# Requirements: Epic 3 — Consensus Algorithm Completion

**Epic:** E3-CONSENSUS
**Last Updated:** 2026-03-14
**Owner:** AI Architect Core Team

---

## Functional Requirements

### FR-E3-001: Bayesian Consensus — Beta Prior Definition
**Description:** Implement configurable Beta distribution prior with α (shape1) and β (shape2) parameters.
**Acceptance Criteria:**
- Prior is stored in BayesianConsensus class initialization
- Default prior: α=2, β=2 (weakly informative)
- Prior can be overridden via constructor or config
- Prior values must be positive (α > 0, β > 0)

**Source:** STORY-E3-001
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-002: Bayesian Posterior Calculation
**Description:** Calculate posterior Beta distribution using Beta-Binomial conjugacy.
**Acceptance Criteria:**
- Input: array of scores [0, 1], threshold (default 0.5)
- Count successes: scores >= threshold
- Count failures: scores < threshold
- Posterior α' = α_prior + successes
- Posterior β' = β_prior + failures
- Return posterior parameters and confidence score

**Source:** STORY-E3-001
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-003: Bayesian Credible Interval Calculation
**Description:** Compute 95% credible interval from posterior distribution.
**Acceptance Criteria:**
- Use scipy.stats.beta.ppf() for quantile calculation
- Credible interval: [2.5th percentile, 97.5th percentile]
- Return tuple: (lower, upper)
- Handle edge cases: uniform posterior (α'=1, β'=1)

**Source:** STORY-E3-001
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-004: Bayesian Consensus Score Computation
**Description:** Return posterior mean as consensus score via compute() method.
**Acceptance Criteria:**
- Method signature: `async def compute(scores: list[float]) -> ConsensusResult`
- Consensus score = posterior mean = α'/(α'+β')
- Confidence score derived from credible interval width
- Return full ConsensusResult with algorithm, consensus_score, consensus_confidence
- Handle empty input: raise ValueError

**Source:** STORY-E3-001
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-005: Majority Voting — Threshold Configuration
**Description:** Implement configurable voting threshold for majority consensus.
**Acceptance Criteria:**
- Default threshold: 0.5 (standard majority)
- Threshold range: (0.0, 1.0), exclusive
- Threshold stored in MajorityVoting class initialization
- Threshold determines: agree if (count_above_threshold / total) >= threshold_level

**Source:** STORY-E3-002
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-006: Majority Voting — Vote Aggregation
**Description:** Count votes and determine majority decision.
**Acceptance Criteria:**
- Input: array of scores [0, 1]
- Score interpretation: >= 0.5 = YES, < 0.5 = NO (binary voting)
- Count: vote_yes, vote_no
- Majority rule: if vote_yes / total >= threshold, consensus = ACCEPT (1.0), else REJECT (0.0)
- Handle tie: (vote_yes == vote_no) → apply tie-breaker

**Source:** STORY-E3-002
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-007: Majority Voting — Tie-Breaking Strategies
**Description:** Implement three tie-breaking strategies when votes are split 50-50.
**Acceptance Criteria:**
- **HIGHEST_CONFIDENCE:** Pick vote with highest mean confidence, deterministic
- **RANDOM_SEEDED:** Use seeded RNG (seed = hash of input), deterministic
- **ESCALATE_TO_DEBATE:** Return FLAG_FOR_REVIEW, defer to human review
- Tie-breaker enum stored in MajorityVoting class
- Default: HIGHEST_CONFIDENCE

**Source:** STORY-E3-002
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-008: Majority Voting Consensus Computation
**Description:** Return majority decision via compute() method.
**Acceptance Criteria:**
- Method signature: `async def compute(scores: list[float]) -> ConsensusResult`
- Return ConsensusResult with algorithm=MAJORITY_VOTING
- consensus_score = 1.0 (ACCEPT) or 0.0 (REJECT) or 0.5 (tied, awaiting tie-breaker)
- consensus_confidence = vote margin / total votes
- Handle empty input: raise ValueError
- Handle single vote: that vote wins (confidence=1.0)

**Source:** STORY-E3-002
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-009: ConsensusAlgorithm Enum Integration
**Description:** Integrate both algorithms into ConsensusAlgorithm enum routing.
**Acceptance Criteria:**
- Rename BAYESIAN_STUB → BAYESIAN in ConsensusAlgorithm enum
- Rename MAJORITY_VOTING_STUB → MAJORITY_VOTING in ConsensusAlgorithm enum
- Router maps enum values to algorithm instances
- Both algorithms are instantiable and callable via router
- Existing algorithms (WEIGHTED_AVERAGE, ADAPTIVE_STABILITY) unchanged
- No breaking changes to existing code

**Source:** STORY-E3-003
**Priority:** P0
**Epic:** E3-CONSENSUS

---

### FR-E3-010: ALG Decision Documents
**Description:** Create ALG-011 (Bayesian Consensus) and ALG-012 (Majority Voting) decision docs.
**Acceptance Criteria:**
- ALG-011 covers: algorithm design, Beta prior rationale, use cases, trade-offs
- ALG-012 covers: majority voting logic, tie-breaking strategies, use cases, examples
- Both in markdown format, stored in `_architecture/alg/` directory
- Each includes: problem statement, solution, assumptions, limitations, references
- Cross-linked in epic PRD

**Source:** STORY-E3-004
**Priority:** P0
**Epic:** E3-CONSENSUS

---

## Non-Functional Requirements

### NFR-E3-001: Performance — Computation Time
**Requirement:** Both algorithms must compute consensus in <10ms for 20 input scores.
**Measurement:** Benchmark with `pytest-benchmark` or `timeit`
**Target:** Mean <5ms, p99 <10ms
**Priority:** P1

---

### NFR-E3-002: Deterministic Output
**Requirement:** Identical inputs always produce identical outputs (bit-for-bit reproducibility).
**Measurement:** Deterministic fixtures, seeded RNG, no float rounding errors
**Target:** 100% determinism across runs
**Priority:** P0

---

### NFR-E3-003: Numerical Stability
**Requirement:** Avoid overflow/underflow in Beta distribution calculations.
**Measurement:** scipy.stats.beta handles log-domain internally; verify no NaN/Inf
**Target:** Zero numerical errors in credible interval calculation
**Priority:** P1

---

### NFR-E3-004: Code Quality
**Requirement:** All code follows AI Architect style guide, type hints, docstrings.
**Measurement:** pylint, mypy, black formatting
**Target:** Lint score >8.5/10, type coverage 100%
**Priority:** P1

---

### NFR-E3-005: Test Coverage
**Requirement:** >90% code coverage for both algorithms.
**Measurement:** pytest-cov
**Target:** ≥90% line coverage, all edge cases tested
**Priority:** P1

---

## Requirements Traceability Matrix

| FR ID | Title | Story | Priority | Status |
|-------|-------|-------|----------|--------|
| FR-E3-001 | Beta Prior Definition | STORY-E3-001 | P0 | Pending |
| FR-E3-002 | Posterior Calculation | STORY-E3-001 | P0 | Pending |
| FR-E3-003 | Credible Interval Calculation | STORY-E3-001 | P0 | Pending |
| FR-E3-004 | Bayesian Consensus Score Computation | STORY-E3-001 | P0 | Pending |
| FR-E3-005 | Majority Voting Threshold Config | STORY-E3-002 | P0 | Pending |
| FR-E3-006 | Vote Aggregation | STORY-E3-002 | P0 | Pending |
| FR-E3-007 | Tie-Breaking Strategies | STORY-E3-002 | P0 | Pending |
| FR-E3-008 | Majority Voting Consensus Computation | STORY-E3-002 | P0 | Pending |
| FR-E3-009 | ConsensusAlgorithm Enum Integration | STORY-E3-003 | P0 | Pending |
| FR-E3-010 | ALG Decision Documents | STORY-E3-004 | P0 | Pending |

---

## Glossary

- **Beta Distribution:** A continuous probability distribution conjugate to the Binomial, used for modeling probabilities
- **Posterior:** Updated belief after observing data
- **Credible Interval:** Range containing the parameter with 95% probability (Bayesian analog to confidence interval)
- **Tie-Breaking:** Strategy to resolve 50-50 votes in Majority Voting
- **Deterministic:** Output is reproducible given the same input and random seed

