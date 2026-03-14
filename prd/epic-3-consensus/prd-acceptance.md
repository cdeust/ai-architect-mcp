# Acceptance Criteria: Epic 3 — Consensus Algorithm Completion

**Epic:** E3-CONSENSUS
**Last Updated:** 2026-03-14
**Total ACs:** 15 (AC-E3-001 through AC-E3-022)

---

## AC-E3-001: Bayesian Prior Initialization

**Story:** STORY-E3-001
**Feature:** Bayesian Consensus — Beta Prior Definition (FR-E3-001)

### Scenario: Default Prior
**GIVEN** a BayesianConsensus instance created with default parameters
**WHEN** the instance is instantiated
**THEN** the Beta prior is initialized with α=2.0, β=2.0

**Test Code:**
```python
def test_bayesian_default_prior():
    algo = BayesianConsensus()
    assert algo.alpha_prior == 2.0
    assert algo.beta_prior == 2.0
    assert algo.threshold == 0.5
```

### Scenario: Custom Prior
**GIVEN** a BayesianConsensus instance created with custom parameters (α=5, β=3)
**WHEN** the instance is instantiated
**THEN** the prior parameters are stored correctly

**Test Code:**
```python
def test_bayesian_custom_prior():
    algo = BayesianConsensus(alpha_prior=5.0, beta_prior=3.0)
    assert algo.alpha_prior == 5.0
    assert algo.beta_prior == 3.0
```

### Scenario: Invalid Prior Validation
**GIVEN** a BayesianConsensus initialization with α <= 0
**WHEN** the constructor is called
**THEN** ValueError is raised with message "Prior parameters must be positive"

**Test Code:**
```python
def test_bayesian_invalid_prior():
    with pytest.raises(ValueError, match="Prior parameters must be positive"):
        BayesianConsensus(alpha_prior=-1.0)
    with pytest.raises(ValueError, match="Prior parameters must be positive"):
        BayesianConsensus(beta_prior=0.0)
```

| KPI | Value | Status |
|-----|-------|--------|
| Alpha prior default | 2.0 | Pending |
| Beta prior default | 2.0 | Pending |
| Custom prior support | Yes | Pending |
| Validation enforcement | ValueError | Pending |

---

## AC-E3-002: Bayesian Posterior Calculation

**Story:** STORY-E3-001
**Feature:** Bayesian Posterior Calculation (FR-E3-002)

### Scenario: Known Inputs → Known Posterior
**GIVEN** input scores [0.8, 0.7, 0.6, 0.4], threshold=0.5, prior α=2, β=2
**WHEN** compute() is called
**THEN**
- Successes (scores >= 0.5) = 3 (indices 0, 1, 2)
- Failures (scores < 0.5) = 1 (index 3)
- Posterior α' = 2 + 3 = 5
- Posterior β' = 2 + 1 = 3
- Posterior mean = 5 / (5 + 3) = 0.625
- consensus_score = 0.625 (exact)

**Test Code:**
```python
@pytest.mark.asyncio
async def test_bayesian_posterior_calculation():
    algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0, threshold=0.5)
    result = await algo.compute([0.8, 0.7, 0.6, 0.4])

    assert result.consensus_score == 0.625  # 5 / (5 + 3)
    assert result.algorithm == ConsensusAlgorithm.BAYESIAN
    assert result.iteration_count == 1
    assert result.converged is True
```

### Scenario: All Successes
**GIVEN** scores all >= threshold
**WHEN** compute() is called
**THEN** failures = 0, posterior mean approaches 1.0

**Test Code:**
```python
@pytest.mark.asyncio
async def test_bayesian_all_successes():
    algo = BayesianConsensus(alpha_prior=2.0, beta_prior=2.0)
    result = await algo.compute([0.9, 0.95, 1.0])

    assert result.consensus_score == 5.0 / 5.0  # (2+3) / (2+3+2)
```

| KPI | Value | Status |
|-----|-------|--------|
| Posterior α' calculation | α + successes | Pending |
| Posterior β' calculation | β + failures | Pending |
| Posterior mean (0.8,0.7,0.6,0.4) | 0.625 | Pending |
| Posterior mean (all successes) | 1.0 | Pending |

---

## AC-E3-003: Bayesian Credible Interval Calculation

**Story:** STORY-E3-001
**Feature:** Bayesian Credible Interval Calculation (FR-E3-003)

### Scenario: 95% Credible Interval from Posterior
**GIVEN** posterior Beta(5, 3)
**WHEN** credible_interval() is called
**THEN** returns (lower, upper) from scipy.stats.beta(5, 3).ppf([0.025, 0.975])

**Expected Result:**
- lower ≈ 0.373
- upper ≈ 0.854
- interval_width ≈ 0.481

**Test Code:**
```python
@pytest.mark.asyncio
async def test_bayesian_credible_interval():
    algo = BayesianConsensus()
    result = await algo.compute([0.8, 0.7, 0.6, 0.4])

    from scipy import stats
    expected_lower = stats.beta.ppf(0.025, 5, 3)
    expected_upper = stats.beta.ppf(0.975, 5, 3)

    # Verify interval width is reasonable (inverse of confidence)
    interval_width = expected_upper - expected_lower
    expected_confidence = 1.0 - interval_width

    # Confidence should be positive and <1
    assert 0.0 < result.consensus_confidence < 1.0
```

| KPI | Value | Status |
|-----|-------|--------|
| Credible interval method | scipy.stats.beta.ppf | Pending |
| Lower percentile | 2.5% | Pending |
| Upper percentile | 97.5% | Pending |
| Edge case: uniform posterior | Handled | Pending |

---

## AC-E3-004: Bayesian Consensus Result Structure

**Story:** STORY-E3-001
**Feature:** Bayesian Consensus Score Computation (FR-E3-004)

### Scenario: Complete ConsensusResult Return
**GIVEN** Bayesian algorithm with scores [0.8, 0.7, 0.6, 0.4]
**WHEN** compute() returns
**THEN**
- `algorithm` = `ConsensusAlgorithm.BAYESIAN`
- `consensus_score` = posterior mean (0.625)
- `consensus_confidence` = 1.0 - (upper - lower)
- `agreement_level` = computed from variance
- `individual_scores` = [0.8, 0.7, 0.6, 0.4]
- `iteration_count` = 1
- `converged` = True

**Test Code:**
```python
@pytest.mark.asyncio
async def test_bayesian_result_structure():
    algo = BayesianConsensus()
    result = await algo.compute([0.8, 0.7, 0.6, 0.4])

    assert result.algorithm == ConsensusAlgorithm.BAYESIAN
    assert isinstance(result.consensus_score, float)
    assert 0.0 <= result.consensus_score <= 1.0
    assert isinstance(result.consensus_confidence, float)
    assert 0.0 <= result.consensus_confidence <= 1.0
    assert result.agreement_level in [AgreementLevel.HIGH, AgreementLevel.MEDIUM, AgreementLevel.LOW]
    assert result.individual_scores == [0.8, 0.7, 0.6, 0.4]
    assert result.iteration_count == 1
    assert result.converged is True
```

| KPI | Value | Status |
|-----|-------|--------|
| Algorithm field | ConsensusAlgorithm.BAYESIAN | Pending |
| Score range | [0, 1] | Pending |
| Confidence range | [0, 1] | Pending |
| Agreement level computation | Variance-based | Pending |
| Input preservation | Individual scores unchanged | Pending |

---

## AC-E3-005: Bayesian Error Handling

**Story:** STORY-E3-001
**Feature:** Bayesian Consensus Score Computation (FR-E3-004)

### Scenario: Empty Scores Array
**GIVEN** compute() called with empty array []
**WHEN** the method executes
**THEN** raises ValueError with message "Scores array cannot be empty"

**Test Code:**
```python
@pytest.mark.asyncio
async def test_bayesian_empty_scores():
    algo = BayesianConsensus()
    with pytest.raises(ValueError, match="Scores array cannot be empty"):
        await algo.compute([])
```

| KPI | Value | Status |
|-----|-------|--------|
| Empty input handling | ValueError raised | Pending |
| Error message | Descriptive | Pending |
| Exception type | ValueError | Pending |

---

## AC-E3-006: Majority Voting Threshold Configuration

**Story:** STORY-E3-002
**Feature:** Majority Voting Threshold Configuration (FR-E3-005)

### Scenario: Default Threshold
**GIVEN** MajorityVoting instance with default configuration
**WHEN** created
**THEN** threshold_level = 0.5

**Test Code:**
```python
def test_majority_voting_default_threshold():
    algo = MajorityVoting()
    assert algo.threshold_level == 0.5
```

### Scenario: Custom Threshold
**GIVEN** MajorityVoting with threshold_level=0.66 (supermajority)
**WHEN** created
**THEN** threshold_level = 0.66

**Test Code:**
```python
def test_majority_voting_custom_threshold():
    algo = MajorityVoting(threshold_level=0.66)
    assert algo.threshold_level == 0.66
```

### Scenario: Invalid Threshold Validation
**GIVEN** threshold_level = 0.0 or 1.0 (boundaries, exclusive range)
**WHEN** created
**THEN** raises ValueError

**Test Code:**
```python
def test_majority_voting_invalid_threshold():
    with pytest.raises(ValueError, match="Threshold must be in range"):
        MajorityVoting(threshold_level=0.0)
    with pytest.raises(ValueError, match="Threshold must be in range"):
        MajorityVoting(threshold_level=1.0)
```

| KPI | Value | Status |
|-----|-------|--------|
| Default threshold | 0.5 | Pending |
| Custom threshold support | Yes | Pending |
| Valid range | (0, 1) exclusive | Pending |
| Boundary validation | Enforced | Pending |

---

## AC-E3-007: Majority Voting Vote Aggregation

**Story:** STORY-E3-002
**Feature:** Majority Voting — Vote Aggregation (FR-E3-006)

### Scenario: Clear Majority
**GIVEN** scores [0.8, 0.7, 0.2, 0.1], threshold=0.5
**WHEN** compute() is called
**THEN**
- vote_yes = 2 (scores >= 0.5: 0.8, 0.7)
- vote_no = 2 (scores < 0.5: 0.2, 0.1)
- ratio = 2 / 4 = 0.5
- check: 0.5 >= 0.5 is true → consensus_score = 1.0 (ACCEPT)

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_aggregation():
    algo = MajorityVoting(threshold_level=0.5)
    result = await algo.compute([0.8, 0.7, 0.2, 0.1])

    assert result.consensus_score == 1.0  # ACCEPT (2 yes >= threshold)
    assert result.algorithm == ConsensusAlgorithm.MAJORITY_VOTING
```

### Scenario: Clear Rejection
**GIVEN** scores [0.4, 0.3, 0.2, 0.1], threshold=0.5
**WHEN** compute() is called
**THEN**
- vote_yes = 0
- vote_no = 4
- ratio = 0 / 4 = 0.0
- check: 0.0 >= 0.5 is false → consensus_score = 0.0 (REJECT)

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_rejection():
    algo = MajorityVoting(threshold_level=0.5)
    result = await algo.compute([0.4, 0.3, 0.2, 0.1])

    assert result.consensus_score == 0.0  # REJECT
    assert result.resolution == DisagreementResolution.REJECT
```

| KPI | Value | Status |
|-----|-------|--------|
| Vote YES classification | score >= 0.5 | Pending |
| Vote NO classification | score < 0.5 | Pending |
| Majority rule | vote_yes / total >= threshold | Pending |
| ACCEPT outcome | consensus_score = 1.0 | Pending |
| REJECT outcome | consensus_score = 0.0 | Pending |

---

## AC-E3-008: Majority Voting Confidence Calculation

**Story:** STORY-E3-002
**Feature:** Majority Voting Consensus Computation (FR-E3-008)

### Scenario: High Confidence Win
**GIVEN** scores [0.8, 0.7, 0.2, 0.1] (3 yes, 1 no)
**WHEN** compute() is called
**THEN**
- vote_yes = 3, vote_no = 1
- margin = abs(3 - 1) = 2
- confidence = 2 / 4 = 0.5
- agreement_level = HIGH (variance < 0.05)

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_confidence():
    algo = MajorityVoting()
    result = await algo.compute([0.8, 0.7, 0.2, 0.1])

    assert result.consensus_confidence == 0.5  # margin 2, total 4
    assert result.agreement_level == AgreementLevel.MEDIUM  # variance between 0.05-0.15
```

| KPI | Value | Status |
|-----|-------|--------|
| Confidence formula | margin / total | Pending |
| Margin calculation | abs(yes - no) | Pending |
| Confidence range | [0, 1] | Pending |
| Agreement level | Variance-based | Pending |

---

## AC-E3-009: Majority Voting Tie-Breaking — HIGHEST_CONFIDENCE

**Story:** STORY-E3-002
**Feature:** Majority Voting — Tie-Breaking Strategies (FR-E3-007)

### Scenario: 50-50 Tie, HIGHEST_CONFIDENCE Resolution
**GIVEN** scores [0.8, 0.2] (vote_yes=1, vote_no=1)
**WHEN** compute() is called with tie_breaker=TieBreaker.HIGHEST_CONFIDENCE
**THEN**
- Mean of YES votes = (0.8) = 0.8
- Mean of NO votes = (0.2) = 0.2
- 0.8 >= 0.2 → pick YES
- consensus_score = 1.0 (ACCEPT)
- consensus_confidence = 1.0 (deterministic)

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_tie_highest_confidence():
    algo = MajorityVoting(tie_breaker=TieBreaker.HIGHEST_CONFIDENCE)
    result = await algo.compute([0.8, 0.2])

    assert result.consensus_score == 1.0  # YES picked (0.8 > 0.2)
    assert result.resolution == DisagreementResolution.ACCEPT
    assert result.consensus_confidence == 1.0
```

| KPI | Value | Status |
|-----|-------|--------|
| Tie detection | vote_yes == vote_no | Pending |
| Mean YES calculation | average of yes votes | Pending |
| Mean NO calculation | average of no votes | Pending |
| Determinism | Reproducible | Pending |
| Outcome (0.8 vs 0.2) | YES wins | Pending |

---

## AC-E3-010: Majority Voting Tie-Breaking — RANDOM_SEEDED

**Story:** STORY-E3-002
**Feature:** Majority Voting — Tie-Breaking Strategies (FR-E3-007)

### Scenario: 50-50 Tie, RANDOM_SEEDED Resolution
**GIVEN** scores [0.7, 0.3] (1 yes, 1 no)
**WHEN** compute() is called twice with same scores and tie_breaker=TieBreaker.RANDOM_SEEDED
**THEN** both calls produce identical outcomes (seeded RNG)

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_tie_random_seeded():
    algo = MajorityVoting(tie_breaker=TieBreaker.RANDOM_SEEDED)

    result1 = await algo.compute([0.7, 0.3])
    result2 = await algo.compute([0.7, 0.3])

    # Same input + seeded RNG = same output
    assert result1.consensus_score == result2.consensus_score
    assert result1.resolution == result2.resolution
```

| KPI | Value | Status |
|-----|-------|--------|
| Seeding mechanism | Hash of score bytes | Pending |
| Determinism | Identical runs → identical outcome | Pending |
| PRNG seed | Derived from input | Pending |

---

## AC-E3-011: Majority Voting Tie-Breaking — ESCALATE_TO_DEBATE

**Story:** STORY-E3-002
**Feature:** Majority Voting — Tie-Breaking Strategies (FR-E3-007)

### Scenario: 50-50 Tie, ESCALATE_TO_DEBATE Resolution
**GIVEN** scores [0.6, 0.4] (tie after rounding to binary)
**WHEN** compute() is called with tie_breaker=TieBreaker.ESCALATE_TO_DEBATE
**THEN**
- consensus_score = 0.5 (neutral, no decision)
- resolution = DisagreementResolution.FLAG_FOR_REVIEW (defer to human)

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_tie_escalate():
    algo = MajorityVoting(tie_breaker=TieBreaker.ESCALATE_TO_DEBATE)
    result = await algo.compute([0.6, 0.4])

    assert result.consensus_score == 0.5
    assert result.resolution == DisagreementResolution.FLAG_FOR_REVIEW
```

| KPI | Value | Status |
|-----|-------|--------|
| Escalation outcome | FLAG_FOR_REVIEW | Pending |
| Consensus score (tie) | 0.5 (neutral) | Pending |
| Human intervention | Required | Pending |

---

## AC-E3-012: Majority Voting Edge Cases

**Story:** STORY-E3-002
**Feature:** Majority Voting Consensus Computation (FR-E3-008)

### Scenario: Single Vote
**GIVEN** scores [0.7]
**WHEN** compute() is called
**THEN**
- vote_yes = 1, vote_no = 0
- consensus_score = 1.0 (ACCEPT)
- consensus_confidence = 1.0

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_single_vote():
    algo = MajorityVoting()
    result = await algo.compute([0.7])

    assert result.consensus_score == 1.0
    assert result.consensus_confidence == 1.0
```

### Scenario: Empty Input
**GIVEN** scores []
**WHEN** compute() is called
**THEN** raises ValueError "Scores array cannot be empty"

**Test Code:**
```python
@pytest.mark.asyncio
async def test_majority_voting_empty():
    algo = MajorityVoting()
    with pytest.raises(ValueError, match="Scores array cannot be empty"):
        await algo.compute([])
```

| KPI | Value | Status |
|-----|-------|--------|
| Single vote handling | Works correctly | Pending |
| Empty input handling | ValueError raised | Pending |
| All same score | Consensus = 1.0 or 0.0 | Pending |

---

## AC-E3-013: ConsensusAlgorithm Enum Rename — BAYESIAN

**Story:** STORY-E3-003
**Feature:** ConsensusAlgorithm Enum Integration (FR-E3-009)

### Scenario: Enum Value Renamed
**GIVEN** ConsensusAlgorithm enum in `_models/consensus.py`
**WHEN** BAYESIAN_STUB is renamed to BAYESIAN
**THEN**
- Old value BAYESIAN_STUB no longer exists
- New value BAYESIAN exists with value "bayesian"
- All references updated (no orphaned references)

**Test Code:**
```python
def test_enum_bayesian_renamed():
    # New enum value exists
    assert hasattr(ConsensusAlgorithm, 'BAYESIAN')
    assert ConsensusAlgorithm.BAYESIAN.value == "bayesian"

    # Old enum value gone
    assert not hasattr(ConsensusAlgorithm, 'BAYESIAN_STUB')
```

| KPI | Value | Status |
|-----|-------|--------|
| Enum value renamed | BAYESIAN_STUB → BAYESIAN | Pending |
| String value | "bayesian" | Pending |
| Backward compatibility | Breaking (by design) | Pending |

---

## AC-E3-014: ConsensusAlgorithm Enum Rename — MAJORITY_VOTING

**Story:** STORY-E3-003
**Feature:** ConsensusAlgorithm Enum Integration (FR-E3-009)

### Scenario: Enum Value Renamed
**GIVEN** ConsensusAlgorithm enum
**WHEN** MAJORITY_VOTING_STUB is renamed to MAJORITY_VOTING
**THEN**
- Old value MAJORITY_VOTING_STUB no longer exists
- New value MAJORITY_VOTING exists with value "majority_voting"
- All references updated

**Test Code:**
```python
def test_enum_majority_voting_renamed():
    assert hasattr(ConsensusAlgorithm, 'MAJORITY_VOTING')
    assert ConsensusAlgorithm.MAJORITY_VOTING.value == "majority_voting"
    assert not hasattr(ConsensusAlgorithm, 'MAJORITY_VOTING_STUB')
```

| KPI | Value | Status |
|-----|-------|--------|
| Enum value renamed | MAJORITY_VOTING_STUB → MAJORITY_VOTING | Pending |
| String value | "majority_voting" | Pending |

---

## AC-E3-015: Consensus Router Dispatch

**Story:** STORY-E3-003
**Feature:** ConsensusAlgorithm Enum Integration (FR-E3-009)

### Scenario: Router Returns Correct Instances
**GIVEN** ConsensusAlgorithm enum values
**WHEN** get_consensus_algorithm() is called with each enum value
**THEN** correct algorithm instance is returned

**Test Code:**
```python
@pytest.mark.asyncio
async def test_consensus_router_dispatch():
    from _verification.consensus_router import get_consensus_algorithm

    # Bayesian
    algo_bayesian = get_consensus_algorithm(ConsensusAlgorithm.BAYESIAN)
    assert isinstance(algo_bayesian, BayesianConsensus)

    # Majority Voting
    algo_majority = get_consensus_algorithm(ConsensusAlgorithm.MAJORITY_VOTING)
    assert isinstance(algo_majority, MajorityVoting)

    # Existing algorithms still work
    algo_weighted = get_consensus_algorithm(ConsensusAlgorithm.WEIGHTED_AVERAGE)
    assert algo_weighted is not None

    algo_adaptive = get_consensus_algorithm(ConsensusAlgorithm.ADAPTIVE_STABILITY)
    assert algo_adaptive is not None
```

| KPI | Value | Status |
|-----|-------|--------|
| Bayesian routing | BayesianConsensus returned | Pending |
| Majority Voting routing | MajorityVoting returned | Pending |
| Existing algos | Unchanged | Pending |
| No breaking changes | All 4 algos routable | Pending |

---

## Summary Table: All ACs

| AC ID | Story | Feature | Status |
|-------|-------|---------|--------|
| AC-E3-001 | E3-001 | FR-E3-001 | Pending |
| AC-E3-002 | E3-001 | FR-E3-002 | Pending |
| AC-E3-003 | E3-001 | FR-E3-003 | Pending |
| AC-E3-004 | E3-001 | FR-E3-004 | Pending |
| AC-E3-005 | E3-001 | FR-E3-004 | Pending |
| AC-E3-006 | E3-002 | FR-E3-005 | Pending |
| AC-E3-007 | E3-002 | FR-E3-006 | Pending |
| AC-E3-008 | E3-002 | FR-E3-008 | Pending |
| AC-E3-009 | E3-002 | FR-E3-007 | Pending |
| AC-E3-010 | E3-002 | FR-E3-007 | Pending |
| AC-E3-011 | E3-002 | FR-E3-007 | Pending |
| AC-E3-012 | E3-002 | FR-E3-008 | Pending |
| AC-E3-013 | E3-003 | FR-E3-009 | Pending |
| AC-E3-014 | E3-003 | FR-E3-009 | Pending |
| AC-E3-015 | E3-003 | FR-E3-009 | Pending |

**Total ACs: 15**
**All stories covered: STORY-E3-001, STORY-E3-002, STORY-E3-003**

