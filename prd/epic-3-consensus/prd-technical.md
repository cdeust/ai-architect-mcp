# Technical Specification: Epic 3 — Consensus Algorithm Completion

**Epic:** E3-CONSENSUS
**Version:** 1.0
**Last Updated:** 2026-03-14

---

## Architecture Overview

### High-Level Design

The consensus verification engine currently supports two algorithms:
1. **WEIGHTED_AVERAGE** — Simple linear average
2. **ADAPTIVE_STABILITY** — KS stability-based consensus

This epic adds two more:
3. **BAYESIAN** (was BAYESIAN_STUB) — Probabilistic Bayesian inference using Beta priors
4. **MAJORITY_VOTING** (was MAJORITY_VOTING_STUB) — Deterministic threshold-based voting

All algorithms implement the `ConsensusAlgorithm` interface and return `ConsensusResult` objects.

---

## Algorithm 1: Bayesian Consensus

### Design Rationale
- **Problem:** Some scenarios have limited samples or strong prior beliefs (e.g., "historical data shows 70% consensus")
- **Solution:** Use Bayesian inference with Beta-Binomial conjugacy to update beliefs efficiently
- **Benefit:** Principled probabilistic reasoning, natural credible intervals, interpretable confidence

### Mathematical Foundation

**Prior:** Beta(α, β)
- Default: α=2, β=2 (weakly informative, symmetric)
- Represents prior belief about probability of agreement

**Likelihood:** Binomial (successes | n trials, probability p)
- Successes: scores >= threshold
- Failures: scores < threshold

**Posterior:** Beta(α', β') via conjugacy
- α' = α + successes
- β' = β + failures
- Closed-form solution, no MCMC needed

**Posterior Mean (consensus_score):** E[p] = α' / (α' + β')

**Credible Interval (95%):**
- Lower: Beta(α', β').ppf(0.025)
- Upper: Beta(α', β').ppf(0.975)
- Width inversely related to confidence

### Implementation Code

```python
from typing import Optional, Tuple
import numpy as np
from scipy import stats
from enum import Enum
from dataclasses import dataclass
from ._models.consensus import (
    ConsensusAlgorithm,
    ConsensusResult,
    AgreementLevel,
    DisagreementResolution,
)


class BayesianConsensus:
    """
    Bayesian consensus using Beta-Binomial conjugacy.

    Prior is a Beta distribution; posterior is updated via observed successes/failures.
    Returns consensus score as posterior mean and confidence from credible interval width.
    """

    def __init__(
        self,
        alpha_prior: float = 2.0,
        beta_prior: float = 2.0,
        threshold: float = 0.5,
    ):
        """
        Initialize Bayesian consensus.

        Args:
            alpha_prior: Shape parameter α for Beta prior (default 2.0)
            beta_prior: Shape parameter β for Beta prior (default 2.0)
            threshold: Score threshold for success classification (default 0.5)

        Raises:
            ValueError: If alpha_prior <= 0 or beta_prior <= 0
        """
        if alpha_prior <= 0 or beta_prior <= 0:
            raise ValueError("Prior parameters must be positive (α > 0, β > 0)")

        self.alpha_prior = alpha_prior
        self.beta_prior = beta_prior
        self.threshold = threshold

    async def compute(
        self,
        scores: list[float],
        **kwargs
    ) -> ConsensusResult:
        """
        Compute Bayesian consensus from input scores.

        Args:
            scores: List of scores in [0, 1]
            **kwargs: Additional parameters (ignored for compatibility)

        Returns:
            ConsensusResult with posterior mean, confidence, credible interval

        Raises:
            ValueError: If scores is empty
        """
        if not scores:
            raise ValueError("Scores array cannot be empty")

        scores_array = np.array(scores, dtype=np.float64)

        # Count successes and failures
        successes = np.sum(scores_array >= self.threshold)
        failures = len(scores_array) - successes

        # Posterior parameters (Beta-Binomial conjugacy)
        alpha_posterior = self.alpha_prior + successes
        beta_posterior = self.beta_prior + failures

        # Consensus score: posterior mean
        consensus_score = float(alpha_posterior / (alpha_posterior + beta_posterior))

        # Credible interval (95%)
        lower, upper = self._credible_interval(alpha_posterior, beta_posterior)

        # Confidence: inverse of credible interval width
        interval_width = upper - lower
        consensus_confidence = float(1.0 - interval_width)  # Clamp to [0, 1]
        consensus_confidence = max(0.0, min(1.0, consensus_confidence))

        # Agreement level based on variance
        variance = np.var(scores_array)
        agreement_level = self._agreement_level(variance)

        # Resolution
        resolution = DisagreementResolution.ACCEPT
        if agreement_level == AgreementLevel.LOW:
            resolution = DisagreementResolution.FLAG_FOR_REVIEW

        return ConsensusResult(
            algorithm=ConsensusAlgorithm.BAYESIAN,
            consensus_score=consensus_score,
            consensus_confidence=consensus_confidence,
            agreement_level=agreement_level,
            resolution=resolution,
            individual_scores=scores,
            iteration_count=1,
            converged=True,
        )

    def _credible_interval(self, alpha: float, beta: float) -> Tuple[float, float]:
        """
        Calculate 95% credible interval from Beta posterior.

        Args:
            alpha: Posterior shape parameter α
            beta: Posterior shape parameter β

        Returns:
            Tuple (lower, upper) percentiles
        """
        lower = float(stats.beta.ppf(0.025, alpha, beta))
        upper = float(stats.beta.ppf(0.975, alpha, beta))
        return (lower, upper)

    @staticmethod
    def _agreement_level(variance: float) -> AgreementLevel:
        """
        Classify agreement level based on score variance.

        Args:
            variance: Variance of input scores

        Returns:
            AgreementLevel enum (HIGH, MEDIUM, LOW)
        """
        if variance < 0.05:
            return AgreementLevel.HIGH
        elif variance < 0.15:
            return AgreementLevel.MEDIUM
        else:
            return AgreementLevel.LOW
```

---

## Algorithm 2: Majority Voting

### Design Rationale
- **Problem:** Simple, deterministic consensus needed when probabilistic ranking is unnecessary
- **Solution:** Count votes above/below threshold; majority wins with tie-breaking fallback
- **Benefit:** Fast, interpretable, no hyperparameter tuning, easy to explain

### Voting Logic

**Vote Classification:**
- score >= 0.5 → YES vote
- score < 0.5 → NO vote

**Majority Rule:**
- vote_yes / total >= threshold_level → ACCEPT (1.0)
- Otherwise → REJECT (0.0)
- vote_yes == vote_no → Apply tie-breaker

**Confidence:**
- confidence = abs(vote_yes - vote_no) / total
- High margin → High confidence, vice versa

### Tie-Breaking Strategies

| Strategy | Behavior | Deterministic |
|----------|----------|---------------|
| HIGHEST_CONFIDENCE | Pick vote with highest mean score | Yes |
| RANDOM_SEEDED | Use seeded RNG (hash of scores) | Yes |
| ESCALATE_TO_DEBATE | Flag for human review | Yes (no decision) |

### Implementation Code

```python
from enum import Enum
from typing import Optional
import hashlib
import numpy as np


class TieBreaker(Enum):
    """Strategies for breaking 50-50 votes."""
    HIGHEST_CONFIDENCE = "highest_confidence"
    RANDOM_SEEDED = "random_seeded"
    ESCALATE_TO_DEBATE = "escalate_to_debate"


class MajorityVoting:
    """
    Majority voting consensus with configurable threshold and tie-breaking.

    Votes are binary (score >= 0.5 → YES, else NO). Majority wins if
    (vote_yes / total) >= threshold_level. Ties are broken via strategy.
    """

    def __init__(
        self,
        threshold_level: float = 0.5,
        tie_breaker: TieBreaker = TieBreaker.HIGHEST_CONFIDENCE,
    ):
        """
        Initialize Majority Voting consensus.

        Args:
            threshold_level: Voting threshold for majority (default 0.5, range (0, 1))
            tie_breaker: Strategy for 50-50 ties (default HIGHEST_CONFIDENCE)

        Raises:
            ValueError: If threshold_level not in (0, 1)
        """
        if not (0.0 < threshold_level < 1.0):
            raise ValueError("Threshold must be in range (0, 1), exclusive")

        self.threshold_level = threshold_level
        self.tie_breaker = tie_breaker

    async def compute(
        self,
        scores: list[float],
        **kwargs
    ) -> ConsensusResult:
        """
        Compute majority voting consensus.

        Args:
            scores: List of scores in [0, 1]
            **kwargs: Additional parameters (ignored for compatibility)

        Returns:
            ConsensusResult with majority decision and confidence

        Raises:
            ValueError: If scores is empty
        """
        if not scores:
            raise ValueError("Scores array cannot be empty")

        scores_array = np.array(scores, dtype=np.float64)
        n_votes = len(scores_array)

        # Count votes
        vote_yes = np.sum(scores_array >= 0.5)
        vote_no = n_votes - vote_yes

        # Check for tie
        is_tie = (vote_yes == vote_no)

        # Consensus score and resolution
        if is_tie:
            consensus_score, resolution = self._resolve_tie(
                scores_array, vote_yes, vote_no
            )
        else:
            # No tie: majority wins
            ratio = vote_yes / n_votes
            if ratio >= self.threshold_level:
                consensus_score = 1.0
                resolution = DisagreementResolution.ACCEPT
            else:
                consensus_score = 0.0
                resolution = DisagreementResolution.REJECT

        # Confidence: margin of victory
        margin = abs(vote_yes - vote_no)
        consensus_confidence = float(margin / n_votes)

        # Agreement level
        variance = np.var(scores_array)
        agreement_level = self._agreement_level(variance)

        return ConsensusResult(
            algorithm=ConsensusAlgorithm.MAJORITY_VOTING,
            consensus_score=consensus_score,
            consensus_confidence=consensus_confidence,
            agreement_level=agreement_level,
            resolution=resolution,
            individual_scores=scores,
            iteration_count=1,
            converged=True,
        )

    def _resolve_tie(
        self,
        scores: np.ndarray,
        vote_yes: int,
        vote_no: int,
    ) -> Tuple[float, DisagreementResolution]:
        """
        Apply tie-breaking strategy.

        Args:
            scores: Input score array
            vote_yes: Count of YES votes
            vote_no: Count of NO votes

        Returns:
            Tuple (consensus_score, resolution)
        """
        if self.tie_breaker == TieBreaker.HIGHEST_CONFIDENCE:
            # Pick the vote with higher mean confidence
            yes_scores = scores[scores >= 0.5]
            no_scores = scores[scores < 0.5]

            yes_mean = np.mean(yes_scores) if len(yes_scores) > 0 else 0.0
            no_mean = np.mean(no_scores) if len(no_scores) > 0 else 0.0

            if yes_mean >= no_mean:
                return 1.0, DisagreementResolution.ACCEPT
            else:
                return 0.0, DisagreementResolution.REJECT

        elif self.tie_breaker == TieBreaker.RANDOM_SEEDED:
            # Seeded RNG: hash of scores as seed
            score_bytes = scores.tobytes()
            seed = int(hashlib.md5(score_bytes).hexdigest(), 16) % (2**32)
            rng = np.random.RandomState(seed)

            pick_yes = rng.rand() >= 0.5
            if pick_yes:
                return 1.0, DisagreementResolution.ACCEPT
            else:
                return 0.0, DisagreementResolution.REJECT

        elif self.tie_breaker == TieBreaker.ESCALATE_TO_DEBATE:
            # Defer to human review
            return 0.5, DisagreementResolution.FLAG_FOR_REVIEW

        else:
            raise ValueError(f"Unknown tie-breaker: {self.tie_breaker}")

    @staticmethod
    def _agreement_level(variance: float) -> AgreementLevel:
        """Classify agreement level based on variance."""
        if variance < 0.05:
            return AgreementLevel.HIGH
        elif variance < 0.15:
            return AgreementLevel.MEDIUM
        else:
            return AgreementLevel.LOW
```

---

## ConsensusAlgorithm Enum Integration

### Current Enum (Before)
```python
class ConsensusAlgorithm(str, Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    ADAPTIVE_STABILITY = "adaptive_stability"
    BAYESIAN_STUB = "bayesian_stub"
    MAJORITY_VOTING_STUB = "majority_voting_stub"
```

### Updated Enum (After)
```python
class ConsensusAlgorithm(str, Enum):
    WEIGHTED_AVERAGE = "weighted_average"
    ADAPTIVE_STABILITY = "adaptive_stability"
    BAYESIAN = "bayesian"
    MAJORITY_VOTING = "majority_voting"
```

### Router Integration

**Before:**
```python
def get_consensus_algorithm(algo: ConsensusAlgorithm) -> BaseConsensus:
    if algo == ConsensusAlgorithm.WEIGHTED_AVERAGE:
        return WeightedAverageConsensus()
    elif algo == ConsensusAlgorithm.ADAPTIVE_STABILITY:
        return AdaptiveStabilityConsensus()
    else:
        raise NotImplementedError(f"Algorithm {algo} not implemented")
```

**After:**
```python
def get_consensus_algorithm(
    algo: ConsensusAlgorithm,
    config: Optional[dict] = None,
) -> BaseConsensus:
    config = config or {}

    if algo == ConsensusAlgorithm.WEIGHTED_AVERAGE:
        return WeightedAverageConsensus()
    elif algo == ConsensusAlgorithm.ADAPTIVE_STABILITY:
        return AdaptiveStabilityConsensus()
    elif algo == ConsensusAlgorithm.BAYESIAN:
        return BayesianConsensus(
            alpha_prior=config.get("alpha_prior", 2.0),
            beta_prior=config.get("beta_prior", 2.0),
            threshold=config.get("threshold", 0.5),
        )
    elif algo == ConsensusAlgorithm.MAJORITY_VOTING:
        tie_breaker_str = config.get("tie_breaker", "highest_confidence")
        tie_breaker = TieBreaker(tie_breaker_str)
        return MajorityVoting(
            threshold_level=config.get("threshold_level", 0.5),
            tie_breaker=tie_breaker,
        )
    else:
        raise NotImplementedError(f"Algorithm {algo} not implemented")
```

---

## Data Model: ConsensusResult (Existing)

Both new algorithms return the same `ConsensusResult` structure:

```python
from dataclasses import dataclass
from enum import Enum
from typing import List

class AgreementLevel(str, Enum):
    HIGH = "high"      # variance < 0.05
    MEDIUM = "medium"  # variance < 0.15
    LOW = "low"        # variance >= 0.15

class DisagreementResolution(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    FLAG_FOR_REVIEW = "flag_for_review"
    RE_EVALUATE = "re_evaluate"

@dataclass
class ConsensusResult:
    algorithm: ConsensusAlgorithm
    consensus_score: float  # [0, 1]
    consensus_confidence: float  # [0, 1]
    agreement_level: AgreementLevel
    resolution: DisagreementResolution
    individual_scores: List[float]
    iteration_count: int
    converged: bool
```

---

## Performance Targets

| Algorithm | Target | Method |
|-----------|--------|--------|
| Bayesian Consensus | <5ms mean, <10ms p99 (20 scores) | scipy.stats.beta (vectorized) |
| Majority Voting | <5ms mean, <10ms p99 (20 scores) | numpy vectorized vote counting |

**Benchmark Tool:** pytest-benchmark, seeded for reproducibility

---

## Edge Cases & Error Handling

| Case | Bayesian | Majority Voting |
|------|----------|-----------------|
| Empty scores | ValueError | ValueError |
| Single score | Posterior = Beta(α+1, β) | consensus_score=1.0, confidence=1.0 |
| All same score | Low variance, HIGH agreement | All votes same, consensus=1.0 |
| Tie (50-50) | N/A | Apply tie-breaker |
| Non-float input | Convert to float via numpy | Convert to float via numpy |

---

## Testing Strategy

### Unit Tests
- **BayesianConsensus:** Prior validation, posterior calculation, credible intervals, edge cases
- **MajorityVoting:** Vote counting, threshold rules, all tie-breakers, edge cases
- **Routing:** Enum dispatch verification, no breaking changes

### Fixtures
- Deterministic JSON fixtures with known input/output pairs
- Seeded RNG for reproducibility
- Bit-for-bit output matching (no rounding)

### Integration Tests
- Consensus algorithm routing via enum
- ConsensusResult model compatibility
- All four algorithms callable and working

---

## Files to Create/Modify

### New Files
- `_verification/algorithms/bayesian_consensus.py` — BayesianConsensus class
- `_verification/algorithms/majority_voting.py` — MajorityVoting class
- `tests/test_bayesian_consensus.py` — Unit tests
- `tests/test_majority_voting.py` — Unit tests
- `tests/test_consensus_routing.py` — Routing tests
- `tests/fixtures/consensus_test_data.json` — Deterministic fixtures

### Modified Files
- `_models/consensus.py` — Rename enum values (BAYESIAN_STUB → BAYESIAN, etc.)
- `_verification/consensus_router.py` — Add routing for both new algorithms

### Documentation
- `_architecture/alg/ALG-011-bayesian-consensus.md` — Algorithm design
- `_architecture/alg/ALG-012-majority-voting.md` — Algorithm design

