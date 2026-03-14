"""StageContext — per-finding, per-stage artifact storage.

Each finding gets a dedicated context slot per stage. Stages write their
output artifact to their slot and read from predecessor slots (read-only).
Context flows forward, never backward.
"""

from __future__ import annotations

from typing import Any


class StageContext:
    """Manages artifact storage and retrieval for pipeline stages.

    Each finding has an isolated context that accumulates artifacts as it
    progresses through the pipeline. Stages read their predecessors' output
    and write their own — never modifying upstream artifacts.
    """

    async def load(self, stage_id: int, finding_id: str) -> dict[str, Any]:
        """Load the artifact for a specific stage and finding.

        Args:
            stage_id: The pipeline stage number (0-10).
            finding_id: The unique identifier for the finding.

        Returns:
            The stage artifact as a dictionary.

        Raises:
            NotImplementedError: Until the context engine is implemented.
            KeyError: If no artifact exists for the given stage and finding.
        """
        raise NotImplementedError

    async def save(
        self, stage_id: int, finding_id: str, content: dict[str, Any]
    ) -> None:
        """Save the artifact for a specific stage and finding.

        Args:
            stage_id: The pipeline stage number (0-10).
            finding_id: The unique identifier for the finding.
            content: The stage artifact to persist.

        Raises:
            NotImplementedError: Until the context engine is implemented.
            ValueError: If stage_id is not in range 0-10.
        """
        raise NotImplementedError

    async def query(self, finding_id: str, semantic_query: str) -> list[dict[str, Any]]:
        """Query across all stages for a finding using semantic search.

        Args:
            finding_id: The unique identifier for the finding.
            semantic_query: Natural language query to match against artifacts.

        Returns:
            List of matching artifact fragments with stage metadata.

        Raises:
            NotImplementedError: Until the context engine is implemented.
        """
        raise NotImplementedError
