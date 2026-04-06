"""MCP HTTP session management and CORS utilities.

Provides session lifecycle (create, touch, expire, evict) and
standard CORS header generation for the HTTP transport layer.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SESSION_TTL_SECONDS: int = 1800

CORS_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
}

# ---------------------------------------------------------------------------
# Session model
# ---------------------------------------------------------------------------


@dataclass
class MCPSession:
    """A single MCP HTTP session.

    Args:
        session_id: Unique session identifier.
        created_at: Unix timestamp of creation.
        last_active: Unix timestamp of last activity.
        ttl_seconds: Time-to-live in seconds before expiry.
        metadata: Arbitrary session metadata.
    """

    session_id: str
    created_at: float
    last_active: float
    ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check whether the session has exceeded its TTL.

        Returns:
            True if current time exceeds last_active + ttl_seconds.
        """
        return time.time() > self.last_active + self.ttl_seconds

    def touch(self) -> None:
        """Update last_active to the current time."""
        self.last_active = time.time()


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------

_DEFAULT_MAX_SESSIONS = 1000


class SessionManager:
    """Manages a pool of MCP HTTP sessions.

    Args:
        ttl_seconds: Default TTL for new sessions.
        max_sessions: Maximum concurrent sessions allowed.
    """

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        max_sessions: int = _DEFAULT_MAX_SESSIONS,
    ) -> None:
        self._ttl = ttl_seconds
        self._max_sessions = max_sessions
        self._sessions: dict[str, MCPSession] = {}

    def create_session(
        self,
        metadata: dict[str, Any] | None = None,
    ) -> MCPSession:
        """Create a new session.

        Args:
            metadata: Optional metadata to attach to the session.

        Returns:
            The newly created MCPSession.

        Raises:
            RuntimeError: If the maximum session limit is reached.
        """
        if len(self._sessions) >= self._max_sessions:
            raise RuntimeError(
                f"Maximum session limit ({self._max_sessions}) reached"
            )

        now = time.time()
        session = MCPSession(
            session_id=str(uuid.uuid4()),
            created_at=now,
            last_active=now,
            ttl_seconds=self._ttl,
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> MCPSession | None:
        """Retrieve a session by ID, evicting it if expired.

        Args:
            session_id: The session identifier to look up.

        Returns:
            The MCPSession if found and not expired, else None.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired:
            del self._sessions[session_id]
            return None
        session.touch()
        return session

    def remove_session(self, session_id: str) -> bool:
        """Remove a session by ID.

        Args:
            session_id: The session identifier to remove.

        Returns:
            True if the session was found and removed, False otherwise.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def active_count(self) -> int:
        """Return the number of active (non-expired) sessions.

        Returns:
            Count of sessions currently held.
        """
        return len(self._sessions)


# ---------------------------------------------------------------------------
# CORS helpers
# ---------------------------------------------------------------------------


def build_cors_headers(
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build a complete set of CORS response headers.

    Args:
        extra: Optional additional headers to merge in.

    Returns:
        Dict of CORS headers, merged with any extras.
    """
    headers = dict(CORS_HEADERS)
    if extra:
        headers.update(extra)
    return headers
