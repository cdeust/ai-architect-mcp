"""Local JSON file adapter for pipeline session state.

Stores one JSON file per session under {data_dir}/sessions/{session_id}.json.
Implements PipelineStatePort for local development and single-machine usage.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_architect_mcp._adapters.memory_ports import PipelineStatePort
from ai_architect_mcp._models.session_state import SessionState

SESSIONS_DIR: str = "sessions"


class LocalPipelineState(PipelineStatePort):
    """JSON file persistence for pipeline session state.

    Each session is stored as a separate JSON file in the sessions directory.
    Files are named by session_id for direct lookup.

    Args:
        data_dir: Root directory for all persistence data.
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize the local pipeline state adapter.

        Args:
            data_dir: Root directory for persistence.
        """
        self._sessions_dir = data_dir / SESSIONS_DIR
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """Get the file path for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Path to the session JSON file.
        """
        return self._sessions_dir / f"{session_id}.json"

    async def load(self, session_id: str) -> SessionState | None:
        """Load a session state by ID.

        Args:
            session_id: Unique session identifier.

        Returns:
            The session state, or None if not found.
        """
        path = self._session_path(session_id)
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        return SessionState.model_validate_json(raw)

    async def save(self, state: SessionState) -> None:
        """Persist a session state to JSON.

        Args:
            state: The session state to save.
        """
        path = self._session_path(state.session_id)
        path.write_text(
            state.model_dump_json(indent=2), encoding="utf-8"
        )

    async def list_sessions(self, limit: int = 10) -> list[str]:
        """List recent session IDs sorted by modification time.

        Args:
            limit: Maximum number of session IDs to return.

        Returns:
            Session IDs, most recently modified first.
        """
        files = sorted(
            self._sessions_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        return [f.stem for f in files[:limit]]
