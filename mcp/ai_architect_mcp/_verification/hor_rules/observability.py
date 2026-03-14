"""HOR Rules 59-64: Observability and dependencies checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ai_architect_mcp._models.verification import (
    PENALTY_CRITICAL,
    PENALTY_WARNING,
    HORRuleResult,
    HORSeverity,
)

CATEGORY = "observability"


def _make_result(rule_id: int, name: str, passed: bool, message: str, severity: HORSeverity) -> HORRuleResult:
    penalty = PENALTY_CRITICAL if severity == HORSeverity.CRITICAL else PENALTY_WARNING
    return HORRuleResult(rule_id=rule_id, rule_name=name, category=CATEGORY, passed=passed, message=message, severity=severity, penalty=penalty)


def rule_059_logging_strategy(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_service = any(kw in content for kw in ["service", "api", "endpoint", "module"])
    has_logging = any(kw in content for kw in ["logging", "log level", "structured log", "logger"])
    if has_service and not has_logging:
        return _make_result(59, "logging_strategy", False, "Service without logging strategy", HORSeverity.WARNING)
    return _make_result(59, "logging_strategy", True, "Logging strategy documented", HORSeverity.WARNING)


def rule_060_metrics_emission(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_ops = any(kw in content for kw in ["operation", "endpoint", "transaction", "request"])
    has_metrics = any(kw in content for kw in ["metric", "counter", "histogram", "gauge", "prometheus", "datadog"])
    if has_ops and not has_metrics:
        return _make_result(60, "metrics_emission", False, "Operations without metrics emission", HORSeverity.WARNING)
    return _make_result(60, "metrics_emission", True, "Metrics emission addressed", HORSeverity.WARNING)


def rule_061_alerting_thresholds(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_metrics = any(kw in content for kw in ["metric", "monitor", "sla", "slo"])
    has_alerting = any(kw in content for kw in ["alert", "threshold", "pager", "oncall", "notification"])
    if has_metrics and not has_alerting:
        return _make_result(61, "alerting_thresholds", False, "Monitoring without alerting thresholds", HORSeverity.WARNING)
    return _make_result(61, "alerting_thresholds", True, "Alerting thresholds defined", HORSeverity.WARNING)


def rule_062_trace_correlation(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_distributed = any(kw in content for kw in ["distributed", "microservice", "multi-service", "cross-service"])
    has_tracing = any(kw in content for kw in ["trace", "correlation id", "request id", "span", "opentelemetry"])
    if has_distributed and not has_tracing:
        return _make_result(62, "trace_correlation", False, "Distributed system without trace correlation", HORSeverity.WARNING)
    return _make_result(62, "trace_correlation", True, "Trace correlation addressed", HORSeverity.WARNING)


def rule_063_dependency_pinning(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_deps = any(kw in content for kw in ["dependency", "package", "library", "module"])
    has_pinning = any(kw in content for kw in ["pin", "lock", "exact version", ">=", "==", "requirements.txt", "package-lock"])
    if has_deps and not has_pinning:
        return _make_result(63, "dependency_pinning", False, "Dependencies without version pinning strategy", HORSeverity.WARNING)
    return _make_result(63, "dependency_pinning", True, "Dependency pinning addressed", HORSeverity.WARNING)


def rule_064_vulnerability_scanning(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_cicd = any(kw in content for kw in ["ci/cd", "pipeline", "github actions", "deployment"])
    has_scanning = any(kw in content for kw in ["vulnerability", "security scan", "dependabot", "snyk", "trivy", "audit"])
    if has_cicd and not has_scanning:
        return _make_result(64, "vulnerability_scanning", False, "CI/CD without security/vulnerability scanning", HORSeverity.WARNING)
    return _make_result(64, "vulnerability_scanning", True, "Vulnerability scanning addressed", HORSeverity.WARNING)


def get_rules() -> list[tuple[int, Callable[[dict[str, Any]], HORRuleResult], str, str, HORSeverity]]:
    return [
        (59, rule_059_logging_strategy, CATEGORY, "logging_strategy", HORSeverity.WARNING),
        (60, rule_060_metrics_emission, CATEGORY, "metrics_emission", HORSeverity.WARNING),
        (61, rule_061_alerting_thresholds, CATEGORY, "alerting_thresholds", HORSeverity.WARNING),
        (62, rule_062_trace_correlation, CATEGORY, "trace_correlation", HORSeverity.WARNING),
        (63, rule_063_dependency_pinning, CATEGORY, "dependency_pinning", HORSeverity.WARNING),
        (64, rule_064_vulnerability_scanning, CATEGORY, "vulnerability_scanning", HORSeverity.WARNING),
    ]
