"""Entry point scoring for identifying likely application entry points.

Scores graph nodes based on call ratio, name patterns, export status,
and test-file penalties. Reuses pattern data from the legacy
entry_point_scoring module.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from ai_codebase_intelligence._models.graph_types import GraphNode

ENTRY_NAME_PATTERNS: list[str] = [
    "main", "init", "bootstrap", "start", "run",
    "setup", "configure", "handler", "controller",
    "process", "execute", "perform", "dispatch",
    "trigger", "fire", "emit",
]

_UNIVERSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(main|init|bootstrap|start|run|setup|configure)$", re.I),
    re.compile(r"^handle[A-Z]"),
    re.compile(r"^on[A-Z]"),
    re.compile(r"Handler$"),
    re.compile(r"Controller$"),
    re.compile(r"^process[A-Z]"),
    re.compile(r"^execute[A-Z]"),
    re.compile(r"^perform[A-Z]"),
    re.compile(r"^dispatch[A-Z]"),
    re.compile(r"^trigger[A-Z]"),
    re.compile(r"^fire[A-Z]"),
    re.compile(r"^emit[A-Z]"),
]

_UTILITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(get|set|is|has|can|should|will|did)[A-Z]"),
    re.compile(r"^_"),
    re.compile(r"^(format|parse|validate|convert|transform)", re.I),
    re.compile(r"^(log|debug|error|warn|info)$", re.I),
    re.compile(r"^(to|from)[A-Z]"),
    re.compile(r"^(encode|decode)", re.I),
    re.compile(r"^(serialize|deserialize)", re.I),
    re.compile(r"Helper$"),
    re.compile(r"Util$"),
    re.compile(r"Utils$"),
    re.compile(r"^utils?$", re.I),
    re.compile(r"^helpers?$", re.I),
]


class EntryPointScore(BaseModel):
    """Scoring result for a potential entry point.

    Args:
        total_score: Final computed score.
        name_pattern_score: Score contribution from name matching.
        test_penalty_applied: Whether the node is in a test file.
        call_ratio_score: callee_count / (caller_count + 1).
        framework_bonus: Additional score from framework detection.
    """

    total_score: float = Field(description="Final computed score")
    name_pattern_score: float = Field(
        description="Score contribution from name matching",
    )
    test_penalty_applied: bool = Field(
        description="Whether the node is in a test file",
    )
    call_ratio_score: float = Field(
        description="callee_count / (caller_count + 1)",
    )
    framework_bonus: float = Field(
        default=0.0,
        description="Additional framework-based score",
    )


def score_entry_point(
    node: GraphNode,
    caller_count: int,
    callee_count: int,
) -> EntryPointScore:
    """Score a graph node as a potential entry point.

    Args:
        node: The graph node to score.
        caller_count: Number of callers of this node.
        callee_count: Number of callees from this node.

    Returns:
        An EntryPointScore with all sub-scores.
    """
    call_ratio = callee_count / (caller_count + 1)

    name = node.name
    name_multiplier = 1.0
    name_score = 0.0

    if any(p.search(name) for p in _UTILITY_PATTERNS):
        name_multiplier = 0.3
        name_score = 0.3
    elif any(p.search(name) for p in _UNIVERSAL_PATTERNS):
        name_multiplier = 1.5
        name_score = 1.0
    else:
        name_score = 0.5

    is_test = _is_test_file(node.file_path)
    export_multiplier = 2.0 if node.is_exported else 1.0

    total = call_ratio * name_multiplier * export_multiplier
    if is_test:
        total *= 0.1

    return EntryPointScore(
        total_score=total,
        name_pattern_score=name_score,
        test_penalty_applied=is_test,
        call_ratio_score=call_ratio,
        framework_bonus=0.0,
    )


def _is_test_file(file_path: str) -> bool:
    """Check whether *file_path* belongs to a test directory or file.

    Args:
        file_path: Relative or absolute file path.

    Returns:
        True if the file is a test file.
    """
    p = file_path.lower().replace("\\", "/")
    return (
        ".test." in p
        or ".spec." in p
        or "__tests__/" in p
        or "__mocks__/" in p
        or "/test/" in p
        or "/tests/" in p
        or "/testing/" in p
        or p.endswith("_test.py")
        or "/test_" in p
        or p.endswith("_test.go")
        or "/src/test/" in p
        or p.endswith("tests.swift")
        or p.endswith("test.swift")
        or "uitests/" in p
        or ".tests/" in p
        or "tests.cs" in p
        or p.endswith("test.php")
        or p.endswith("spec.php")
        or "/tests/feature/" in p
        or "/tests/unit/" in p
    )
