"""HOR Rules 1-10: Core PRD structural checks.

Each rule is a pure function: artifact dict -> HORRuleResult.
Zero LLM calls. Deterministic pass/fail.
"""

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

CATEGORY = "structural"
REQUIRED_SECTIONS = [
    "Overview", "Requirements", "User Stories", "Technical",
    "Acceptance", "Roadmap", "Testing",
]
MAX_TITLE_LENGTH = 200
AC_PATTERN = re.compile(r"AC-(\d{3})")
FR_SOURCES = {"User Request", "Clarification", "Codebase", "Mockup"}


def _make_result(
    rule_id: int, name: str, passed: bool, message: str,
    severity: HORSeverity,
) -> HORRuleResult:
    """Create a HORRuleResult with correct penalty for severity."""
    penalty = (
        PENALTY_CRITICAL if severity == HORSeverity.CRITICAL
        else PENALTY_WARNING
    )
    return HORRuleResult(
        rule_id=rule_id, rule_name=name, category=CATEGORY,
        passed=passed, message=message, severity=severity, penalty=penalty,
    )


def rule_001_title_exists(artifact: dict[str, Any]) -> HORRuleResult:
    """Check that title is present, non-empty, and under 200 chars."""
    title = artifact.get("title", "")
    if not title or not title.strip():
        return _make_result(
            1, "title_exists", False,
            "Title is missing or empty", HORSeverity.CRITICAL,
        )
    if len(title) > MAX_TITLE_LENGTH:
        return _make_result(
            1, "title_exists", False,
            f"Title exceeds {MAX_TITLE_LENGTH} characters",
            HORSeverity.CRITICAL,
        )
    return _make_result(
        1, "title_exists", True,
        "Title present and within length limit", HORSeverity.CRITICAL,
    )


def rule_002_sections_present(artifact: dict[str, Any]) -> HORRuleResult:
    """Check that all 7 standard sections are present."""
    sections = artifact.get("sections", [])
    section_names = [
        s if isinstance(s, str) else s.get("name", "") for s in sections
    ]
    missing = [
        r for r in REQUIRED_SECTIONS
        if not any(r.lower() in s.lower() for s in section_names)
    ]
    if missing:
        return _make_result(
            2, "sections_present", False,
            f"Missing sections: {', '.join(missing)}",
            HORSeverity.CRITICAL,
        )
    return _make_result(
        2, "sections_present", True,
        "All required sections present", HORSeverity.CRITICAL,
    )


def rule_003_ac_numbering(artifact: dict[str, Any]) -> HORRuleResult:
    """Check AC-XXX format is sequential with no gaps."""
    content = artifact.get("content", "")
    matches = AC_PATTERN.findall(content)
    if not matches:
        return _make_result(
            3, "ac_numbering", True,
            "No AC references found (may be valid for non-PRD artifacts)",
            HORSeverity.WARNING,
        )
    numbers = sorted(int(m) for m in matches)
    expected = list(range(numbers[0], numbers[0] + len(numbers)))
    if numbers != expected:
        return _make_result(
            3, "ac_numbering", False,
            f"AC numbering has gaps: found {numbers}, expected {expected}",
            HORSeverity.WARNING,
        )
    return _make_result(
        3, "ac_numbering", True,
        f"AC numbering sequential: AC-{numbers[0]:03d} to AC-{numbers[-1]:03d}",
        HORSeverity.WARNING,
    )


def rule_004_no_orphan_ddl(artifact: dict[str, Any]) -> HORRuleResult:
    """Check every CREATE TYPE/TABLE is referenced elsewhere."""
    content = artifact.get("content", "")
    creates = re.findall(
        r"CREATE\s+(?:TYPE|TABLE)\s+(\w+)", content, re.IGNORECASE,
    )
    if not creates:
        return _make_result(
            4, "no_orphan_ddl", True,
            "No DDL statements found", HORSeverity.WARNING,
        )
    orphans = [name for name in creates if content.count(name) < 2]
    if orphans:
        return _make_result(
            4, "no_orphan_ddl", False,
            f"Orphan DDL: {', '.join(orphans)} defined but never referenced",
            HORSeverity.WARNING,
        )
    return _make_result(
        4, "no_orphan_ddl", True,
        "All DDL definitions referenced", HORSeverity.WARNING,
    )


def rule_005_no_volatile_indexes(artifact: dict[str, Any]) -> HORRuleResult:
    """Check no NOW() in partial index predicates."""
    content = artifact.get("content", "")
    if re.search(r"(?:CREATE\s+INDEX|WHERE).*NOW\(\)", content, re.IGNORECASE):
        return _make_result(
            5, "no_volatile_indexes", False,
            "NOW() found in index predicate — use immutable expressions",
            HORSeverity.CRITICAL,
        )
    return _make_result(
        5, "no_volatile_indexes", True,
        "No volatile functions in index predicates", HORSeverity.CRITICAL,
    )


def rule_006_fr_traceability(artifact: dict[str, Any]) -> HORRuleResult:
    """Check every FR traces to a source."""
    requirements = artifact.get("requirements", [])
    if not requirements:
        return _make_result(
            6, "fr_traceability", True,
            "No functional requirements found", HORSeverity.WARNING,
        )
    untraceable = [
        r.get("id", "?") for r in requirements
        if isinstance(r, dict) and r.get("source") not in FR_SOURCES
    ]
    if untraceable:
        return _make_result(
            6, "fr_traceability", False,
            f"FRs without valid source: {', '.join(untraceable)}",
            HORSeverity.WARNING,
        )
    return _make_result(
        6, "fr_traceability", True,
        "All FRs trace to valid sources", HORSeverity.WARNING,
    )


def rule_007_no_placeholder_tests(artifact: dict[str, Any]) -> HORRuleResult:
    """Check test functions have implementation bodies."""
    content = artifact.get("content", "")
    placeholders = re.findall(
        r"(?:def\s+test_\w+.*?:)\s*(?:pass|\.\.\.)\s*$",
        content, re.MULTILINE,
    )
    if placeholders:
        return _make_result(
            7, "no_placeholder_tests", False,
            f"Found {len(placeholders)} placeholder test(s) with pass/... body",
            HORSeverity.CRITICAL,
        )
    return _make_result(
        7, "no_placeholder_tests", True,
        "No placeholder tests found", HORSeverity.CRITICAL,
    )


def rule_008_sp_not_in_fr_table(artifact: dict[str, Any]) -> HORRuleResult:
    """Check SP column absent from FR table."""
    content = artifact.get("content", "")
    if re.search(r"\|\s*FR-\d+\s*\|.*\|\s*\d+\s*SP\s*\|", content):
        return _make_result(
            8, "sp_not_in_fr_table", False,
            "Story Points found in FR table — SP belongs in sprint planning",
            HORSeverity.WARNING,
        )
    return _make_result(
        8, "sp_not_in_fr_table", True,
        "FR table does not contain SP column", HORSeverity.WARNING,
    )


def rule_009_uneven_sp_distribution(
    artifact: dict[str, Any],
) -> HORRuleResult:
    """Check sprint SP not evenly distributed (sign of fake estimates)."""
    sprints = artifact.get("sprints", [])
    if len(sprints) < 2:
        return _make_result(
            9, "uneven_sp_distribution", True,
            "Fewer than 2 sprints — distribution check not applicable",
            HORSeverity.WARNING,
        )
    points = [
        s.get("story_points", 0) for s in sprints if isinstance(s, dict)
    ]
    if len(set(points)) == 1 and len(points) > 2:
        return _make_result(
            9, "uneven_sp_distribution", False,
            "All sprints have identical SP — likely fake estimates",
            HORSeverity.WARNING,
        )
    return _make_result(
        9, "uneven_sp_distribution", True,
        "Sprint SP distribution appears realistic", HORSeverity.WARNING,
    )


def rule_010_verification_metrics_disclaimer(
    artifact: dict[str, Any],
) -> HORRuleResult:
    """Check projected metrics labeled as such."""
    content = artifact.get("content", "")
    has_metrics = bool(re.search(r"\d+%|\d+\.\d+", content))
    if has_metrics:
        disclaimers = ["projected", "estimated", "expected", "approximate"]
        if not any(word in content.lower() for word in disclaimers):
            return _make_result(
                10, "verification_metrics_disclaimer", False,
                "Metrics found without projected/estimated disclaimer",
                HORSeverity.WARNING,
            )
    return _make_result(
        10, "verification_metrics_disclaimer", True,
        "Metrics properly labeled or no metrics present",
        HORSeverity.WARNING,
    )


def get_rules() -> list[
    tuple[int, Callable[[dict[str, Any]], HORRuleResult], str, str, HORSeverity]
]:
    """Return all rules in this module for auto-discovery."""
    return [
        (1, rule_001_title_exists, CATEGORY, "title_exists", HORSeverity.CRITICAL),
        (2, rule_002_sections_present, CATEGORY, "sections_present", HORSeverity.CRITICAL),
        (3, rule_003_ac_numbering, CATEGORY, "ac_numbering", HORSeverity.WARNING),
        (4, rule_004_no_orphan_ddl, CATEGORY, "no_orphan_ddl", HORSeverity.WARNING),
        (5, rule_005_no_volatile_indexes, CATEGORY, "no_volatile_indexes", HORSeverity.CRITICAL),
        (6, rule_006_fr_traceability, CATEGORY, "fr_traceability", HORSeverity.WARNING),
        (7, rule_007_no_placeholder_tests, CATEGORY, "no_placeholder_tests", HORSeverity.CRITICAL),
        (8, rule_008_sp_not_in_fr_table, CATEGORY, "sp_not_in_fr_table", HORSeverity.WARNING),
        (9, rule_009_uneven_sp_distribution, CATEGORY, "uneven_sp_distribution", HORSeverity.WARNING),
        (10, rule_010_verification_metrics_disclaimer, CATEGORY, "verification_metrics_disclaimer", HORSeverity.WARNING),
    ]
