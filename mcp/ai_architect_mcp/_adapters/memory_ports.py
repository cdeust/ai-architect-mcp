"""Port interfaces for the four-layer memory model.

Defines abstract base classes for pipeline state persistence, experience
pattern storage with biological decay, and immutable audit event logging.
Concrete adapters implement these ports and are injected at the composition root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_architect_mcp._models.audit_event import AuditEvent, AuditQuery
from ai_architect_mcp._models.experience_pattern import ExperiencePattern
from ai_architect_mcp._models.session_state import SessionState


class PipelineStatePort(ABC):
    """Port for pipeline session state persistence.

    Stores and retrieves session state across pipeline runs.
    One JSON file per session in the local implementation.
    """

    @abstractmethod
    async def load(self, session_id: str) -> SessionState | None:
        """Load a session state by ID.

        Args:
            session_id: Unique session identifier.

        Returns:
            The session state, or None if not found.
        """
        ...

    @abstractmethod
    async def save(self, state: SessionState) -> None:
        """Persist a session state.

        Args:
            state: The session state to save.
        """
        ...

    @abstractmethod
    async def list_sessions(self, limit: int = 10) -> list[str]:
        """List recent session IDs.

        Args:
            limit: Maximum number of session IDs to return.

        Returns:
            List of session ID strings, most recent first.
        """
        ...


class ExperiencePort(ABC):
    """Port for experience pattern storage with biological decay.

    Patterns are stored, queried with decay filtering, and reinforced
    when re-observed.
    """

    @abstractmethod
    async def save(self, pattern: ExperiencePattern) -> None:
        """Persist an experience pattern.

        Args:
            pattern: The pattern to save.
        """
        ...

    @abstractmethod
    async def list_patterns(
        self, stage_id: int | None = None, min_relevance: float = 0.0
    ) -> list[ExperiencePattern]:
        """List patterns filtered by stage and minimum relevance.

        Args:
            stage_id: Optional stage filter (0-10).
            min_relevance: Minimum current relevance threshold.

        Returns:
            Matching patterns sorted by relevance descending.
        """
        ...

    @abstractmethod
    async def reinforce(self, pattern_id: str) -> ExperiencePattern:
        """Reinforce a pattern by incrementing its count and boosting relevance.

        Args:
            pattern_id: ID of the pattern to reinforce.

        Returns:
            The reinforced pattern.

        Raises:
            KeyError: If pattern_id is not found.
        """
        ...


class AuditPort(ABC):
    """Port for immutable audit event logging.

    Events are append-only. Once written, they cannot be modified or deleted.
    """

    @abstractmethod
    async def append(self, event: AuditEvent) -> None:
        """Append an audit event to the log.

        Args:
            event: The immutable event to record.
        """
        ...

    @abstractmethod
    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query audit events with optional filters.

        Args:
            query: Filter parameters (all fields combined with AND).

        Returns:
            Matching events sorted by timestamp descending.
        """
        ...
