"""D1 — Sections Present scorer (Critical).

Checks that all required PRD sections exist in the artifact content.
"""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

REQUIRED_SECTIONS: list[str] = [
    "Overview",
    "Requirements",
    "User Stories",
    "Technical",
    "Acceptance",
    "Roadmap",
    "Testing",
]

PASS_THRESHOLD = 0.8


def score_sections_present(artifact: dict[str, Any]) -> DimensionScore:
    """Score the presence of required sections in a PRD artifact.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D1_SECTIONS_PRESENT.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []
    found_count = 0

    for section in REQUIRED_SECTIONS:
        if f"## {section}" in content:
            found_count += 1
        else:
            findings.append(f"Missing required section: '{section}'")

    total = len(REQUIRED_SECTIONS)
    score = found_count / total if total > 0 else 0.0

    return DimensionScore(
        dimension_type=DimensionType.D1_SECTIONS_PRESENT,
        dimension_name="Sections Present",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
