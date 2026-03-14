"""ArtifactStore — in-memory dict-backed artifact storage.

Provides the storage backend for StageContext. Enforces forward-only
writes: once a later stage has written an artifact, earlier stages
cannot be modified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MIN_STAGE_ID = 0
MAX_STAGE_ID = 10


class ContextViolationError(Exception):
    """Raised when a context operation violates forward-only constraint."""


class ArtifactNotFoundError(Exception):
    """Raised when a requested artifact does not exist."""


class ArtifactStore:
    """In-memory artifact store with optional filesystem persistence.

    Stores artifacts keyed by (stage_id, finding_id). Enforces that
    artifacts can only be written to stages that have no later-stage
    artifacts already stored.

    Args:
        persist_dir: Optional directory for filesystem persistence.
            If None, artifacts are stored in memory only.
    """

    def __init__(self, persist_dir: Path | None = None) -> None:
        """Initialize the artifact store.

        Args:
            persist_dir: Optional directory for filesystem persistence.
        """
        self._store: dict[tuple[int, str], dict[str, Any]] = {}
        self._persist_dir = persist_dir

    async def store(
        self, stage_id: int, finding_id: str, artifact: dict[str, Any]
    ) -> None:
        """Store an artifact for a specific stage and finding.

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.
            artifact: The artifact data to store.

        Raises:
            ValueError: If stage_id is out of range.
            ContextViolationError: If a later stage already has an artifact.
        """
        self._validate_stage_id(stage_id)
        self._enforce_forward_only(stage_id, finding_id)
        self._store[(stage_id, finding_id)] = artifact

        if self._persist_dir is not None:
            await self._persist(stage_id, finding_id, artifact)

    async def retrieve(
        self, stage_id: int, finding_id: str
    ) -> dict[str, Any]:
        """Retrieve an artifact for a specific stage and finding.

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.

        Returns:
            The stored artifact data.

        Raises:
            ValueError: If stage_id is out of range.
            ArtifactNotFoundError: If no artifact exists for the key.
        """
        self._validate_stage_id(stage_id)
        key = (stage_id, finding_id)
        if key not in self._store:
            msg = (
                f"No artifact found for stage {stage_id}, "
                f"finding {finding_id} — ensure the stage has "
                f"completed before attempting to read its artifact"
            )
            raise ArtifactNotFoundError(msg)
        return self._store[key]

    async def query(
        self, finding_id: str, predicate: str
    ) -> list[dict[str, Any]]:
        """Query artifacts across all stages for a finding.

        Args:
            finding_id: Unique finding identifier.
            predicate: Key name to search for in artifacts.

        Returns:
            List of artifacts containing the predicate key.
        """
        results: list[dict[str, Any]] = []
        for (sid, fid), artifact in sorted(self._store.items()):
            if fid != finding_id:
                continue
            if predicate in str(artifact):
                results.append({"stage_id": sid, "artifact": artifact})
        return results

    async def exists(self, stage_id: int, finding_id: str) -> bool:
        """Check if an artifact exists for a specific stage and finding.

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.

        Returns:
            True if an artifact exists, False otherwise.
        """
        self._validate_stage_id(stage_id)
        return (stage_id, finding_id) in self._store

    async def list_stages(self, finding_id: str) -> list[int]:
        """List all stages that have artifacts for a finding.

        Args:
            finding_id: Unique finding identifier.

        Returns:
            Sorted list of stage IDs with stored artifacts.
        """
        return sorted(
            sid for (sid, fid) in self._store if fid == finding_id
        )

    def _validate_stage_id(self, stage_id: int) -> None:
        """Validate that stage_id is within the valid range.

        Args:
            stage_id: The stage ID to validate.

        Raises:
            ValueError: If stage_id is out of range 0-10.
        """
        if not (MIN_STAGE_ID <= stage_id <= MAX_STAGE_ID):
            msg = (
                f"stage_id {stage_id} is out of range — "
                f"must be between {MIN_STAGE_ID} and {MAX_STAGE_ID}"
            )
            raise ValueError(msg)

    def _enforce_forward_only(self, stage_id: int, finding_id: str) -> None:
        """Enforce forward-only write constraint.

        Args:
            stage_id: The stage attempting to write.
            finding_id: The finding being written to.

        Raises:
            ContextViolationError: If a later stage already has an artifact.
        """
        for (sid, fid) in self._store:
            if fid == finding_id and sid > stage_id:
                msg = (
                    f"Cannot modify stage {stage_id}: stage {sid} "
                    f"already written — context flows forward only"
                )
                raise ContextViolationError(msg)

    async def _persist(
        self, stage_id: int, finding_id: str, artifact: dict[str, Any]
    ) -> None:
        """Persist artifact to filesystem.

        Args:
            stage_id: Pipeline stage number.
            finding_id: Finding identifier.
            artifact: The artifact data to persist.
        """
        if self._persist_dir is None:
            return
        stage_dir = self._persist_dir / finding_id / f"stage_{stage_id}"
        stage_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = stage_dir / "artifact.json"
        artifact_path.write_text(json.dumps(artifact, indent=2, default=str))
