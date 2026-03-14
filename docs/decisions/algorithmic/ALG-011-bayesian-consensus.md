# ALG-011: Bayesian Consensus

## OBSERVATION

The verification suite had 4 consensus algorithm enum values but only 2 implementations (Weighted Average, KS Adaptive Stability). `BAYESIAN_STUB` was an enum-only stub with no backing algorithm. Bayesian posterior updating is a well-established method for aggregating evidence under uncertainty, directly applicable to multi-evaluator consensus.

## PROBLEM

When evaluators provide scores with varying reliability, simple averaging treats all observations equally. The system lacked a consensus method that could incorporate prior beliefs and update them as evidence accumulates. This meant no principled way to express "we expect high quality" as a prior and let evaluator scores update that belief.

Affected: all Stage 7 consensus operations that need prior-informed aggregation.
Frequency: every verification run where prior knowledge exists about expected quality.

## SOLUTION

Beta-Binomial posterior updating with configurable priors.

**Algorithm:**
1. Accept prior Beta(alpha, beta) — default uniform Beta(1, 1)
2. Convert each evaluator score to a Bernoulli trial: score >= 0.5 → success
3. Update posterior: alpha' = alpha + successes, beta' = beta + failures
4. Consensus score = posterior mean = alpha' / (alpha' + beta')
5. Confidence = 1.0 - credible_interval_width (95% level via `scipy.stats.beta.ppf`)
6. Agreement classified by variance thresholds (same as other algorithms)

**Implementation:** `_verification/algorithms/bayesian_consensus.py`
- Class: `BayesianConsensus`
- Interface: `resolve(evaluations: list[ClaimEvaluation]) -> ConsensusResult`
- Dependencies: `scipy.stats.beta` for credible intervals

## JUSTIFICATION

**Why Beta-Binomial over other Bayesian approaches:**
- Conjugate prior makes posterior computation closed-form (no MCMC needed)
- Naturally handles the [0, 1] score domain
- Prior parameters are interpretable: alpha = "pseudo-successes", beta = "pseudo-failures"

**Why not Dirichlet-Multinomial:**
- Scores are binary (pass/fail threshold), not multi-category
- Added complexity with no benefit for the binary consensus use case

**Why scipy for credible intervals:**
- scipy.stats.beta.ppf provides exact quantile computation
- Already in project dependencies
- Pure Python alternatives would require numerical approximation

## REPRODUCIBILITY

```python
from ai_architect_mcp._verification.algorithms.bayesian_consensus import BayesianConsensus
from ai_architect_mcp._models.verification import ClaimEvaluation, Verdict
from uuid import uuid4

evals = [
    ClaimEvaluation(claim_id=uuid4(), evaluator_id=f"e{i}", score=s,
                    confidence=0.9, verdict=Verdict.PASS, reasoning="test")
    for i, s in enumerate([0.85, 0.90, 0.88, 0.82])
]
result = BayesianConsensus(prior_alpha=1.0, prior_beta=1.0).resolve(evals)
assert abs(result.consensus_score - 0.833333) < 1e-4
assert result.agreement_level.value == "high"
```

## VERIFICATION DATA

- 13 tests in `tests/test_verification/test_bayesian_consensus.py`
- Fixture: `tests/fixtures/consensus_bayesian.json`
- Posterior mean verified against manual calculation: 4 successes + Beta(1,1) prior → Beta(5,1) → mean 5/6 = 0.8333
- Confidence interval width decreases as sample size increases (verified in test_confidence_bounded)
- Strong prior (alpha=10) shifts consensus score upward vs uniform prior (verified in test_custom_prior)
