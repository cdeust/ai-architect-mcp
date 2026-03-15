"""StageContext — per-finding, per-stage artifact storage.

Each finding gets a dedicated context slot per stage. Stages write their
output artifact to their slot and read from predecessor slots (read-only).
Context flows forward, never backward.
"""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._context.artifact_store import ArtifactStore


class StageContext:
    """Manages artifact storage and retrieval for pipeline stages.

    Each finding has an isolated context that accumulates artifacts as it
    progresses through the pipeline. Stages read their predecessors' output
    and write their own — never modifying upstream artifacts.

    Args:
        store: The artifact store backend. Creates in-memory store if None.
        observability: Optional ObservabilityPort for emitting events.
    """

    def __init__(
        self,
        store: ArtifactStore | None = None,
        observability: Any | None = None,
    ) -> None:
        """Initialize with an artifact store and optional observability.

        Args:
            store: ArtifactStore instance. Creates one if not provided.
            observability: ObservabilityPort instance for event emission.
        """
        self._store = store or ArtifactStore()
        self._observability = observability

    async def load(
        self, stage_id: int, finding_id: str
    ) -> dict[str, Any]:
        """Load the artifact for a specific stage and finding.

        Args:
            stage_id: The pipeline stage number (0-10).
            finding_id: The unique identifier for the finding.

        Returns:
            The stage artifact as a dictionary.

        Raises:
            ValueError: If stage_id is out of range.
            ArtifactNotFoundError: If no artifact exists.
        """
        return await self._store.retrieve(stage_id, finding_id)

    async def save(
        self,
        stage_id: int,
        finding_id: str,
        content: dict[str, Any],
    ) -> None:
        """Save the artifact for a specific stage and finding.

        Args:
            stage_id: The pipeline stage number (0-10).
            finding_id: The unique identifier for the finding.
            content: The stage artifact to persist.

        Raises:
            ValueError: If stage_id is out of range.
            ContextViolationError: If writing backward.
        """
        await self._store.store(stage_id, finding_id, content)
        if self._observability is not None:
            from ai_architect_mcp._observability.instrumentation import (
                emit_artifact_saved,
            )
            await emit_artifact_saved(stage_id, finding_id)

    async def query(
        self, finding_id: str, semantic_query: str
    ) -> list[dict[str, Any]]:
        """Query across all stages for a finding.

        Args:
            finding_id: The unique identifier for the finding.
            semantic_query: Query string to match against artifacts.

        Returns:
            List of matching artifact fragments with stage metadata.
        """
        return await self._store.query(finding_id, semantic_query)

    async def load_artifact(
        self, stage_id: int, finding_id: str
    ) -> dict[str, Any]:
        """Load a stage artifact (StageContextPort protocol).

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.

        Returns:
            The stage artifact as a dictionary.
        """
        return await self._store.retrieve(stage_id, finding_id)

    async def save_artifact(
        self,
        stage_id: int,
        finding_id: str,
        artifact: dict[str, Any],
    ) -> None:
        """Save a stage artifact (StageContextPort protocol).

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.
            artifact: The artifact to persist.
        """
        await self._store.store(stage_id, finding_id, artifact)

    async def query_artifacts(
        self, finding_id: str, query: str
    ) -> list[dict[str, Any]]:
        """Query artifacts across stages (StageContextPort protocol).

        Args:
            finding_id: Unique finding identifier.
            query: Semantic query string.

        Returns:
            Matching artifact fragments with stage metadata.
        """
        return await self._store.query(finding_id, query)
