"""D2 — Header Format scorer (Critical).

Checks that section headers follow the ``## SectionName`` pattern.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

VALID_HEADER_PATTERN = re.compile(r"^## [A-Z][A-Za-z0-9 ]+$", re.MULTILINE)
ANY_HEADER_PATTERN = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)

PENALTY_PER_MALFORMED = 0.1
PASS_THRESHOLD = 0.8


def score_header_format(artifact: dict[str, Any]) -> DimensionScore:
    """Score header formatting consistency.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D2_HEADER_FORMAT.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    all_headers = ANY_HEADER_PATTERN.findall(content)
    valid_headers = VALID_HEADER_PATTERN.findall(content)

    malformed_count = len(all_headers) - len(valid_headers)

    for header in all_headers:
        if not VALID_HEADER_PATTERN.match(header):
            findings.append(f"Malformed header: '{header.strip()}'")

    raw_score = 1.0 - (malformed_count * PENALTY_PER_MALFORMED)
    score = max(0.0, min(1.0, raw_score))

    return DimensionScore(
        dimension_type=DimensionType.D2_HEADER_FORMAT,
        dimension_name="Header Format",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
