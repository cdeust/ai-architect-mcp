# Roadmap: Epic 3 — Consensus Algorithm Completion

**Epic:** E3-CONSENSUS
**Total Duration:** 2 weeks (2 sprints)
**Team Capacity:** 1–2 engineers
**Total Effort:** 10 SP
**Last Updated:** 2026-03-14

---

## Overview

This epic is delivered in 2 sprints over 2 weeks, with clear handoff milestones and sequential dependencies.

**Sprint Structure:**
- **Sprint 1 (Week 1):** Core algorithm implementation (6 SP)
- **Sprint 2 (Week 2):** Integration, documentation, verification (4 SP)

---

## Sprint 1: Core Algorithm Implementation (Week 1, 6 SP)

### Goals
- Implement Bayesian Consensus algorithm (3 SP)
- Implement Majority Voting algorithm (3 SP)
- Establish deterministic test infrastructure

### Deliverables
1. **BayesianConsensus class** (100% feature-complete)
2. **MajorityVoting class** (100% feature-complete)
3. **Unit tests** (>90% coverage for both algorithms)
4. **Deterministic fixtures** (JSON-based test data)

### Stories
- **STORY-E3-001** (3 SP): Implement Bayesian Consensus Algorithm
  - Task: Implement BayesianConsensus class with Beta prior
  - Task: Posterior calculation via Beta-Binomial conjugacy
  - Task: Credible interval calculation (scipy.stats.beta)
  - Task: Unit tests with deterministic fixtures
  - Task: Peer review

- **STORY-E3-002** (3 SP): Implement Majority Voting Consensus Algorithm
  - Task: Implement MajorityVoting class with threshold
  - Task: Vote aggregation and majority rule
  - Task: TieBreaker enum (3 strategies)
  - Task: Unit tests for all tie-breaking paths
  - Task: Peer review

### Schedule (Week 1)

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| Mon | Design review (both algorithms) | Team | Pending |
| Mon | Bayesian: Prior initialization + posterior calculation | Engineer 1 | Pending |
| Tue | Bayesian: Credible interval + unit tests | Engineer 1 | Pending |
| Wed | Majority Voting: Vote aggregation + tie-breakers | Engineer 2 | Pending |
| Wed | Majority Voting: Unit tests + edge cases | Engineer 2 | Pending |
| Thu | Bayesian: Peer review + refinements | Engineer 1 + 2 | Pending |
| Fri | Majority Voting: Peer review + refinements | Engineer 1 + 2 | Pending |
| Fri | Deterministic fixtures creation | Engineer 1 or 2 | Pending |

### Exit Criteria
- ✅ Both algorithms 100% feature-complete
- ✅ Unit test coverage >90% for each algorithm
- ✅ All tests passing on CI/CD
- ✅ Code review approved for both stories
- ✅ Performance benchmarks <5ms mean for 20 scores

---

## Sprint 2: Integration, Documentation, Verification (Week 2, 4 SP)

### Goals
- Integrate both algorithms into ConsensusAlgorithm enum and routing
- Create decision documents (ALG-011, ALG-012)
- Comprehensive test suite with routing verification
- Epic closure and documentation

### Deliverables
1. **ConsensusAlgorithm enum** (BAYESIAN_STUB → BAYESIAN, MAJORITY_VOTING_STUB → MAJORITY_VOTING)
2. **Consensus router** (dispatch logic for both new algorithms)
3. **ALG-011 document** (Bayesian Consensus design)
4. **ALG-012 document** (Majority Voting design)
5. **Integration tests** (routing verification, no breaking changes)
6. **Epic PRD validation** (cross-reference verification)

### Stories
- **STORY-E3-003** (1 SP): Integrate ConsensusAlgorithm Enum Routing
  - Task: Rename BAYESIAN_STUB → BAYESIAN
  - Task: Rename MAJORITY_VOTING_STUB → MAJORITY_VOTING
  - Task: Update consensus router with dispatch logic
  - Task: Integration tests (routing + enum dispatch)
  - Task: Verify no breaking changes to existing algorithms

- **STORY-E3-004** (1 SP): Write ALG Decision Documents
  - Task: ALG-011 — Bayesian Consensus design doc
  - Task: ALG-012 — Majority Voting design doc
  - Task: Cross-reference validation
  - Task: Peer review

- **STORY-E3-005** (2 SP): Comprehensive Test Suite with Deterministic Fixtures
  - Task: test_bayesian_consensus.py (unit tests, edge cases)
  - Task: test_majority_voting.py (unit tests, all tie-breakers)
  - Task: test_consensus_routing.py (enum dispatch, no breaking changes)
  - Task: pytest-cov (>90% coverage verification)
  - Task: pytest-benchmark (performance targets <5ms mean, <10ms p99)
  - Task: All tests passing on CI/CD

### Schedule (Week 2)

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| Mon | Enum renaming + router integration | Engineer 1 | Pending |
| Mon | Integration test design | Engineer 2 | Pending |
| Tue | Integration tests (routing, dispatch, compat) | Engineer 2 | Pending |
| Tue | ALG-011 document (Bayesian design) | Engineer 1 | Pending |
| Wed | ALG-012 document (Majority Voting design) | Engineer 1 | Pending |
| Wed | Final unit test refinement + fixtures | Engineer 2 | Pending |
| Thu | Comprehensive test run + coverage report | Engineer 1 + 2 | Pending |
| Thu | Performance benchmarking | Engineer 1 or 2 | Pending |
| Fri | Epic validation + cross-reference check | Team | Pending |
| Fri | Final code review + merge to main | Team | Pending |

### Exit Criteria
- ✅ Enum renamed (BAYESIAN, MAJORITY_VOTING)
- ✅ Router dispatch logic working for all 4 algorithms
- ✅ Integration tests passing (no breaking changes)
- ✅ ALG-011 and ALG-012 documents complete and reviewed
- ✅ Overall test coverage >90% for both algorithms
- ✅ Performance benchmarks met (<5ms mean, <10ms p99)
- ✅ All tests passing on CI/CD
- ✅ Epic PRD verified for consistency
- ✅ Code merged to main branch

---

## Dependency Graph

```
Sprint 1:
  STORY-E3-001 (3 SP: Bayesian implementation)
  STORY-E3-002 (3 SP: Majority Voting implementation)
                       ↓
Sprint 2:
  STORY-E3-003 (1 SP: Enum routing) ──┐
  STORY-E3-004 (1 SP: ALG docs)       ├─→ STORY-E3-005 (2 SP: Tests)
  (Parallel start, not blocked)        │
                                       ↓
                            Epic Complete ✓
```

**Critical Path:** STORY-E3-001 → STORY-E3-003 → STORY-E3-005
**Duration:** ~6 days (Mon-Sat)
**Parallel tracks:** STORY-E3-004 (docs, 1 day)

---

## Risk Mitigation Plan

| Risk | Impact | Likelihood | Mitigation | Timing |
|------|--------|-----------|-----------|--------|
| Bayesian math errors (posterior calc) | High | Medium | Peer review + scipy.stats validation | Sprint 1, Thu |
| Non-deterministic output (PRNG) | High | Low | Seeded RNG, deterministic fixtures | Sprint 1, Fri |
| Performance regression | Medium | Low | Benchmark sprint 1, profile sprint 2 | Sprint 2, Thu |
| Breaking changes to existing algos | High | Very Low | Integration tests, regression suite | Sprint 2, Wed |
| Documentation gaps | Low | Low | Peer review of ALG docs | Sprint 2, Thu |

---

## Success Metrics

### Quality Metrics
| Metric | Target | Method |
|--------|--------|--------|
| Code coverage (both algorithms) | >90% | pytest-cov |
| Test pass rate | 100% | CI/CD status |
| Code review approval | 100% | GitHub/bitbucket |
| Determinism | 100% | Fixture reproducibility tests |

### Performance Metrics
| Metric | Target | Method |
|--------|--------|--------|
| Bayesian compute time (20 scores) | <5ms mean, <10ms p99 | pytest-benchmark |
| Majority Voting compute time (20 scores) | <5ms mean, <10ms p99 | pytest-benchmark |

### Delivery Metrics
| Metric | Target |
|--------|--------|
| Sprint 1 velocity | 6 SP completed |
| Sprint 2 velocity | 4 SP completed |
| Total effort | 10 SP on-time |
| Burn-down | Linear (no blockers) |

---

## Communication & Milestones

### Sprint 1 Milestones
- **End of Day 1:** Design approved, both stories started
- **End of Day 3:** Bayesian algorithm complete + tests
- **End of Day 5:** Majority Voting algorithm complete + tests
- **End of Sprint (Fri):** Both algorithms feature-complete, >90% coverage

### Sprint 2 Milestones
- **End of Day 1:** Enum renaming + router integration
- **End of Day 3:** Integration tests passing, ALG documents started
- **End of Day 4:** ALG-011 and ALG-012 complete
- **End of Day 5:** Final test suite + benchmarks
- **End of Sprint (Fri):** Epic complete, merged to main, ready for release

### Weekly Sync-Ups
- **Monday 10:00 AM:** Sprint planning / progress check
- **Wednesday 2:00 PM:** Mid-sprint check-in
- **Friday 4:00 PM:** Sprint review + retrospective

---

## Team Capacity

### Recommended Team
- **Engineer 1:** Primary on Bayesian Consensus (STORY-E3-001) + integration (STORY-E3-003) + docs (STORY-E3-004)
- **Engineer 2:** Primary on Majority Voting (STORY-E3-002) + tests (STORY-E3-005)
- **Code Reviewer:** Senior engineer (peer reviews for both)

### Time Allocation
- **Sprint 1:** 30–40 hours per engineer (6 SP distributed)
- **Sprint 2:** 20–30 hours per engineer (4 SP distributed)
- **Total:** ~50–70 hours per engineer across both sprints

---

## Post-Epic Activities

After epic closure (Friday EOD, Week 2):
1. Merge to main branch (CI/CD verification)
2. Tag release candidate (v0.2.0-beta)
3. Update release notes with new algorithms
4. Plan downstream epics (if any consensus-dependent work)
5. Retrospective & lessons learned

---

## Appendix: Story Breakdown

### STORY-E3-001: Bayesian Consensus (3 SP)
- Code: BayesianConsensus class (150–200 lines)
- Tests: test_bayesian_consensus.py (200–300 lines)
- Docs: Docstrings in Google style

### STORY-E3-002: Majority Voting (3 SP)
- Code: MajorityVoting class + TieBreaker enum (150–200 lines)
- Tests: test_majority_voting.py (200–300 lines)
- Docs: Docstrings in Google style

### STORY-E3-003: Enum Routing (1 SP)
- Changes: `_models/consensus.py` enum (2 renames)
- Changes: `_verification/consensus_router.py` (routing logic, ~30 lines)
- Tests: test_consensus_routing.py (50–100 lines)

### STORY-E3-004: ALG Docs (1 SP)
- ALG-011: ~800–1000 words (design, rationale, use cases)
- ALG-012: ~800–1000 words (logic, tie-breaking, examples)
- Cross-references: Updated PRD links

### STORY-E3-005: Test Suite (2 SP)
- Unit tests: ~500–700 lines (Bayesian + Majority)
- Integration tests: ~150–200 lines (routing)
- Fixtures: ~300–500 lines (JSON deterministic test data)
- Benchmarks: ~100–150 lines (pytest-benchmark)

**Total Code:** ~2000–3000 lines (implementation + tests + docs)

