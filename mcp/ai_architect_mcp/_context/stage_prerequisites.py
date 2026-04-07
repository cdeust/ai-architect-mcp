"""Stage prerequisites — declarative gate that prevents skipping pipeline stages.

The pipeline has 11 stages (0–10) that must be executed in order. Stage N
cannot start unless every prerequisite stage has produced an artifact for
the same finding.

This is enforced inside ``StageContext.save`` so any caller — slash
command, MCP tool, or hand-written script — fails fast if it tries to
short-circuit the pipeline.

The map is intentionally explicit. Adding a new stage means adding a row
here, not editing a regex or parsing skill markdown at runtime.

Reference: ``CLAUDE.md`` — "Context flows forward, never backward."
"""
from __future__ import annotations


class StagePrerequisiteViolation(Exception):
    """Raised when a stage save is attempted before its prerequisites exist.

    Carries the missing prerequisite stage IDs so the caller can fix the
    pipeline order instead of guessing which gate failed.
    """

    def __init__(
        self,
        stage_id: int,
        finding_id: str,
        missing: list[int],
    ) -> None:
        self.stage_id = stage_id
        self.finding_id = finding_id
        self.missing = missing
        msg = (
            f"Stage {stage_id} cannot save artifact for finding "
            f"'{finding_id}' — missing prerequisite stages: {missing}. "
            f"Run the pipeline strictly in order: stage 0 → 1 → 2 → 3 → "
            f"4 → 5 → 6 → 7 → 8 → 9 → 10. The orchestrator must not "
            f"skip stages or invoke implementation (stage 6) before PRD "
            f"generation (stage 4) and PRD review (stage 5) have "
            f"produced their artifacts."
        )
        super().__init__(msg)


# Canonical 11-stage pipeline (0-10) matching artifact_store MAX_STAGE_ID.
# Stage 4.5 (Plan Interview) is a sub-gate of Stage 4 — it validates the
# PRD before it propagates and is checked separately by the interview
# tools, but it does not consume its own artifact slot. Stage 5 onward
# is unchanged from the existing skill numbering.
#
# 0  Health
# 1  Discovery
# 2  Impact
# 3  Integration design
# 4  PRD generation (includes 4.5 Plan Interview as a sub-gate)
# 5  PRD review
# 6  Implementation
# 7  Verification
# 8  Benchmark
# 9  Deployment
# 10 Pull request
STAGE_PREREQUISITES: dict[int, frozenset[int]] = {
    0: frozenset(),
    1: frozenset({0}),
    2: frozenset({0, 1}),
    3: frozenset({0, 1, 2}),
    4: frozenset({0, 1, 2, 3}),
    5: frozenset({0, 1, 2, 3, 4}),
    6: frozenset({0, 1, 2, 3, 4, 5}),
    7: frozenset({0, 1, 2, 3, 4, 5, 6}),
    8: frozenset({0, 1, 2, 3, 4, 5, 6, 7}),
    9: frozenset({0, 1, 2, 3, 4, 5, 6, 7, 8}),
    10: frozenset({0, 1, 2, 3, 4, 5, 6, 7, 8, 9}),
}


def check_prerequisites(
    stage_id: int,
    finding_id: str,
    completed_stages: set[int],
) -> None:
    """Raise ``StagePrerequisiteViolation`` if any prerequisite is missing.

    Args:
        stage_id: The stage that wants to save an artifact.
        finding_id: The finding under processing.
        completed_stages: Stage IDs that already have an artifact for this
            finding.

    Raises:
        StagePrerequisiteViolation: If a prerequisite stage has not yet
            saved an artifact.
    """
    required = STAGE_PREREQUISITES.get(stage_id, frozenset())
    missing = sorted(required - completed_stages)
    if missing:
        raise StagePrerequisiteViolation(stage_id, finding_id, missing)


def is_unknown_stage(stage_id: int) -> bool:
    """Return True if the stage id is not in the canonical pipeline."""
    return stage_id not in STAGE_PREREQUISITES
