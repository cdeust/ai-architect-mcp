# ALG-012: Majority Voting Consensus

## OBSERVATION

The verification suite lacked a simple, interpretable consensus method based on majority decision. `MAJORITY_VOTING_STUB` was an enum-only stub. Many verification scenarios need a binary accept/reject outcome where each evaluator casts a vote, and the majority determines the result.

## PROBLEM

Weighted averaging and Bayesian methods produce continuous scores that require interpretation thresholds. In some verification contexts (e.g., "does this PR meet acceptance criteria?"), a direct majority vote is more appropriate and interpretable. The system had no mechanism for binary voting with configurable tie-breaking.

Affected: Stage 7 verification decisions requiring binary outcomes.
Frequency: every verification run where binary consensus is preferred.

## SOLUTION

Threshold-based majority voting with three tie-breaking strategies.

**Algorithm:**
1. Each evaluator score >= voting_threshold (default 0.5) → YES vote, else NO
2. YES ratio >= acceptance_ratio → ACCEPT, else REJECT
3. Confidence = margin of victory = |yes_count - no_count| / total
4. Agreement: margin >= 0.8 → HIGH, >= 0.2 → MEDIUM, else LOW
5. On exact tie, apply configured tie-breaker

**Tie-breaking strategies (TieBreaker enum):**
- `HIGHEST_CONFIDENCE`: average confidence of YES vs NO voters (deterministic)
- `RANDOM_SEEDED`: SHA-256 hash of sorted scores → deterministic but pseudo-random
- `ESCALATE_TO_DEBATE`: flag for multi-agent debate review (sets converged=False)

**Implementation:** `_verification/algorithms/majority_voting.py`
- Class: `MajorityVotingConsensus`
- Interface: `resolve(evaluations: list[ClaimEvaluation]) -> ConsensusResult`
- Dependencies: `hashlib` (stdlib) for seeded RNG

## JUSTIFICATION

**Why margin-based confidence instead of vote ratio:**
- Margin directly reflects decision certainty: 5-0 vote = margin 1.0, 3-2 = margin 0.2
- More interpretable than raw ratio for binary decisions

**Why SHA-256 for seeded RNG:**
- Deterministic given same inputs (reproducible)
- No numpy/random dependency needed
- Uniform distribution of first hex digit provides unbiased coin flip

**Why not Condorcet ranking:**
- Evaluators score a single claim, not rank multiple claims
- Condorcet's Jury Theorem motivates majority voting but pairwise ranking doesn't apply

**Why three tie-breakers instead of one:**
- Different verification contexts have different requirements
- ESCALATE_TO_DEBATE enables integration with the existing Multi-Agent Debate algorithm (ALG-006)

## REPRODUCIBILITY

```python
from ai_architect_mcp._verification.algorithms.majority_voting import MajorityVotingConsensus
from ai_architect_mcp._models.consensus import TieBreaker
from ai_architect_mcp._models.verification import ClaimEvaluation, Verdict
from uuid import uuid4

evals = [
    ClaimEvaluation(claim_id=uuid4(), evaluator_id=f"e{i}", score=s,
                    confidence=0.9, verdict=Verdict.PASS if s >= 0.5 else Verdict.FAIL,
                    reasoning="test")
    for i, s in enumerate([0.8, 0.7, 0.3, 0.9, 0.6])
]
result = MajorityVotingConsensus(voting_threshold=0.5).resolve(evals)
assert result.consensus_score == 0.8  # 4/5 YES
assert result.consensus_confidence == 0.6  # margin = |4-1|/5
```

## VERIFICATION DATA

- 14 tests in `tests/test_verification/test_majority_voting.py`
- Fixture: `tests/fixtures/consensus_majority_voting.json`
- Tie-breaking determinism verified: 5 consecutive runs with RANDOM_SEEDED produce identical results
- ESCALATE_TO_DEBATE correctly sets converged=False and resolution=RE_EVALUATE
- Custom voting_threshold changes classification (strict 0.8 vs lenient 0.5 produce different resolutions)
- Unanimous vote produces HIGH agreement and margin 1.0
