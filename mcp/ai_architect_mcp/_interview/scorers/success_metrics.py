"""D10 — Success Metrics scorer (Critical).

Checks that success metrics contain quantitative values.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

METRICS_HEADER = re.compile(r"(?i)^##\s+(?:Success\s+)?Metrics?", re.MULTILINE)
METRIC_ITEM = re.compile(r"(?i)^\s*[-*]\s+.+", re.MULTILINE)
QUANTITATIVE_PATTERN = re.compile(r"\d+(?:\.\d+)?(?:\s*%)?")

PASS_THRESHOLD = 0.8


def score_success_metrics(artifact: dict[str, Any]) -> DimensionScore:
    """Score whether success metrics contain quantitative values.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D10_SUCCESS_METRICS.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    header_match = METRICS_HEADER.search(content)

    if not header_match:
        return DimensionScore(
            dimension_type=DimensionType.D10_SUCCESS_METRICS,
            dimension_name="Success Metrics",
            score=0.0,
            passed=False,
            findings=["No 'Metrics' or 'Success Metrics' section found"],
        )

    start = header_match.end()
    next_header = re.search(r"^## ", content[start:], re.MULTILINE)
    section_text = content[start:start + next_header.start()] if next_header else content[start:]

    metrics = METRIC_ITEM.findall(section_text)

    if not metrics:
        return DimensionScore(
            dimension_type=DimensionType.D10_SUCCESS_METRICS,
            dimension_name="Success Metrics",
            score=0.0,
            passed=False,
            findings=["Metrics section exists but contains no listed items"],
        )

    metrics_with_numbers = 0
    for metric in metrics:
        if QUANTITATIVE_PATTERN.search(metric):
            metrics_with_numbers += 1
        else:
            findings.append(
                f"Metric lacks quantitative value: '{metric.strip()[:60]}'"
            )

    total = len(metrics)
    score = metrics_with_numbers / total if total > 0 else 0.0

    return DimensionScore(
        dimension_type=DimensionType.D10_SUCCESS_METRICS,
        dimension_name="Success Metrics",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
