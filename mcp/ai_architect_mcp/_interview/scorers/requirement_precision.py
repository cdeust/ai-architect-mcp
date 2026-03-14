"""D8 — Requirement Precision scorer (Critical).

Checks that requirements contain measurable criteria.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

REQUIREMENT_PATTERN = re.compile(
    r"(?:FR|NFR)-\d+[:\s](.*)", re.MULTILINE,
)
MEASURABLE_PATTERN = re.compile(
    r"\d+(?:\.\d+)?(?:\s*(?:%|ms|seconds?|minutes?|hours?|requests?))?",
)

PASS_THRESHOLD = 0.8


def score_requirement_precision(artifact: dict[str, Any]) -> DimensionScore:
    """Score whether requirements have measurable criteria.

    Extracts the description portion after the FR/NFR ID and checks
    for numeric/measurable values.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D8_REQUIREMENT_PRECISION.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    descriptions = REQUIREMENT_PATTERN.findall(content)

    if not descriptions:
        return DimensionScore(
            dimension_type=DimensionType.D8_REQUIREMENT_PRECISION,
            dimension_name="Requirement Precision",
            score=0.0,
            passed=False,
            findings=["No requirements (FR-xxx, NFR-xxx) found in artifact"],
        )

    precise_count = 0
    for desc in descriptions:
        if MEASURABLE_PATTERN.search(desc):
            precise_count += 1
        else:
            findings.append(
                f"Requirement lacks measurable criteria: '{desc.strip()[:60]}'"
            )

    total = len(descriptions)
    score = precise_count / total if total > 0 else 0.0

    return DimensionScore(
        dimension_type=DimensionType.D8_REQUIREMENT_PRECISION,
        dimension_name="Requirement Precision",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
