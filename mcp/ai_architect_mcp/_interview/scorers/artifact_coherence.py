"""D5 — Artifact Coherence scorer (Advisory).

Measures cross-referencing of terms between sections.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect_mcp._interview.models import DimensionScore, DimensionType

TERM_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b")

PASS_THRESHOLD = 0.6


def _extract_sections(content: str) -> dict[str, str]:
    """Split content into named sections by ## headers.

    Args:
        content: Full PRD markdown content.

    Returns:
        Dict mapping section name to section body text.
    """
    sections: dict[str, str] = {}
    parts = re.split(r"^## ", content, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.split("\n", 1)
        name = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        sections[name] = body
    return sections


def score_artifact_coherence(artifact: dict[str, Any]) -> DimensionScore:
    """Score cross-referencing of terms across sections.

    Args:
        artifact: PRD artifact with a ``content`` string field.

    Returns:
        DimensionScore for D5_ARTIFACT_COHERENCE.
    """
    content: str = artifact.get("content", "")
    findings: list[str] = []

    sections = _extract_sections(content)

    if len(sections) < 2:
        return DimensionScore(
            dimension_type=DimensionType.D5_ARTIFACT_COHERENCE,
            dimension_name="Artifact Coherence",
            score=1.0,
            passed=True,
            findings=["Fewer than 2 sections — coherence check skipped"],
        )

    # Collect terms defined in each section
    section_terms: dict[str, set[str]] = {}
    for name, body in sections.items():
        section_terms[name] = set(TERM_PATTERN.findall(body))

    all_terms: set[str] = set()
    for terms in section_terms.values():
        all_terms.update(terms)

    if not all_terms:
        return DimensionScore(
            dimension_type=DimensionType.D5_ARTIFACT_COHERENCE,
            dimension_name="Artifact Coherence",
            score=1.0,
            passed=True,
            findings=["No multi-word terms found — coherence check skipped"],
        )

    cross_referenced = 0
    for term in all_terms:
        sections_containing = [
            name for name, terms in section_terms.items() if term in terms
        ]
        if len(sections_containing) >= 2:
            cross_referenced += 1

    total_defined = len(all_terms)
    score = cross_referenced / total_defined if total_defined > 0 else 1.0

    if score < PASS_THRESHOLD:
        findings.append(
            f"Only {cross_referenced}/{total_defined} terms referenced across sections"
        )

    return DimensionScore(
        dimension_type=DimensionType.D5_ARTIFACT_COHERENCE,
        dimension_name="Artifact Coherence",
        score=score,
        passed=score >= PASS_THRESHOLD,
        findings=findings,
    )
