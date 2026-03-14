"""D4 — Outline Flow scorer (Critical).

Checks that sections appear in the canonical ordering.
"""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

CANONICAL_ORDER: list[str] = [
    "Overview",
    "Requirements",
    "User Stories",
    "Technical",
    "Acceptance",
    "Roadmap",
    "Testing",
]

PASS_THRESHOLD = 0.8


def score_outline_flow(artifact: dict[str, Any]) -> DimensionScore:
    """Score whether sections follow the canonical ordering.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D4_OUTLINE_FLOW.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    # Find positions of each section in the content
    found_sections: list[tuple[str, int]] = []
    for section in CANONICAL_ORDER:
        pos = content.find(f"## {section}")
        if pos >= 0:
            found_sections.append((section, pos))

    if not found_sections:
        return DimensionScore(
            dimension_type=DimensionType.D4_OUTLINE_FLOW,
            dimension_name="Outline Flow",
            score=0.0,
            passed=False,
            findings=["No recognised sections found in content"],
        )

    total = len(found_sections)
    correctly_positioned = 0

    for i in range(len(found_sections)):
        in_order = True
        for j in range(i + 1, len(found_sections)):
            if found_sections[i][1] > found_sections[j][1]:
                in_order = False
                break
        if in_order:
            correctly_positioned += 1
        else:
            findings.append(
                f"Section '{found_sections[i][0]}' appears out of canonical order"
            )

    score = correctly_positioned / total if total > 0 else 0.0

    return DimensionScore(
        dimension_type=DimensionType.D4_OUTLINE_FLOW,
        dimension_name="Outline Flow",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
