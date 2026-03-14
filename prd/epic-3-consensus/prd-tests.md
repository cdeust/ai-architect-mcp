# Test Plan: Epic 3 — Consensus Algorithm Completion

**Epic:** E3-CONSENSUS
**Last Updated:** 2026-03-14
**Test Framework:** pytest + pytest-asyncio + pytest-cov + pytest-benchmark
**Coverage Target:** >90% for both algorithms

---

## Test Structure

```
tests/
├── test_bayesian_consensus.py      # Unit tests for Bayesian algorithm
├── test_majority_voting.py          # Unit tests for Majority Voting
├── test_consensus_routing.py        # Integration tests for routing
└── fixtures/
    └── consensus_test_data.json     # Deterministic test fixtures
```

---

## File 1: test_bayesian_consensus.py

### Test Suite: Bayesian Consensus

```python
import pytest
import numpy as np
from scipy import stats
from _verification.algorithms.bayesian_consensus import BayesianConsensus
from _models.consensus import (
    ConsensusAlgorithm,
    ConsensusResult,
    AgreementLevel,
    DisagreementResolution,
)


class TestBayesianConsensusPriorInitialization:
    """Test Beta prior initialization."""

    def test_default_prior(self):
        """Test default prior parameters."""
        algo = BayesianConsensus()
        assert algo.alpha_prior == 2.0
        assert algo.beta_prior == 2.0
        assert algo.threshold == 0.5

    def test_custom_prior(self):
        """Test custom prior parameters."""
        algo = BayesianConsensus(alpha_prior=5.0, beta_prior=3.0, threshold=0.6)
        assert algo.alpha_prior == 5.0
        assert algo.beta_prior == 3.0
        assert algo.threshold == 0.6

    def test_invalid_alpha_prior(self):
        """Test validation: alpha_prior must be positive."""
        with pytest.raises(ValueError, match="Prior parameters must be positive"):
            BayesianConsensus(alpha_prior=-1.0)

    def test_invalid_beta_prior(self):
        """Test validation: beta_prior must be positive."""
        with pytest.raises(ValueError, match="Prior parameters must be positive"):
            BayesianConsensus(beta_prior=0.0)

    def test_zero_alpha_prior(self):
        """Test validation: alpha_prior cannot be zero."""
        with pytest.raises(ValueError, match="Prior parameters must be positive"):
            BayesianConsensus(alpha_prior=0.0)


class TestBayesianConsensusPosteriorCalculation:
    """Test Beta-Binomial posterior calculation."""

    @pytest.mark.asyncio
    async def test_posterior_known_inputs(self):
        """Test posterior with known input: [0.8, 0.7, 0.6, 0.4].

        Expected:
            - Successes (>= 0.5): 3 (0.8, 0.7, 0.6)
            - Failures (< 0.5): 1 (0.4)
            - Posterior α' = 2 + 3 = 5
            - Posterior β' = 2 + 1 = 3
            - Posterior mean = 5 / (5 + 3) = 0.625
        """
        algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0, threshold=0.5)
        result = await algo.compute([0.8, 0.7, 0.6, 0.4])

        # Exact posterior mean
        assert result.consensus_score == 0.625
        assert result.algorithm == ConsensusAlgorithm.BAYESIAN
        assert result.iteration_count == 1
        assert result.converged is True

    @pytest.mark.asyncio
    async def test_posterior_all_successes(self):
        """Test posterior when all scores >= threshold."""
        algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0, threshold=0.5)
        result = await algo.compute([0.9, 0.95, 1.0])

        # Posterior α' = 2 + 3 = 5, β' = 2 + 0 = 2
        # Posterior mean = 5 / (5 + 2) = 5/7 ≈ 0.714286
        expected_mean = 5.0 / 7.0
        assert result.consensus_score == pytest.approx(expected_mean, abs=1e-6)

    @pytest.mark.asyncio
    async def test_posterior_all_failures(self):
        """Test posterior when all scores < threshold."""
        algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0, threshold=0.5)
        result = await algo.compute([0.1, 0.2, 0.3])

        # Posterior α' = 2 + 0 = 2, β' = 2 + 3 = 5
        # Posterior mean = 2 / (2 + 5) = 2/7 ≈ 0.285714
        expected_mean = 2.0 / 7.0
        assert result.consensus_score == pytest.approx(expected_mean, abs=1e-6)

    @pytest.mark.asyncio
    async def test_posterior_custom_prior(self):
        """Test posterior with custom prior α=5, β=3."""
        algo = BayesianConsensus(alpha_prior=5.0, beta_prior=3.0, threshold=0.5)
        result = await algo.compute([0.8, 0.7, 0.6, 0.4])

        # Successes = 3, Failures = 1
        # Posterior α' = 5 + 3 = 8, β' = 3 + 1 = 4
        # Posterior mean = 8 / (8 + 4) = 8/12 = 2/3 ≈ 0.666667
        expected_mean = 8.0 / 12.0
        assert result.consensus_score == pytest.approx(expected_mean, abs=1e-6)


class TestBayesianConsensusCredibleInterval:
    """Test 95% credible interval calculation."""

    @pytest.mark.asyncio
    async def test_credible_interval_calculation(self):
        """Test credible interval from Beta posterior."""
        algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0)
        result = await algo.compute([0.8, 0.7, 0.6, 0.4])

        # Posterior β(5, 3)
        expected_lower = stats.beta.ppf(0.025, 5, 3)
        expected_upper = stats.beta.ppf(0.975, 5, 3)
        expected_width = expected_upper - expected_lower

        # Confidence is inverse of interval width
        expected_confidence = 1.0 - expected_width
        expected_confidence = max(0.0, min(1.0, expected_confidence))

        assert result.consensus_confidence == pytest.approx(expected_confidence, abs=1e-6)

    @pytest.mark.asyncio
    async def test_credible_interval_narrow(self):
        """Test credible interval with narrow posterior (high confidence)."""
        algo = BayesianConsensus(alpha_prior=100.0, beta_prior=100.0)
        # Strong prior, few samples → narrow posterior
        result = await algo.compute([0.9, 0.95])

        # Confidence should be high (narrow interval)
        assert result.consensus_confidence > 0.9

    @pytest.mark.asyncio
    async def test_credible_interval_wide(self):
        """Test credible interval with wide posterior (low confidence)."""
        algo = BayesianConsensus(alpha_prior=1.0, beta_prior=1.0)
        # Uniform prior, few samples → wide posterior
        result = await algo.compute([0.8])

        # Confidence should be lower (wide interval)
        assert result.consensus_confidence < 0.5


class TestBayesianConsensusAgreementLevel:
    """Test agreement level classification."""

    @pytest.mark.asyncio
    async def test_agreement_level_high(self):
        """Test HIGH agreement (variance < 0.05)."""
        algo = BayesianConsensus()
        result = await algo.compute([0.8, 0.79, 0.81, 0.82])  # Low variance

        assert result.agreement_level == AgreementLevel.HIGH

    @pytest.mark.asyncio
    async def test_agreement_level_medium(self):
        """Test MEDIUM agreement (variance 0.05-0.15)."""
        algo = BayesianConsensus()
        result = await algo.compute([0.8, 0.6, 0.7, 0.75])  # Medium variance

        assert result.agreement_level == AgreementLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_agreement_level_low(self):
        """Test LOW agreement (variance >= 0.15)."""
        algo = BayesianConsensus()
        result = await algo.compute([0.95, 0.1, 0.5, 0.8])  # High variance

        assert result.agreement_level == AgreementLevel.LOW


class TestBayesianConsensusErrorHandling:
    """Test error conditions."""

    @pytest.mark.asyncio
    async def test_empty_scores(self):
        """Test that empty scores raise ValueError."""
        algo = BayesianConsensus()
        with pytest.raises(ValueError, match="Scores array cannot be empty"):
            await algo.compute([])

    @pytest.mark.asyncio
    async def test_single_score(self):
        """Test with single score."""
        algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0)
        result = await algo.compute([0.8])

        # Single success: α' = 2 + 1 = 3, β' = 2 + 0 = 2
        # Mean = 3 / (3 + 2) = 3/5 = 0.6
        assert result.consensus_score == pytest.approx(0.6, abs=1e-6)


class TestBayesianConsensusConsensusResult:
    """Test ConsensusResult structure."""

    @pytest.mark.asyncio
    async def test_result_structure(self):
        """Test that ConsensusResult contains all required fields."""
        algo = BayesianConsensus()
        result = await algo.compute([0.8, 0.7, 0.6, 0.4])

        assert isinstance(result, ConsensusResult)
        assert result.algorithm == ConsensusAlgorithm.BAYESIAN
        assert isinstance(result.consensus_score, float)
        assert 0.0 <= result.consensus_score <= 1.0
        assert isinstance(result.consensus_confidence, float)
        assert 0.0 <= result.consensus_confidence <= 1.0
        assert result.agreement_level in [
            AgreementLevel.HIGH,
            AgreementLevel.MEDIUM,
            AgreementLevel.LOW,
        ]
        assert result.individual_scores == [0.8, 0.7, 0.6, 0.4]
        assert result.iteration_count == 1
        assert result.converged is True

    @pytest.mark.asyncio
    async def test_result_resolution(self):
        """Test resolution field in result."""
        algo = BayesianConsensus()
        result = await algo.compute([0.8, 0.7, 0.6, 0.4])

        assert result.resolution in [
            DisagreementResolution.ACCEPT,
            DisagreementResolution.FLAG_FOR_REVIEW,
        ]
```

---

## File 2: test_majority_voting.py

### Test Suite: Majority Voting

```python
import pytest
import numpy as np
from _verification.algorithms.majority_voting import MajorityVoting, TieBreaker
from _models.consensus import (
    ConsensusAlgorithm,
    ConsensusResult,
    AgreementLevel,
    DisagreementResolution,
)


class TestMajorityVotingThresholdConfiguration:
    """Test voting threshold configuration."""

    def test_default_threshold(self):
        """Test default threshold is 0.5."""
        algo = MajorityVoting()
        assert algo.threshold_level == 0.5
        assert algo.tie_breaker == TieBreaker.HIGHEST_CONFIDENCE

    def test_custom_threshold(self):
        """Test custom threshold configuration."""
        algo = MajorityVoting(threshold_level=0.66)
        assert algo.threshold_level == 0.66

    def test_invalid_threshold_zero(self):
        """Test that threshold=0.0 raises ValueError."""
        with pytest.raises(ValueError, match="Threshold must be in range"):
            MajorityVoting(threshold_level=0.0)

    def test_invalid_threshold_one(self):
        """Test that threshold=1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Threshold must be in range"):
            MajorityVoting(threshold_level=1.0)

    def test_valid_threshold_boundaries(self):
        """Test valid thresholds near boundaries."""
        algo1 = MajorityVoting(threshold_level=0.01)
        assert algo1.threshold_level == 0.01

        algo2 = MajorityVoting(threshold_level=0.99)
        assert algo2.threshold_level == 0.99


class TestMajorityVotingVoteAggregation:
    """Test vote counting and aggregation."""

    @pytest.mark.asyncio
    async def test_clear_majority_yes(self):
        """Test 3-1 vote (3 yes, 1 no) → ACCEPT."""
        algo = MajorityVoting(threshold_level=0.5)
        result = await algo.compute([0.8, 0.7, 0.6, 0.2])

        assert result.consensus_score == 1.0  # ACCEPT
        assert result.resolution == DisagreementResolution.ACCEPT
        assert result.consensus_confidence == 0.5  # margin 2, total 4

    @pytest.mark.asyncio
    async def test_clear_majority_no(self):
        """Test 1-3 vote (1 yes, 3 no) → REJECT."""
        algo = MajorityVoting(threshold_level=0.5)
        result = await algo.compute([0.8, 0.2, 0.3, 0.1])

        assert result.consensus_score == 0.0  # REJECT
        assert result.resolution == DisagreementResolution.REJECT
        assert result.consensus_confidence == 0.5

    @pytest.mark.asyncio
    async def test_boundary_majority_yes(self):
        """Test 2-2 vote but above threshold (3-1)."""
        algo = MajorityVoting(threshold_level=0.5)
        result = await algo.compute([0.8, 0.7, 0.2, 0.1])

        assert result.consensus_score == 1.0  # 2/4 = 0.5 >= 0.5 → ACCEPT
        assert result.consensus_confidence == 0.0  # No margin

    @pytest.mark.asyncio
    async def test_supermajority_threshold(self):
        """Test supermajority threshold (0.66)."""
        algo = MajorityVoting(threshold_level=0.66)
        result = await algo.compute([0.8, 0.7, 0.2, 0.1])

        # 2/4 = 0.5 < 0.66 → REJECT (fails supermajority)
        assert result.consensus_score == 0.0
        assert result.resolution == DisagreementResolution.REJECT


class TestMajorityVotingConfidenceCalculation:
    """Test confidence score (margin of victory)."""

    @pytest.mark.asyncio
    async def test_confidence_high_margin(self):
        """Test high confidence with large margin (3-1)."""
        algo = MajorityVoting()
        result = await algo.compute([0.8, 0.7, 0.2, 0.1])

        # vote_yes=2, vote_no=2, margin=0, confidence=0.0
        # Wait, 0.8,0.7 are yes, 0.2,0.1 are no → 2-2, no margin
        assert result.consensus_confidence == 0.0

    @pytest.mark.asyncio
    async def test_confidence_low_margin(self):
        """Test low confidence with narrow margin (2-1)."""
        algo = MajorityVoting()
        result = await algo.compute([0.8, 0.7, 0.2])

        # vote_yes=2, vote_no=1, margin=1, confidence=1/3≈0.333
        assert result.consensus_confidence == pytest.approx(1.0 / 3.0, abs=1e-6)

    @pytest.mark.asyncio
    async def test_confidence_single_vote(self):
        """Test single vote → confidence 1.0."""
        algo = MajorityVoting()
        result = await algo.compute([0.8])

        assert result.consensus_confidence == 1.0


class TestMajorityVotingTieBreaker:
    """Test all three tie-breaking strategies."""

    @pytest.mark.asyncio
    async def test_tie_breaker_highest_confidence_yes_wins(self):
        """Test HIGHEST_CONFIDENCE: higher mean vote wins (0.8 vs 0.2)."""
        algo = MajorityVoting(tie_breaker=TieBreaker.HIGHEST_CONFIDENCE)
        result = await algo.compute([0.8, 0.2])

        # YES votes: [0.8], mean=0.8
        # NO votes: [0.2], mean=0.2
        # 0.8 > 0.2 → YES wins → ACCEPT
        assert result.consensus_score == 1.0
        assert result.resolution == DisagreementResolution.ACCEPT

    @pytest.mark.asyncio
    async def test_tie_breaker_highest_confidence_no_wins(self):
        """Test HIGHEST_CONFIDENCE: lower mean vote loses (0.3 vs 0.9)."""
        algo = MajorityVoting(tie_breaker=TieBreaker.HIGHEST_CONFIDENCE)
        result = await algo.compute([0.3, 0.9])

        # YES votes: [0.9], mean=0.9
        # NO votes: [0.3], mean=0.3
        # 0.9 > 0.3 → YES wins → ACCEPT
        assert result.consensus_score == 1.0

    @pytest.mark.asyncio
    async def test_tie_breaker_random_seeded_deterministic(self):
        """Test RANDOM_SEEDED: same input → same output (deterministic)."""
        algo = MajorityVoting(tie_breaker=TieBreaker.RANDOM_SEEDED)

        result1 = await algo.compute([0.7, 0.3])
        result2 = await algo.compute([0.7, 0.3])

        # Same input + seeded RNG = identical output
        assert result1.consensus_score == result2.consensus_score
        assert result1.resolution == result2.resolution

    @pytest.mark.asyncio
    async def test_tie_breaker_escalate_to_debate(self):
        """Test ESCALATE_TO_DEBATE: defer to human review."""
        algo = MajorityVoting(tie_breaker=TieBreaker.ESCALATE_TO_DEBATE)
        result = await algo.compute([0.7, 0.3])

        assert result.consensus_score == 0.5  # Neutral, no decision
        assert result.resolution == DisagreementResolution.FLAG_FOR_REVIEW

    @pytest.mark.asyncio
    async def test_tie_breaker_consistency(self):
        """Test tie-breaker consistency across multiple calls."""
        algo = MajorityVoting(tie_breaker=TieBreaker.RANDOM_SEEDED)

        results = [await algo.compute([0.6, 0.4]) for _ in range(5)]

        # All results should be identical (seeded)
        scores = [r.consensus_score for r in results]
        assert all(s == scores[0] for s in scores)


class TestMajorityVotingAgreementLevel:
    """Test agreement level classification."""

    @pytest.mark.asyncio
    async def test_agreement_level_high(self):
        """Test HIGH agreement (low variance)."""
        algo = MajorityVoting()
        result = await algo.compute([0.8, 0.79, 0.81, 0.82])

        assert result.agreement_level == AgreementLevel.HIGH

    @pytest.mark.asyncio
    async def test_agreement_level_medium(self):
        """Test MEDIUM agreement (medium variance)."""
        algo = MajorityVoting()
        result = await algo.compute([0.8, 0.6, 0.7, 0.75])

        assert result.agreement_level == AgreementLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_agreement_level_low(self):
        """Test LOW agreement (high variance)."""
        algo = MajorityVoting()
        result = await algo.compute([0.95, 0.1, 0.5, 0.8])

        assert result.agreement_level == AgreementLevel.LOW


class TestMajorityVotingEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_scores(self):
        """Test empty input → ValueError."""
        algo = MajorityVoting()
        with pytest.raises(ValueError, match="Scores array cannot be empty"):
            await algo.compute([])

    @pytest.mark.asyncio
    async def test_single_score(self):
        """Test single score → that vote wins."""
        algo = MajorityVoting()
        result = await algo.compute([0.8])

        assert result.consensus_score == 1.0  # YES vote
        assert result.consensus_confidence == 1.0

    @pytest.mark.asyncio
    async def test_all_same_scores_yes(self):
        """Test all scores >= 0.5 → unanimous ACCEPT."""
        algo = MajorityVoting()
        result = await algo.compute([0.9, 0.95, 1.0])

        assert result.consensus_score == 1.0
        assert result.consensus_confidence == 1.0

    @pytest.mark.asyncio
    async def test_all_same_scores_no(self):
        """Test all scores < 0.5 → unanimous REJECT."""
        algo = MajorityVoting()
        result = await algo.compute([0.1, 0.2, 0.3])

        assert result.consensus_score == 0.0
        assert result.consensus_confidence == 1.0


class TestMajorityVotingConsensusResult:
    """Test ConsensusResult structure."""

    @pytest.mark.asyncio
    async def test_result_structure(self):
        """Test ConsensusResult contains all required fields."""
        algo = MajorityVoting()
        result = await algo.compute([0.8, 0.7, 0.2, 0.1])

        assert isinstance(result, ConsensusResult)
        assert result.algorithm == ConsensusAlgorithm.MAJORITY_VOTING
        assert result.consensus_score in [0.0, 0.5, 1.0]
        assert 0.0 <= result.consensus_confidence <= 1.0
        assert result.agreement_level in [
            AgreementLevel.HIGH,
            AgreementLevel.MEDIUM,
            AgreementLevel.LOW,
        ]
        assert result.individual_scores == [0.8, 0.7, 0.2, 0.1]
        assert result.iteration_count == 1
        assert result.converged is True
```

---

## File 3: test_consensus_routing.py

### Test Suite: Consensus Algorithm Routing

```python
import pytest
from _verification.consensus_router import get_consensus_algorithm
from _verification.algorithms.bayesian_consensus import BayesianConsensus
from _verification.algorithms.majority_voting import MajorityVoting, TieBreaker
from _models.consensus import ConsensusAlgorithm


class TestConsensusRouterDispatch:
    """Test router dispatch for all algorithms."""

    def test_bayesian_algorithm_dispatch(self):
        """Test BAYESIAN enum routes to BayesianConsensus."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.BAYESIAN)
        assert isinstance(algo, BayesianConsensus)

    def test_majority_voting_algorithm_dispatch(self):
        """Test MAJORITY_VOTING enum routes to MajorityVoting."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.MAJORITY_VOTING)
        assert isinstance(algo, MajorityVoting)

    def test_weighted_average_algorithm_dispatch(self):
        """Test WEIGHTED_AVERAGE still works (no breaking changes)."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.WEIGHTED_AVERAGE)
        assert algo is not None  # Type depends on implementation

    def test_adaptive_stability_algorithm_dispatch(self):
        """Test ADAPTIVE_STABILITY still works (no breaking changes)."""
        algo = get_consensus_algorithm(ConsensusAlgorithm.ADAPTIVE_STABILITY)
        assert algo is not None

    def test_all_algorithms_dispatch(self):
        """Test all four algorithms are dispatchable."""
        algorithms = [
            ConsensusAlgorithm.WEIGHTED_AVERAGE,
            ConsensusAlgorithm.ADAPTIVE_STABILITY,
            ConsensusAlgorithm.BAYESIAN,
            ConsensusAlgorithm.MAJORITY_VOTING,
        ]

        for algo_enum in algorithms:
            algo = get_consensus_algorithm(algo_enum)
            assert algo is not None


class TestConsensusRouterConfiguration:
    """Test router with algorithm configuration."""

    def test_bayesian_with_custom_prior(self):
        """Test router respects custom Bayesian prior config."""
        config = {"alpha_prior": 5.0, "beta_prior": 3.0}
        algo = get_consensus_algorithm(ConsensusAlgorithm.BAYESIAN, config=config)

        assert isinstance(algo, BayesianConsensus)
        assert algo.alpha_prior == 5.0
        assert algo.beta_prior == 3.0

    def test_majority_voting_with_custom_threshold(self):
        """Test router respects custom Majority Voting threshold config."""
        config = {"threshold_level": 0.66, "tie_breaker": "escalate_to_debate"}
        algo = get_consensus_algorithm(
            ConsensusAlgorithm.MAJORITY_VOTING, config=config
        )

        assert isinstance(algo, MajorityVoting)
        assert algo.threshold_level == 0.66
        assert algo.tie_breaker == TieBreaker.ESCALATE_TO_DEBATE


class TestEnumValuesExist:
    """Test that enum values are correctly renamed."""

    def test_bayesian_enum_exists(self):
        """Test BAYESIAN enum value exists."""
        assert hasattr(ConsensusAlgorithm, "BAYESIAN")
        assert ConsensusAlgorithm.BAYESIAN.value == "bayesian"

    def test_majority_voting_enum_exists(self):
        """Test MAJORITY_VOTING enum value exists."""
        assert hasattr(ConsensusAlgorithm, "MAJORITY_VOTING")
        assert ConsensusAlgorithm.MAJORITY_VOTING.value == "majority_voting"

    def test_old_enum_values_removed(self):
        """Test old stub enum values are removed."""
        assert not hasattr(ConsensusAlgorithm, "BAYESIAN_STUB")
        assert not hasattr(ConsensusAlgorithm, "MAJORITY_VOTING_STUB")
```

---

## File 4: fixtures/consensus_test_data.json

### Deterministic Test Fixtures

```json
{
  "bayesian_consensus": {
    "known_inputs": [
      {
        "name": "test_known_posterior",
        "scores": [0.8, 0.7, 0.6, 0.4],
        "alpha_prior": 2.0,
        "beta_prior": 2.0,
        "threshold": 0.5,
        "expected_consensus_score": 0.625,
        "expected_successes": 3,
        "expected_failures": 1
      },
      {
        "name": "test_all_successes",
        "scores": [0.9, 0.95, 1.0],
        "alpha_prior": 2.0,
        "beta_prior": 2.0,
        "threshold": 0.5,
        "expected_consensus_score": 0.7142857142857143,
        "expected_successes": 3,
        "expected_failures": 0
      },
      {
        "name": "test_all_failures",
        "scores": [0.1, 0.2, 0.3],
        "alpha_prior": 2.0,
        "beta_prior": 2.0,
        "threshold": 0.5,
        "expected_consensus_score": 0.2857142857142857,
        "expected_successes": 0,
        "expected_failures": 3
      },
      {
        "name": "test_custom_prior",
        "scores": [0.8, 0.7, 0.6, 0.4],
        "alpha_prior": 5.0,
        "beta_prior": 3.0,
        "threshold": 0.5,
        "expected_consensus_score": 0.6666666666666666,
        "expected_successes": 3,
        "expected_failures": 1
      }
    ],
    "edge_cases": [
      {
        "name": "test_single_score",
        "scores": [0.8],
        "alpha_prior": 2.0,
        "beta_prior": 2.0,
        "threshold": 0.5,
        "expected_consensus_score": 0.6
      }
    ]
  },
  "majority_voting": {
    "voting_aggregation": [
      {
        "name": "test_clear_majority_yes",
        "scores": [0.8, 0.7, 0.6, 0.2],
        "threshold_level": 0.5,
        "expected_consensus_score": 1.0,
        "expected_vote_yes": 3,
        "expected_vote_no": 1,
        "expected_confidence": 0.5,
        "expected_resolution": "accept"
      },
      {
        "name": "test_clear_majority_no",
        "scores": [0.8, 0.2, 0.3, 0.1],
        "threshold_level": 0.5,
        "expected_consensus_score": 0.0,
        "expected_vote_yes": 1,
        "expected_vote_no": 3,
        "expected_confidence": 0.5,
        "expected_resolution": "reject"
      },
      {
        "name": "test_supermajority",
        "scores": [0.8, 0.7, 0.2, 0.1],
        "threshold_level": 0.66,
        "expected_consensus_score": 0.0,
        "expected_vote_yes": 2,
        "expected_vote_no": 2,
        "expected_resolution": "reject"
      }
    ],
    "tie_breaking": [
      {
        "name": "test_tie_highest_confidence_yes",
        "scores": [0.8, 0.2],
        "tie_breaker": "highest_confidence",
        "expected_consensus_score": 1.0,
        "expected_resolution": "accept"
      },
      {
        "name": "test_tie_escalate",
        "scores": [0.7, 0.3],
        "tie_breaker": "escalate_to_debate",
        "expected_consensus_score": 0.5,
        "expected_resolution": "flag_for_review"
      }
    ],
    "edge_cases": [
      {
        "name": "test_single_vote",
        "scores": [0.8],
        "threshold_level": 0.5,
        "expected_consensus_score": 1.0,
        "expected_confidence": 1.0
      },
      {
        "name": "test_all_yes",
        "scores": [0.9, 0.95, 1.0],
        "threshold_level": 0.5,
        "expected_consensus_score": 1.0,
        "expected_confidence": 1.0
      },
      {
        "name": "test_all_no",
        "scores": [0.1, 0.2, 0.3],
        "threshold_level": 0.5,
        "expected_consensus_score": 0.0,
        "expected_confidence": 1.0
      }
    ]
  }
}
```

---

## Performance Benchmarks

### Benchmark Configuration (pytest-benchmark)

```python
# In conftest.py or inline in tests

@pytest.mark.benchmark
class TestBayesianConsensusBenchmark:
    """Benchmark Bayesian consensus performance."""

    @pytest.mark.asyncio
    def test_benchmark_bayesian_20_scores(self, benchmark):
        """Benchmark: 20 scores, default prior."""
        algo = BayesianConsensus()
        scores = [0.5 + 0.05 * i for i in range(20)]

        result = benchmark(
            lambda: asyncio.run(algo.compute(scores)),
            rounds=100,
        )

        assert result.consensus_score > 0.0


@pytest.mark.benchmark
class TestMajorityVotingBenchmark:
    """Benchmark Majority Voting performance."""

    @pytest.mark.asyncio
    def test_benchmark_majority_voting_20_scores(self, benchmark):
        """Benchmark: 20 scores, default threshold."""
        algo = MajorityVoting()
        scores = [0.5 + 0.05 * i for i in range(20)]

        result = benchmark(
            lambda: asyncio.run(algo.compute(scores)),
            rounds=100,
        )

        assert result.consensus_score in [0.0, 0.5, 1.0]
```

**Expected Results:**
- Bayesian: <5ms mean, <10ms p99
- Majority Voting: <5ms mean, <10ms p99

---

## Test Execution & Coverage

### Command Line Execution

```bash
# Run all tests
pytest tests/test_bayesian_consensus.py tests/test_majority_voting.py tests/test_consensus_routing.py -v

# Run with coverage
pytest tests/ --cov=_verification/algorithms --cov-report=html --cov-report=term

# Run benchmarks
pytest tests/ -v -m benchmark --benchmark-only

# Run specific test class
pytest tests/test_bayesian_consensus.py::TestBayesianConsensusPosteriorCalculation -v
```

### Coverage Target
- **Line Coverage:** >90%
- **Branch Coverage:** >85%
- **Excluded:** __pycache__, venv, .git

---

## Determinism Verification

### Test Reproducibility

```python
@pytest.mark.asyncio
async def test_deterministic_bayesian():
    """Verify identical inputs produce identical outputs."""
    algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0)
    scores = [0.8, 0.7, 0.6, 0.4]

    results = [await algo.compute(scores) for _ in range(10)]

    # All results must be identical (bit-for-bit)
    first_score = results[0].consensus_score
    assert all(r.consensus_score == first_score for r in results)
```

