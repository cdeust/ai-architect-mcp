"""HOR Rules 24-30: Architecture and code quality checks."""

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

CATEGORY = "architecture"
BANNED_SUFFIXES = ["Utils", "Helper", "Helpers", "Manager", "Handler", "Processor"]
MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 40


def _make_result(rule_id: int, name: str, passed: bool, message: str, severity: HORSeverity) -> HORRuleResult:
    penalty = PENALTY_CRITICAL if severity == HORSeverity.CRITICAL else PENALTY_WARNING
    return HORRuleResult(rule_id=rule_id, rule_name=name, category=CATEGORY, passed=passed, message=message, severity=severity, penalty=penalty)


def rule_024_dependency_direction(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    violations = re.findall(r"(?:Domain|Model)\s*(?:import|depend|reference).*(?:Presentation|UI|View)", content, re.IGNORECASE)
    if violations:
        return _make_result(24, "dependency_direction", False, "Domain layer depends on Presentation layer — violates dependency rule", HORSeverity.CRITICAL)
    return _make_result(24, "dependency_direction", True, "Dependency direction correct: Domain <- Presentation <- Infrastructure", HORSeverity.CRITICAL)


def rule_025_no_god_objects(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    found = [s for s in BANNED_SUFFIXES if re.search(rf"\b\w+{s}\b", content)]
    if found:
        return _make_result(25, "no_god_objects", False, f"God-object names found: {', '.join(found)} — name things for what they do", HORSeverity.CRITICAL)
    return _make_result(25, "no_god_objects", True, "No god-object naming patterns", HORSeverity.CRITICAL)


def rule_026_file_size_limit(artifact: dict[str, Any]) -> HORRuleResult:
    files = artifact.get("files", [])
    oversized = [f.get("path", "?") for f in files if isinstance(f, dict) and f.get("lines", 0) > MAX_FILE_LINES]
    if oversized:
        return _make_result(26, "file_size_limit", False, f"Files exceeding {MAX_FILE_LINES} lines: {', '.join(oversized[:5])}", HORSeverity.CRITICAL)
    return _make_result(26, "file_size_limit", True, f"All files within {MAX_FILE_LINES}-line limit", HORSeverity.CRITICAL)


def rule_027_function_length(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    code_blocks = re.findall(r"```[\s\S]*?```", content)
    for block in code_blocks:
        functions = re.split(r"\n(?:def |func |fn )", block)
        for func in functions[1:]:
            lines = [l for l in func.split("\n") if l.strip() and not l.strip().startswith(("#", "//"))]
            if len(lines) > MAX_FUNCTION_LINES:
                return _make_result(27, "function_length", False, f"Function exceeds {MAX_FUNCTION_LINES} logical lines", HORSeverity.WARNING)
    return _make_result(27, "function_length", True, f"All functions within {MAX_FUNCTION_LINES}-line limit", HORSeverity.WARNING)


def rule_028_one_type_per_file(artifact: dict[str, Any]) -> HORRuleResult:
    files = artifact.get("files", [])
    for f in files:
        if isinstance(f, dict) and f.get("public_types", 0) > 1:
            return _make_result(28, "one_type_per_file", False, f"File {f.get('path', '?')} has {f['public_types']} public types", HORSeverity.CRITICAL)
    return _make_result(28, "one_type_per_file", True, "All files have at most one public type", HORSeverity.CRITICAL)


def rule_029_no_backward_compat_hacks(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "")
    hacks = re.findall(r"(?:typealias|@available\s*\(\s*\*\s*,\s*deprecated|#if\s+swift)", content)
    if hacks:
        return _make_result(29, "no_backward_compat_hacks", False, "Backward-compatibility hacks found — remove and update directly", HORSeverity.CRITICAL)
    return _make_result(29, "no_backward_compat_hacks", True, "No backward-compatibility hacks", HORSeverity.CRITICAL)


def rule_030_solid_compliance(artifact: dict[str, Any]) -> HORRuleResult:
    content = artifact.get("content", "").lower()
    solid = {"srp": "single responsibility", "ocp": "open/closed", "lsp": "liskov", "isp": "interface segregation", "dip": "dependency inversion"}
    missing = [abbr for abbr, full in solid.items() if abbr.lower() not in content and full not in content]
    if len(missing) > 2:
        return _make_result(30, "solid_compliance", False, f"SOLID principles not addressed: {', '.join(missing)}", HORSeverity.WARNING)
    return _make_result(30, "solid_compliance", True, "SOLID principles addressed in tech spec", HORSeverity.WARNING)


def get_rules() -> list[tuple[int, Callable[[dict[str, Any]], HORRuleResult], str, str, HORSeverity]]:
    return [
        (24, rule_024_dependency_direction, CATEGORY, "dependency_direction", HORSeverity.CRITICAL),
        (25, rule_025_no_god_objects, CATEGORY, "no_god_objects", HORSeverity.CRITICAL),
        (26, rule_026_file_size_limit, CATEGORY, "file_size_limit", HORSeverity.CRITICAL),
        (27, rule_027_function_length, CATEGORY, "function_length", HORSeverity.WARNING),
        (28, rule_028_one_type_per_file, CATEGORY, "one_type_per_file", HORSeverity.CRITICAL),
        (29, rule_029_no_backward_compat_hacks, CATEGORY, "no_backward_compat_hacks", HORSeverity.CRITICAL),
        (30, rule_030_solid_compliance, CATEGORY, "solid_compliance", HORSeverity.WARNING),
    ]
