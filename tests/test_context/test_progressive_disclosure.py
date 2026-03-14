"""Tests for progressive disclosure rendering functions."""

from __future__ import annotations

from ai_architect_mcp._context.progressive_disclosure import (
    render,
    render_l1,
    render_l2,
    render_l3,
)
from ai_architect_mcp._models.disclosure import DisclosureLevel


SAMPLE_DATA = {
    "title": "Authentication System PRD",
    "requirements_count": 12,
    "long_field": "x" * 200,
    "nested": {"key": "value"},
}


def test_render_l1_shows_types_only() -> None:
    """L1 renders key names with type annotations, no values."""
    result = render_l1(SAMPLE_DATA)
    assert "title: <str>" in result
    assert "requirements_count: <int>" in result
    assert "Authentication" not in result


def test_render_l2_truncates_long_values() -> None:
    """L2 truncates values longer than 120 characters."""
    result = render_l2(SAMPLE_DATA)
    assert "title: Authentication System PRD" in result
    assert "..." in result
    assert len(result) < len(render_l3(SAMPLE_DATA))


def test_render_l3_full_json() -> None:
    """L3 produces complete JSON output."""
    result = render_l3(SAMPLE_DATA)
    assert "Authentication System PRD" in result
    assert "x" * 200 in result


def test_l1_smaller_than_l2_smaller_than_l3() -> None:
    """Output size increases with disclosure level."""
    l1 = render_l1(SAMPLE_DATA)
    l2 = render_l2(SAMPLE_DATA)
    l3 = render_l3(SAMPLE_DATA)
    assert len(l1) < len(l2) < len(l3)


def test_render_dispatches_correctly() -> None:
    """render() dispatches to the correct level function."""
    assert render(SAMPLE_DATA, DisclosureLevel.L1_CONFIG) == render_l1(SAMPLE_DATA)
    assert render(SAMPLE_DATA, DisclosureLevel.L2_SUMMARY) == render_l2(SAMPLE_DATA)
    assert render(SAMPLE_DATA, DisclosureLevel.L3_FULL) == render_l3(SAMPLE_DATA)


def test_render_empty_dict() -> None:
    """All levels handle empty data without error."""
    assert render_l1({}) == ""
    assert render_l2({}) == ""
    assert render_l3({}) == "{}"
