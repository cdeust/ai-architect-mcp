"""HOR Rules 47-58: Senior quality and testing checks."""

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

CATEGORY = "quality"


def _make_result(rule_id: int, name: str, passed: bool, message: str, severity: HORSeverity) -> HORRuleResult:
    penalty = PENALTY_CRITICAL if severity == HORSeverity.CRITICAL else PENALTY_WARNING
    return HORRuleResult(rule_id=rule_id, rule_name=name, category=CATEGORY, passed=passed, message=message, severity=severity, penalty=penalty)


def rule_047_naming_conventions(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    abbreviations = re.findall(r"\b(?:mgr|svc|impl|util|tmp|usr|btn|lbl)\b", content, re.IGNORECASE)
    if abbreviations:
        return _make_result(47, "naming_conventions", False, f"Non-descriptive abbreviations: {', '.join(set(abbreviations)[:5])}", HORSeverity.WARNING)
    return _make_result(47, "naming_conventions", True, "Naming conventions followed", HORSeverity.WARNING)


def rule_048_complexity_limit(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_complex = any(kw in content for kw in ["complex", "nested", "deeply"])
    has_addressed = any(kw in content for kw in ["cyclomatic", "complexity limit", "extract", "refactor", "simplif"])
    if has_complex and not has_addressed:
        return _make_result(48, "complexity_limit", False, "Complexity concerns without mitigation strategy", HORSeverity.WARNING)
    return _make_result(48, "complexity_limit", True, "Complexity addressed", HORSeverity.WARNING)


def rule_049_duplication_prevention(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_duplication = any(kw in content for kw in ["duplicate", "copy", "similar code"])
    has_dry = any(kw in content for kw in ["dry", "don't repeat", "shared", "common", "extract", "reuse"])
    if has_duplication and not has_dry:
        return _make_result(49, "duplication_prevention", False, "Duplication identified without DRY strategy", HORSeverity.WARNING)
    return _make_result(49, "duplication_prevention", True, "DRY principle addressed", HORSeverity.WARNING)


def rule_050_type_safety(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    code_blocks = re.findall(r"```(?:python|swift|typescript)[\s\S]*?```", content)
    for block in code_blocks:
        if "Any" in block and "type hint" not in block.lower():
            return _make_result(50, "type_safety", False, "Code uses 'Any' type — provide specific type hints", HORSeverity.WARNING)
    return _make_result(50, "type_safety", True, "Type safety maintained in code examples", HORSeverity.WARNING)


def rule_051_documentation(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_public_api = any(kw in content for kw in ["public func", "public class", "def ", "export"])
    has_docs = any(kw in content for kw in ["docstring", "documentation", "/// ", '"""', "jsdoc"])
    if has_public_api and not has_docs:
        return _make_result(51, "documentation", False, "Public API without documentation requirements", HORSeverity.WARNING)
    return _make_result(51, "documentation", True, "Documentation requirements addressed", HORSeverity.WARNING)


def rule_052_no_todo_in_production(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    todos = re.findall(r"\b(?:TODO|FIXME|HACK|XXX)\b", content)
    if todos:
        return _make_result(52, "no_todo_in_production", False, f"Found {len(todos)} TODO/FIXME/HACK markers in production code", HORSeverity.CRITICAL)
    return _make_result(52, "no_todo_in_production", True, "No TODO/FIXME/HACK markers", HORSeverity.CRITICAL)


def rule_053_test_coverage_requirement(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_testing = "test" in content
    has_coverage = any(kw in content for kw in ["coverage", "80%", "90%", "100%", "threshold"])
    if has_testing and not has_coverage:
        return _make_result(53, "test_coverage_requirement", False, "Testing section without coverage targets", HORSeverity.WARNING)
    return _make_result(53, "test_coverage_requirement", True, "Coverage targets specified", HORSeverity.WARNING)


def rule_054_edge_case_testing(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_testing = "test" in content
    has_edge = any(kw in content for kw in ["edge case", "boundary", "corner case", "empty", "null", "zero", "overflow"])
    if has_testing and not has_edge:
        return _make_result(54, "edge_case_testing", False, "Testing section without edge case coverage", HORSeverity.WARNING)
    return _make_result(54, "edge_case_testing", True, "Edge cases addressed in testing", HORSeverity.WARNING)


def rule_055_integration_testing(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_components = any(kw in content for kw in ["module", "service", "component", "layer"])
    has_integration = any(kw in content for kw in ["integration test", "end-to-end", "e2e", "system test"])
    if has_components and not has_integration:
        return _make_result(55, "integration_testing", False, "Multiple components without integration test strategy", HORSeverity.WARNING)
    return _make_result(55, "integration_testing", True, "Integration testing addressed", HORSeverity.WARNING)


def rule_056_performance_testing(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    nfrs = artifact.get("nfrs", [])
    has_perf_nfr = nfrs or any(kw in content for kw in ["performance", "latency", "throughput", "response time"])
    has_perf_test = any(kw in content for kw in ["benchmark", "load test", "performance test", "stress test"])
    if has_perf_nfr and not has_perf_test:
        return _make_result(56, "performance_testing", False, "Performance requirements without test methodology", HORSeverity.WARNING)
    return _make_result(56, "performance_testing", True, "Performance testing addressed", HORSeverity.WARNING)


def rule_057_regression_testing(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_testing = "test" in content
    has_regression = any(kw in content for kw in ["regression", "ci/cd", "continuous", "automated test", "pipeline"])
    if has_testing and not has_regression:
        return _make_result(57, "regression_testing", False, "Testing without regression prevention strategy", HORSeverity.WARNING)
    return _make_result(57, "regression_testing", True, "Regression prevention addressed", HORSeverity.WARNING)


def rule_058_test_isolation(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    has_testing = "test" in content
    has_isolation = any(kw in content for kw in ["isolat", "independent", "no shared state", "fixture", "setup", "teardown"])
    if has_testing and not has_isolation:
        return _make_result(58, "test_isolation", False, "Tests without isolation strategy", HORSeverity.WARNING)
    return _make_result(58, "test_isolation", True, "Test isolation addressed", HORSeverity.WARNING)


def get_rules() -> list[tuple[int, Callable[[dict[str, Any]], HORRuleResult], str, str, HORSeverity]]:
    return [
        (47, rule_047_naming_conventions, CATEGORY, "naming_conventions", HORSeverity.WARNING),
        (48, rule_048_complexity_limit, CATEGORY, "complexity_limit", HORSeverity.WARNING),
        (49, rule_049_duplication_prevention, CATEGORY, "duplication_prevention", HORSeverity.WARNING),
        (50, rule_050_type_safety, CATEGORY, "type_safety", HORSeverity.WARNING),
        (51, rule_051_documentation, CATEGORY, "documentation", HORSeverity.WARNING),
        (52, rule_052_no_todo_in_production, CATEGORY, "no_todo_in_production", HORSeverity.CRITICAL),
        (53, rule_053_test_coverage_requirement, CATEGORY, "test_coverage_requirement", HORSeverity.WARNING),
        (54, rule_054_edge_case_testing, CATEGORY, "edge_case_testing", HORSeverity.WARNING),
        (55, rule_055_integration_testing, CATEGORY, "integration_testing", HORSeverity.WARNING),
        (56, rule_056_performance_testing, CATEGORY, "performance_testing", HORSeverity.WARNING),
        (57, rule_057_regression_testing, CATEGORY, "regression_testing", HORSeverity.WARNING),
        (58, rule_058_test_isolation, CATEGORY, "test_isolation", HORSeverity.WARNING),
    ]
