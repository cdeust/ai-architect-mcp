"""D6 — Clarity Level scorer (Critical).

Penalises vague or imprecise language in PRD artifacts.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

VAGUE_WORDS: list[str] = [
    "various",
    "several",
    "some",
    "many",
    "few",
    "often",
    "usually",
    "generally",
    "mostly",
    "things",
    "stuff",
    "etc",
    "and so on",
    "TBD",
    "TODO",
]

PENALTY_PER_VAGUE = 0.05
PASS_THRESHOLD = 0.8


def score_clarity_level(artifact: dict[str, Any]) -> DimensionScore:
    """Score language clarity by counting vague terms.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D6_CLARITY_LEVEL.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []
    vague_count = 0

    content_lower = content.lower()
    for word in VAGUE_WORDS:
        pattern = re.compile(r"\b" + re.escape(word.lower()) + r"\b")
        occurrences = len(pattern.findall(content_lower))
        if occurrences > 0:
            vague_count += occurrences
            findings.append(
                f"Vague term '{word}' found {occurrences} time(s)"
            )

    score = max(0.0, 1.0 - vague_count * PENALTY_PER_VAGUE)

    return DimensionScore(
        dimension_type=DimensionType.D6_CLARITY_LEVEL,
        dimension_name="Clarity Level",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
