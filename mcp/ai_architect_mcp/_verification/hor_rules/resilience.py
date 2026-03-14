"""HOR Rules 39-46: Error handling and concurrency checks."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from ai_architect_mcp._models.verification import (
    PENALTY_CRITICAL,
    PENALTY_WARNING,
    HORRuleResult,
    HORSeverity,
)

CATEGORY = "resilience"


def _make_result(rule_id: int, name: str, passed: bool, message: str, severity: HORSeverity) -> HORRuleResult:
    penalty = PENALTY_CRITICAL if severity == HORSeverity.CRITICAL else PENALTY_WARNING
    return HORRuleResult(rule_id=rule_id, rule_name=name, category=CATEGORY, passed=passed, message=message, severity=severity, penalty=penalty)


def rule_039_no_bare_except(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    if re.search(r"except\s*:", content):
        return _make_result(39, "no_bare_except", False, "Bare except found — catch specific exception types only", HORSeverity.CRITICAL)
    return _make_result(39, "no_bare_except", True, "No bare except clauses", HORSeverity.CRITICAL)


def rule_040_retry_logic(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_external = any(kw in content for kw in ["http", "api call", "external service", "network"])
    has_retry = any(kw in content for kw in ["retry", "backoff", "exponential", "tenacity"])
    if has_external and not has_retry:
        return _make_result(40, "retry_logic", False, "External calls without retry/backoff strategy", HORSeverity.WARNING)
    return _make_result(40, "retry_logic", True, "Retry logic documented or not applicable", HORSeverity.WARNING)


def rule_041_timeout_handling(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_external = any(kw in content for kw in ["http", "api", "external", "network", "database"])
    has_timeout = any(kw in content for kw in ["timeout", "deadline", "time_limit", "cancel"])
    if has_external and not has_timeout:
        return _make_result(41, "timeout_handling", False, "External operations without timeout handling", HORSeverity.WARNING)
    return _make_result(41, "timeout_handling", True, "Timeouts documented or not applicable", HORSeverity.WARNING)


def rule_042_circuit_breaker(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_external_service = any(kw in content for kw in ["microservice", "external service", "third-party", "downstream"])
    has_circuit = any(kw in content for kw in ["circuit breaker", "circuit_breaker", "bulkhead", "fallback"])
    if has_external_service and not has_circuit:
        return _make_result(42, "circuit_breaker", False, "External service dependency without circuit breaker pattern", HORSeverity.WARNING)
    return _make_result(42, "circuit_breaker", True, "Circuit breaker pattern addressed or not applicable", HORSeverity.WARNING)


def rule_043_graceful_degradation(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_dependency = any(kw in content for kw in ["dependency", "external", "service", "integration"])
    has_fallback = any(kw in content for kw in ["fallback", "graceful", "degrade", "offline", "cache"])
    if has_dependency and not has_fallback:
        return _make_result(43, "graceful_degradation", False, "Dependencies without fallback paths documented", HORSeverity.WARNING)
    return _make_result(43, "graceful_degradation", True, "Graceful degradation paths documented", HORSeverity.WARNING)


def rule_044_race_condition_prevention(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_concurrent = any(kw in content for kw in ["concurrent", "parallel", "thread", "async", "actor"])
    has_safety = any(kw in content for kw in ["lock", "mutex", "semaphore", "actor isolation", "sendable", "atomic", "serial queue"])
    if has_concurrent and not has_safety:
        return _make_result(44, "race_condition_prevention", False, "Concurrency without safety mechanisms documented", HORSeverity.CRITICAL)
    return _make_result(44, "race_condition_prevention", True, "Concurrency safety addressed", HORSeverity.CRITICAL)


def rule_045_atomicity(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_mutation = any(kw in content for kw in ["update", "write", "delete", "insert", "modify", "state change"])
    has_atomic = any(kw in content for kw in ["atomic", "transaction", "rollback", "compensat", "saga"])
    if has_mutation and not has_atomic:
        return _make_result(45, "atomicity", False, "State mutations without atomicity guarantees", HORSeverity.WARNING)
    return _make_result(45, "atomicity", True, "Atomicity addressed for state mutations", HORSeverity.WARNING)


def rule_046_deadlock_prevention(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_locks = any(kw in content for kw in ["lock", "mutex", "semaphore", "synchronized"])
    has_prevention = any(kw in content for kw in ["lock ordering", "actor", "deadlock", "timeout"])
    if has_locks and not has_prevention:
        return _make_result(46, "deadlock_prevention", False, "Lock usage without deadlock prevention strategy", HORSeverity.CRITICAL)
    return _make_result(46, "deadlock_prevention", True, "Deadlock prevention addressed or not applicable", HORSeverity.CRITICAL)


def get_rules() -> list[tuple[int, Callable[[dict[str, Any]], HORRuleResult], str, str, HORSeverity]]:
    return [
        (39, rule_039_no_bare_except, CATEGORY, "no_bare_except", HORSeverity.CRITICAL),
        (40, rule_040_retry_logic, CATEGORY, "retry_logic", HORSeverity.WARNING),
        (41, rule_041_timeout_handling, CATEGORY, "timeout_handling", HORSeverity.WARNING),
        (42, rule_042_circuit_breaker, CATEGORY, "circuit_breaker", HORSeverity.WARNING),
        (43, rule_043_graceful_degradation, CATEGORY, "graceful_degradation", HORSeverity.WARNING),
        (44, rule_044_race_condition_prevention, CATEGORY, "race_condition_prevention", HORSeverity.CRITICAL),
        (45, rule_045_atomicity, CATEGORY, "atomicity", HORSeverity.WARNING),
        (46, rule_046_deadlock_prevention, CATEGORY, "deadlock_prevention", HORSeverity.CRITICAL),
    ]
