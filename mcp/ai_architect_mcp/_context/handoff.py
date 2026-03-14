"""HandoffDocument — session boundary persistence.

At the end of every session, a HandoffDocument is written with:
- What was completed
- What is in progress
- What is blocked
- What the next session should do first

This ensures no state is lost between sessions, even if context is compacted.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HandoffDocument:
    """Session boundary state for pipeline continuity.

    Written by stop.sh hook at session end. Read by session-start.sh
    at the beginning of the next session to restore pipeline state.
    """

    completed: list[str] = field(default_factory=list)
    in_progress: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    session_id: str = ""
    timestamp: str = ""
