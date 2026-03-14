"""D9 — Assumption Validation scorer (Advisory).

Checks that an assumptions section exists with sufficient stated assumptions.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

ASSUMPTION_HEADER = re.compile(r"(?i)^##\s+Assumption", re.MULTILINE)
ASSUMPTION_ITEM = re.compile(r"(?i)^\s*[-*]\s+.+", re.MULTILINE)

MIN_ASSUMPTIONS_FULL = 3
PASS_THRESHOLD = 0.6


def score_assumption_validation(artifact: dict[str, Any]) -> DimensionScore:
    """Score the presence and quantity of stated assumptions.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D9_ASSUMPTION_VALIDATION.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    header_match = ASSUMPTION_HEADER.search(content)

    if not header_match:
        return DimensionScore(
            dimension_type=DimensionType.D9_ASSUMPTION_VALIDATION,
            dimension_name="Assumption Validation",
            score=0.0,
            passed=False,
            findings=["No 'Assumptions' section found in artifact"],
        )

    # Extract content after the assumptions header until next ## header
    start = header_match.end()
    next_header = re.search(r"^## ", content[start:], re.MULTILINE)
    section_text = content[start:start + next_header.start()] if next_header else content[start:]

    items = ASSUMPTION_ITEM.findall(section_text)
    count = len(items)

    if count >= MIN_ASSUMPTIONS_FULL:
        score = 1.0
    elif count >= 1:
        score = 0.5
        findings.append(
            f"Only {count} assumption(s) stated — at least {MIN_ASSUMPTIONS_FULL} recommended"
        )
    else:
        score = 0.0
        findings.append("Assumptions section exists but contains no listed items")

    return DimensionScore(
        dimension_type=DimensionType.D9_ASSUMPTION_VALIDATION,
        dimension_name="Assumption Validation",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
