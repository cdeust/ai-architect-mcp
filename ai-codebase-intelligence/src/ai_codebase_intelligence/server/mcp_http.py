"""MCP over HTTP — 1:1 port of gitnexus server/mcp-http.js.

Manages stateful sessions with TTL eviction. In Python we use a
simple dict since there's no concurrent access (GIL).
"""
from __future__ import annotations

import time
import uuid
from typing import Any

SESSION_TTL_S = 30 * 60  # 30 minutes
CLEANUP_INTERVAL_S = 5 * 60  # 5 minutes


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(self) -> str:
        sid = str(uuid.uuid4())
        self._sessions[sid] = {"lastActivity": time.time()}
        return sid

    def touch(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session["lastActivity"] = time.time()
        return True

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def cleanup_idle(self) -> int:
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s["lastActivity"] > SESSION_TTL_S
        ]
        for sid in expired:
            self._sessions.pop(sid, None)
        return len(expired)

    def close_all(self) -> None:
        self._sessions.clear()

    @property
    def count(self) -> int:
        return len(self._sessions)
