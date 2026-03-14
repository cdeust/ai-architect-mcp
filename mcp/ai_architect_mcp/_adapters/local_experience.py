"""Local JSON adapter for experience pattern storage.

Stores all patterns in {data_dir}/experience/patterns.json as a JSON array.
Implements ExperiencePort with biological decay filtering on read.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_architect_mcp._adapters.memory_ports import ExperiencePort
from ai_architect_mcp._models.experience_pattern import ExperiencePattern

EXPERIENCE_DIR: str = "experience"
PATTERNS_FILE: str = "patterns.json"


class LocalExperience(ExperiencePort):
    """JSON file persistence for experience patterns.

    All patterns are stored in a single JSON array file. Reads apply
    decay filtering via current_relevance(). Writes replace the full file.

    Args:
        data_dir: Root directory for all persistence data.
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize the local experience adapter.

        Args:
            data_dir: Root directory for persistence.
        """
        self._dir = data_dir / EXPERIENCE_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / PATTERNS_FILE

    def _load_all(self) -> list[ExperiencePattern]:
        """Load all patterns from disk.

        Returns:
            All stored patterns regardless of relevance.
        """
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [ExperiencePattern.model_validate(item) for item in raw]

    def _save_all(self, patterns: list[ExperiencePattern]) -> None:
        """Write all patterns to disk.

        Args:
            patterns: Complete list of patterns to persist.
        """
        data = [p.model_dump(mode="json") for p in patterns]
        self._path.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    async def save(self, pattern: ExperiencePattern) -> None:
        """Persist an experience pattern (upsert by pattern_id).

        Args:
            pattern: The pattern to save.
        """
        patterns = self._load_all()
        existing_idx = next(
            (i for i, p in enumerate(patterns) if p.pattern_id == pattern.pattern_id),
            None,
        )
        if existing_idx is not None:
            patterns[existing_idx] = pattern
        else:
            patterns.append(pattern)
        self._save_all(patterns)

    async def list_patterns(
        self, stage_id: int | None = None, min_relevance: float = 0.0
    ) -> list[ExperiencePattern]:
        """List patterns filtered by stage and minimum current relevance.

        Args:
            stage_id: Optional stage filter (0-10).
            min_relevance: Minimum current relevance threshold.

        Returns:
            Matching patterns sorted by current relevance descending.
        """
        patterns = self._load_all()
        if stage_id is not None:
            patterns = [p for p in patterns if p.stage_id == stage_id]
        result = [
            p for p in patterns if p.current_relevance() >= min_relevance
        ]
        result.sort(key=lambda p: p.current_relevance(), reverse=True)
        return result

    async def reinforce(self, pattern_id: str) -> ExperiencePattern:
        """Reinforce a pattern by ID.

        Args:
            pattern_id: ID of the pattern to reinforce.

        Returns:
            The reinforced pattern with boosted relevance.

        Raises:
            KeyError: If pattern_id is not found.
        """
        patterns = self._load_all()
        for i, p in enumerate(patterns):
            if p.pattern_id == pattern_id:
                reinforced = p.reinforce()
                patterns[i] = reinforced
                self._save_all(patterns)
                return reinforced
        msg = f"Pattern '{pattern_id}' not found — cannot reinforce a non-existent pattern"
        raise KeyError(msg)
