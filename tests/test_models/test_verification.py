"""Tests for verification models — verdict enum, confidence validators, penalties."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from ai_architect_mcp._models.verification import (
    PENALTY_CRITICAL,
    PENALTY_WARNING,
    ClaimEvaluation,
    ClaimSource,
    ClaimType,
    HORRuleResult,
    HORSeverity,
    Verdict,
    VerificationClaim,
    VerificationReport,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestVerdict:
    """Test Verdict enum."""

    def test_all_verdicts_present(self) -> None:
        assert len(Verdict) == 5

    def test_verdict_values(self) -> None:
        expected = {"pass", "spec_complete", "needs_runtime", "inconclusive", "fail"}
        assert {v.value for v in Verdict} == expected


class TestVerificationClaim:
    """Test VerificationClaim model."""

    def test_valid_claim(self) -> None:
        claim = VerificationClaim(
            content="The system supports authentication",
            claim_type=ClaimType.ATOMIC_FACT,
            source=ClaimSource.DECOMPOSITION,
            priority=50,
        )
        assert claim.content == "The system supports authentication"
        assert claim.claim_id is not None

    def test_priority_below_min_rejected(self) -> None:
        with pytest.raises(ValueError):
            VerificationClaim(
                content="test",
                claim_type=ClaimType.ATOMIC_FACT,
                source=ClaimSource.GENERATION,
                priority=0,
            )

    def test_priority_above_max_rejected(self) -> None:
        with pytest.raises(ValueError):
            VerificationClaim(
                content="test",
                claim_type=ClaimType.ATOMIC_FACT,
                source=ClaimSource.GENERATION,
                priority=101,
            )


class TestClaimEvaluation:
    """Test ClaimEvaluation model."""

    def test_valid_evaluation(self) -> None:
        eval_result = ClaimEvaluation(
            claim_id=uuid4(),
            evaluator_id="nli_evaluator",
            score=0.95,
            confidence=0.88,
            verdict=Verdict.PASS,
            reasoning="Claim is entailed by the premise",
        )
        assert eval_result.score == 0.95

    def test_score_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError):
            ClaimEvaluation(
                claim_id=uuid4(),
                evaluator_id="test",
                score=1.5,
                confidence=0.5,
                verdict=Verdict.PASS,
                reasoning="test",
            )

    def test_confidence_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError):
            ClaimEvaluation(
                claim_id=uuid4(),
                evaluator_id="test",
                score=0.5,
                confidence=-0.1,
                verdict=Verdict.PASS,
                reasoning="test",
            )


class TestHORRuleResult:
    """Test HORRuleResult model."""

    def test_critical_penalty(self) -> None:
        result = HORRuleResult(
            rule_id=1,
            rule_name="title_exists",
            category="structural",
            passed=False,
            message="Title missing",
            severity=HORSeverity.CRITICAL,
            penalty=PENALTY_CRITICAL,
        )
        assert result.penalty == 0.15

    def test_warning_penalty(self) -> None:
        result = HORRuleResult(
            rule_id=10,
            rule_name="verification_metrics_disclaimer",
            category="structural",
            passed=False,
            message="Metrics not labeled as projected",
            severity=HORSeverity.WARNING,
            penalty=PENALTY_WARNING,
        )
        assert result.penalty == 0.05

    def test_mismatched_penalty_rejected(self) -> None:
        with pytest.raises(ValueError, match="does not match severity"):
            HORRuleResult(
                rule_id=1,
                rule_name="test",
                category="structural",
                passed=False,
                message="test",
                severity=HORSeverity.CRITICAL,
                penalty=0.05,
            )

    def test_rule_id_boundaries(self) -> None:
        for rule_id in [1, 64]:
            result = HORRuleResult(
                rule_id=rule_id,
                rule_name="test",
                category="structural",
                passed=True,
                message="passed",
                severity=HORSeverity.WARNING,
                penalty=PENALTY_WARNING,
            )
            assert result.rule_id == rule_id

    def test_rule_id_out_of_range(self) -> None:
        with pytest.raises(ValueError):
            HORRuleResult(
                rule_id=65,
                rule_name="test",
                category="structural",
                passed=True,
                message="passed",
                severity=HORSeverity.WARNING,
                penalty=PENALTY_WARNING,
            )


class TestVerificationReport:
    """Test VerificationReport model."""

    def test_valid_report(self) -> None:
        report = VerificationReport(
            overall_score=0.85,
            algorithm_used="weighted_average",
        )
        assert report.overall_score == 0.85
        assert report.claims == []
        assert report.hor_results == []

    def test_score_out_of_range(self) -> None:
        with pytest.raises(ValueError):
            VerificationReport(
                overall_score=1.5,
                algorithm_used="test",
            )

    def test_serialization_round_trip(self) -> None:
        report = VerificationReport(
            overall_score=0.72,
            algorithm_used="graph_constrained",
        )
        dumped = report.model_dump(mode="json")
        restored = VerificationReport.model_validate(dumped)
        assert restored.overall_score == report.overall_score

    def test_fixture_full_report(self) -> None:
        fixture_path = FIXTURES_DIR / "verification_report_full.json"
        if fixture_path.exists():
            data = json.loads(fixture_path.read_text())
            report = VerificationReport.model_validate(data)
            assert report.overall_score >= 0.0
