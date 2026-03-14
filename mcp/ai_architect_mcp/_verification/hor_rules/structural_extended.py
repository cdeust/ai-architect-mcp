"""HOR Rules 11-23: Extended structural checks.

Pure functions: artifact dict -> HORRuleResult. Zero LLM calls.
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

CATEGORY = "structural_extended"


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


def rule_011_cross_ref_consistency(artifact: dict[str, Any]) -> HORRuleResult:
    """Check all cross-references resolve to defined IDs."""
    content = artifact.get("content", "")
    refs = re.findall(
        r"(?:see|ref|refer to)\s+((?:FR|AC|STORY)-\d+)",
        content, re.IGNORECASE,
    )
    defined = set(re.findall(r"((?:FR|AC|STORY)-\d+)", content))
    broken = [r for r in refs if r not in defined]
    if broken:
        return _make_result(
            11, "cross_ref_consistency", False,
            f"Broken cross-references: {', '.join(broken)}",
            HORSeverity.WARNING,
        )
    return _make_result(
        11, "cross_ref_consistency", True,
        "All cross-references resolve", HORSeverity.WARNING,
    )


def rule_012_clean_architecture(artifact: dict[str, Any]) -> HORRuleResult:
    """Check tech spec references clean architecture patterns."""
    content = artifact.get("content", "")
    has_tech = "technical" in content.lower() or "architecture" in content.lower()
    keywords = ["port", "adapter", "interface", "protocol", "abstraction"]
    if has_tech and not any(kw in content.lower() for kw in keywords):
        return _make_result(
            12, "clean_architecture", False,
            "Tech spec lacks ports/adapters pattern references",
            HORSeverity.WARNING,
        )
    return _make_result(
        12, "clean_architecture", True,
        "Clean architecture patterns referenced", HORSeverity.WARNING,
    )


def rule_013_self_check_reported(artifact: dict[str, Any]) -> HORRuleResult:
    """Check post-generation self-check results are present."""
    has_self_check = (
        artifact.get("self_check", None) is not None
        or "self-check" in artifact.get("content", "").lower()
    )
    if not has_self_check:
        return _make_result(
            13, "self_check_reported", False,
            "Post-generation self-check results missing",
            HORSeverity.WARNING,
        )
    return _make_result(
        13, "self_check_reported", True,
        "Self-check results present", HORSeverity.WARNING,
    )


def rule_014_codebase_analysis_present(artifact: dict[str, Any]) -> HORRuleResult:
    """Check codebase analysis present when codebase was provided."""
    has_codebase = artifact.get("codebase_provided", False)
    has_analysis = (
        "codebase analysis" in artifact.get("content", "").lower()
        or artifact.get("codebase_analysis") is not None
    )
    if has_codebase and not has_analysis:
        return _make_result(
            14, "codebase_analysis_present", False,
            "Codebase provided but no analysis found",
            HORSeverity.WARNING,
        )
    return _make_result(
        14, "codebase_analysis_present", True,
        "Codebase analysis present or not required", HORSeverity.WARNING,
    )


def rule_015_honest_verdicts(artifact: dict[str, Any]) -> HORRuleResult:
    """Check verdict distribution is not suspiciously uniform."""
    verdicts = artifact.get("verdicts", [])
    if len(verdicts) > 5 and all(v == "pass" for v in verdicts):
        return _make_result(
            15, "honest_verdicts", False,
            "All claims PASS — likely confirmatory bias",
            HORSeverity.CRITICAL,
        )
    return _make_result(
        15, "honest_verdicts", True,
        "Verdict distribution appears honest", HORSeverity.CRITICAL,
    )


def rule_016_code_matches_architecture(artifact: dict[str, Any]) -> HORRuleResult:
    """Check code examples use injected ports, not direct system calls."""
    content = artifact.get("content", "")
    code_blocks = re.findall(r"```[\s\S]*?```", content)
    for block in code_blocks:
        if re.search(r"(?:import\s+subprocess|os\.system|shutil)", block):
            return _make_result(
                16, "code_matches_architecture", False,
                "Code example uses direct system calls instead of injected ports",
                HORSeverity.CRITICAL,
            )
    return _make_result(
        16, "code_matches_architecture", True,
        "Code examples use injected ports", HORSeverity.CRITICAL,
    )


def rule_017_test_traceability(artifact: dict[str, Any]) -> HORRuleResult:
    """Check all tests trace to acceptance criteria."""
    tests = artifact.get("tests", [])
    if not tests:
        return _make_result(
            17, "test_traceability", True,
            "No test section found", HORSeverity.WARNING,
        )
    untraceable = [
        t.get("name", "?") for t in tests
        if isinstance(t, dict) and not t.get("traces_to")
    ]
    if untraceable:
        return _make_result(
            17, "test_traceability", False,
            f"Tests without AC mapping: {', '.join(untraceable[:5])}",
            HORSeverity.WARNING,
        )
    return _make_result(
        17, "test_traceability", True,
        "All tests trace to acceptance criteria", HORSeverity.WARNING,
    )


def rule_018_generic_over_specific(artifact: dict[str, Any]) -> HORRuleResult:
    """Check tech spec designs for general case, not specific."""
    content = artifact.get("content", "")
    patterns = re.findall(
        r"(?:hardcode|hard-code|magic\s+number|specific\s+to\s+\w+)",
        content, re.IGNORECASE,
    )
    if patterns:
        return _make_result(
            18, "generic_over_specific", False,
            f"Found specificity anti-patterns: {', '.join(patterns[:3])}",
            HORSeverity.WARNING,
        )
    return _make_result(
        18, "generic_over_specific", True,
        "Tech spec designs for general case", HORSeverity.WARNING,
    )


def rule_019_no_nested_types(artifact: dict[str, Any]) -> HORRuleResult:
    """Check no nested type definitions in code examples."""
    content = artifact.get("content", "")
    nested = re.findall(
        r"(?:struct|class|enum)\s+\w+\s*\{[^}]*(?:struct|class|enum)\s+\w+",
        content,
    )
    if nested:
        return _make_result(
            19, "no_nested_types", False,
            f"Found {len(nested)} nested type definition(s)",
            HORSeverity.CRITICAL,
        )
    return _make_result(
        19, "no_nested_types", True,
        "No nested types found", HORSeverity.CRITICAL,
    )


def rule_020_single_responsibility(artifact: dict[str, Any]) -> HORRuleResult:
    """Check code examples stay under line limit."""
    content = artifact.get("content", "")
    code_blocks = re.findall(r"```[\s\S]*?```", content)
    for block in code_blocks:
        lines = [
            line for line in block.split("\n")
            if line.strip() and not line.strip().startswith(("//", "#", "```"))
        ]
        if len(lines) > 50:
            return _make_result(
                20, "single_responsibility", False,
                f"Code example has {len(lines)} lines — exceeds ~50 line guideline",
                HORSeverity.WARNING,
            )
    return _make_result(
        20, "single_responsibility", True,
        "Code examples under line limit", HORSeverity.WARNING,
    )


def rule_021_no_self_referencing_deps(artifact: dict[str, Any]) -> HORRuleResult:
    """Check no story depends on itself."""
    stories = artifact.get("stories", [])
    for story in stories:
        if isinstance(story, dict):
            story_id = story.get("id", "")
            deps = story.get("depends_on", [])
            if story_id and story_id in deps:
                return _make_result(
                    21, "no_self_referencing_deps", False,
                    f"Story {story_id} depends on itself",
                    HORSeverity.CRITICAL,
                )
    return _make_result(
        21, "no_self_referencing_deps", True,
        "No self-referencing dependencies", HORSeverity.CRITICAL,
    )


def rule_022_id_coverage(artifact: dict[str, Any]) -> HORRuleResult:
    """Check all ID sequences are continuous with no gaps."""
    content = artifact.get("content", "")
    for prefix in ["FR", "AC", "STORY"]:
        ids = sorted(set(int(m) for m in re.findall(rf"{prefix}-(\d+)", content)))
        if ids and ids != list(range(ids[0], ids[0] + len(ids))):
            return _make_result(
                22, "id_coverage", False,
                f"{prefix} IDs have gaps: {ids}", HORSeverity.WARNING,
            )
    return _make_result(
        22, "id_coverage", True,
        "All ID sequences continuous", HORSeverity.WARNING,
    )


def rule_023_toc_present(artifact: dict[str, Any]) -> HORRuleResult:
    """Check documents with many sections have a table of contents."""
    content = artifact.get("content", "")
    has_toc = (
        "table of contents" in content.lower()
        or "## contents" in content.lower()
    )
    sections = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
    if len(sections) > 5 and not has_toc:
        return _make_result(
            23, "toc_present", False,
            "Document has 5+ sections but no table of contents",
            HORSeverity.WARNING,
        )
    return _make_result(
        23, "toc_present", True,
        "Table of contents present or not needed", HORSeverity.WARNING,
    )


def get_rules() -> list[
    tuple[int, Callable[[dict[str, Any]], HORRuleResult], str, str, HORSeverity]
]:
    """Return all rules in this module for auto-discovery."""
    return [
        (11, rule_011_cross_ref_consistency, CATEGORY, "cross_ref_consistency", HORSeverity.WARNING),
        (12, rule_012_clean_architecture, CATEGORY, "clean_architecture", HORSeverity.WARNING),
        (13, rule_013_self_check_reported, CATEGORY, "self_check_reported", HORSeverity.WARNING),
        (14, rule_014_codebase_analysis_present, CATEGORY, "codebase_analysis_present", HORSeverity.WARNING),
        (15, rule_015_honest_verdicts, CATEGORY, "honest_verdicts", HORSeverity.CRITICAL),
        (16, rule_016_code_matches_architecture, CATEGORY, "code_matches_architecture", HORSeverity.CRITICAL),
        (17, rule_017_test_traceability, CATEGORY, "test_traceability", HORSeverity.WARNING),
        (18, rule_018_generic_over_specific, CATEGORY, "generic_over_specific", HORSeverity.WARNING),
        (19, rule_019_no_nested_types, CATEGORY, "no_nested_types", HORSeverity.CRITICAL),
        (20, rule_020_single_responsibility, CATEGORY, "single_responsibility", HORSeverity.WARNING),
        (21, rule_021_no_self_referencing_deps, CATEGORY, "no_self_referencing_deps", HORSeverity.CRITICAL),
        (22, rule_022_id_coverage, CATEGORY, "id_coverage", HORSeverity.WARNING),
        (23, rule_023_toc_present, CATEGORY, "toc_present", HORSeverity.WARNING),
    ]
