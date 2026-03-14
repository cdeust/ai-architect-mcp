"""D3 — ID Consistency scorer (Critical).

Validates that identifiers (FR-xxx, AC-xxx, STORY-xxx) are unique
and follow a consistent sequential pattern.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

ID_PATTERN = re.compile(r"\b(FR|AC|STORY|NFR|TC)-(\d+)\b")

PASS_THRESHOLD = 0.8


def score_id_consistency(artifact: dict[str, Any]) -> DimensionScore:
    """Score identifier consistency within a PRD artifact.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D3_ID_CONSISTENCY.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    matches = ID_PATTERN.findall(content)

    if not matches:
        return DimensionScore(
            dimension_type=DimensionType.D3_ID_CONSISTENCY,
            dimension_name="ID Consistency",
            score=0.0,
            passed=False,
            findings=["No identifiers (FR-xxx, AC-xxx, STORY-xxx) found"],
        )

    full_ids = [f"{prefix}-{num}" for prefix, num in matches]
    total_ids = len(full_ids)
    consistent_count = 0

    seen: set[str] = set()
    for fid in full_ids:
        if fid in seen:
            findings.append(f"Duplicate identifier: '{fid}'")
        else:
            consistent_count += 1
            seen.add(fid)

    # Check sequential ordering within each prefix group
    prefix_groups: dict[str, list[int]] = {}
    for prefix, num in matches:
        prefix_groups.setdefault(prefix, []).append(int(num))

    for prefix, numbers in prefix_groups.items():
        unique_numbers = sorted(set(numbers))
        expected = list(range(unique_numbers[0], unique_numbers[0] + len(unique_numbers)))
        if unique_numbers != expected:
            findings.append(
                f"Non-sequential IDs for prefix '{prefix}': {unique_numbers}"
            )

    score = consistent_count / total_ids if total_ids > 0 else 0.0

    return DimensionScore(
        dimension_type=DimensionType.D3_ID_CONSISTENCY,
        dimension_name="ID Consistency",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
