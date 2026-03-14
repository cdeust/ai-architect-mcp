"""D7 — Stakeholder Alignment scorer (Advisory).

Verifies that user stories reference a stakeholder or actor.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

STAKEHOLDER_PATTERN = re.compile(r"(?i)(as a\s+\w+|stakeholder:)", re.MULTILINE)
STORY_PATTERN = re.compile(r"(?i)STORY-\d+[:\s].*", re.MULTILINE)

PASS_THRESHOLD = 0.6


def score_stakeholder_alignment(artifact: dict[str, Any]) -> DimensionScore:
    """Score stakeholder coverage in user stories.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D7_STAKEHOLDER_ALIGNMENT.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    stories = STORY_PATTERN.findall(content)

    if not stories:
        return DimensionScore(
            dimension_type=DimensionType.D7_STAKEHOLDER_ALIGNMENT,
            dimension_name="Stakeholder Alignment",
            score=1.0,
            passed=True,
            findings=["No user stories found — stakeholder check skipped"],
        )

    stories_with_stakeholder = 0
    for story in stories:
        if STAKEHOLDER_PATTERN.search(story):
            stories_with_stakeholder += 1
        else:
            findings.append(
                f"Story missing stakeholder reference: '{story.strip()[:60]}'"
            )

    total = len(stories)
    score = stories_with_stakeholder / total if total > 0 else 1.0

    return DimensionScore(
        dimension_type=DimensionType.D7_STAKEHOLDER_ALIGNMENT,
        dimension_name="Stakeholder Alignment",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
