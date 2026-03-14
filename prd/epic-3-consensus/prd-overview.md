# PRD: Epic 3 — Consensus Algorithm Completion
## AI Architect Project

**Epic ID:** E3-CONSENSUS
**Status:** Ready for Development
**Priority:** High
**Size:** S (5–8 SP) → 10 SP allocated
**Duration:** 1–2 weeks (2 sprints)
**Owner:** AI Architect Core Team
**Created:** 2026-03-14

---

## Executive Summary

AI Architect currently has two consensus algorithm stubs in the `ConsensusAlgorithm` enum that require full implementation:
1. **Bayesian Consensus** (`BAYESIAN_STUB` → `BAYESIAN`)
2. **Majority Voting** (`MAJORITY_VOTING_STUB` → `MAJORITY_VOTING`)

This epic completes both algorithms to enable probabilistic Bayesian consensus using Beta-Binomial updating and deterministic majority-based consensus with tie-breaking strategies. These are complementary to existing algorithms (Weighted Average, Adaptive Stability).

**Deliverables:**
- 2 fully implemented consensus algorithm classes
- Integration with ConsensusAlgorithm enum and routing engine
- 2 decision documents (ALG-011, ALG-012)
- Comprehensive test suite with deterministic fixtures
- Zero breaking changes to existing algorithms

---

## Problem Statement

Currently, `BAYESIAN_STUB` and `MAJORITY_VOTING_STUB` are placeholder entries in the ConsensusAlgorithm enum. Teams cannot leverage:
- **Bayesian Consensus:** Principled prior updating for scenarios with limited samples or domain knowledge
- **Majority Voting:** Simple threshold-based consensus for categorical or binary decisions with tie-breaking

Without these implementations, the verification engine has gaps in consensus methodology coverage.

---

## Solution Overview

### Bayesian Consensus Algorithm
- **Prior:** Beta distribution with configurable α (shape1) and β (shape2) parameters
- **Update:** Posterior calculation via Beta-Binomial conjugacy
- **Output:** Posterior mean, credible intervals, confidence scores
- **Use Case:** Scenarios requiring probabilistic reasoning with prior beliefs

### Majority Voting Algorithm
- **Voting Model:** Threshold-based agreement counting
- **Tie-Breaking:** Three strategies (highest confidence, random seeded, escalate to debate)
- **Output:** Majority decision, confidence level based on margin
- **Use Case:** Deterministic consensus when probabilistic ranking is not needed

---

## Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Both algorithms compute in <10ms (20 input scores) | <10ms | Pending |
| Deterministic output (identical inputs → identical outputs) | 100% | Pending |
| Test coverage >90% | >90% | Pending |
| Zero impact on existing algorithms | Pass | Pending |
| Decision documents (ALG-011, ALG-012) | Complete | Pending |
| Integration verified via routing tests | Pass | Pending |

---

## Timeline

| Sprint | Dates | Focus | SP |
|--------|-------|-------|-----|
| 1 | Week 1 | Core algorithms (Bayesian, Majority Voting) | 6 |
| 2 | Week 2 | Integration, docs, tests, verification | 4 |

**Total Effort:** 10 SP
**Team:** 1–2 engineers

---

## Scope

### In Scope
- Bayesian Consensus algorithm implementation
- Majority Voting algorithm implementation
- Integration with ConsensusAlgorithm enum routing
- Deterministic test suite
- ALG-011 and ALG-012 decision documents
- Performance benchmarks

### Out of Scope
- UI/UX enhancements
- Historical consensus data migration
- Third-party consensus libraries
- Real-time streaming consensus

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Bayesian math errors (posterior calc) | High | Medium | Peer review + scipy validation tests |
| Non-deterministic output (PRNG issues) | High | Low | Seeded RNG in tie-breaking, fixtures |
| Performance regression | Medium | Low | Benchmark existing algos, profile new ones |

---

## Dependencies

- ✅ Existing `ConsensusResult` model (no changes needed)
- ✅ Existing `AgreementLevel` enum
- ✅ Existing `DisagreementResolution` enum
- ✅ scipy library (Beta distribution)
- ✅ pytest, pytest-asyncio (testing)

**No external dependencies on other epics.**

---

## Next Steps

1. Review and approve PRD
2. Create JIRA tickets (5 total)
3. Assign to sprint 1
4. Begin development on Bayesian and Majority Voting implementations
5. Weekly sync-ups on progress

---

## Appendix: Related Documents

- `prd-requirements.md` — Functional and non-functional requirements (FR-E3-001 through FR-E3-010)
- `prd-user-stories.md` — 5 user stories with acceptance criteria
- `prd-technical.md` — Full implementation code and architecture
- `prd-acceptance.md` — Detailed acceptance criteria (AC-E3-001 through AC-E3-015)
- `prd-roadmap.md` — Sprint breakdown and timeline
- `prd-jira.md` — JIRA ticket definitions and CSV export
- `prd-tests.md` — Full pytest code and fixture data
- `prd-verification.md` — Structural cross-reference validation

