"""GitHub Actions StageContext adapter — JSON file persistence.

Provides StageContextPort implementation that persists artifacts
as JSON files in the workspace, suitable for GHA artifact upload.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_architect_mcp._adapters.ports import StageContextPort

ARTIFACTS_DIR = ".ai-architect/artifacts"


class GitHubActionsContext(StageContextPort):
    """Stage context backed by JSON files in the workspace.

    Args:
        workspace: Root workspace directory.
    """

    def __init__(self, workspace: Path) -> None:
        """Initialize the GHA context adapter.

        Args:
            workspace: Workspace root for artifact storage.
        """
        self._root = workspace / ARTIFACTS_DIR

    async def load_artifact(
        self, stage_id: int, finding_id: str,
    ) -> dict[str, Any]:
        """Load a stage artifact from disk.

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.

        Returns:
            The stage artifact as a dictionary.

        Raises:
            FileNotFoundError: If the artifact file does not exist.
        """
        path = self._artifact_path(stage_id, finding_id)
        if not path.exists():
            msg = (
                f"Artifact not found for stage {stage_id}, "
                f"finding {finding_id} at {path}"
            )
            raise FileNotFoundError(msg)
        return json.loads(path.read_text(encoding="utf-8"))

    async def save_artifact(
        self,
        stage_id: int,
        finding_id: str,
        artifact: dict[str, Any],
    ) -> None:
        """Save a stage artifact to disk.

        Args:
            stage_id: Pipeline stage number (0-10).
            finding_id: Unique finding identifier.
            artifact: The artifact to persist.
        """
        path = self._artifact_path(stage_id, finding_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(artifact, indent=2, default=str),
            encoding="utf-8",
        )

    async def query_artifacts(
        self, finding_id: str, query: str,
    ) -> list[dict[str, Any]]:
        """Query artifacts across stages for a finding.

        Args:
            finding_id: Unique finding identifier.
            query: Search string to match in artifacts.

        Returns:
            Matching artifacts with stage metadata.
        """
        results: list[dict[str, Any]] = []
        finding_dir = self._root / finding_id
        if not finding_dir.exists():
            return results

        for stage_dir in sorted(finding_dir.iterdir()):
            if not stage_dir.is_dir():
                continue
            artifact_file = stage_dir / "artifact.json"
            if not artifact_file.exists():
                continue
            content = artifact_file.read_text(encoding="utf-8")
            if query in content:
                results.append({
                    "stage_id": int(stage_dir.name.split("_")[-1]),
                    "artifact": json.loads(content),
                })

        return results

    def _artifact_path(self, stage_id: int, finding_id: str) -> Path:
        """Build the artifact file path.

        Args:
            stage_id: Pipeline stage number.
            finding_id: Finding identifier.

        Returns:
            Path to the artifact JSON file.
        """
        return self._root / finding_id / f"stage_{stage_id}" / "artifact.json"
