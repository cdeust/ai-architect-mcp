"""HandoffDocument — session boundary persistence.

At the end of every session, a HandoffDocument is written with:
- What was completed
- What is in progress
- What is blocked
- What the next session should do first

This ensures no state is lost between sessions, even if context is compacted.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, model_validator


class HandoffDocument(BaseModel):
    """Session boundary state for pipeline continuity.

    Written by stop.sh hook at session end. Read by session-start.sh
    at the beginning of the next session to restore pipeline state.
    """

    completed: list[str] = Field(default_factory=list)
    in_progress: list[str] = Field(default_factory=list)
    blocked: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    session_id: str = ""
    timestamp: str = ""

    @model_validator(mode="after")
    def validate_populated_requires_session_id(self) -> HandoffDocument:
        """If any list is populated, session_id must be set."""
        has_content = (
            self.completed
            or self.in_progress
            or self.blocked
            or self.next_actions
        )
        if has_content and not self.session_id.strip():
            msg = (
                "session_id is required when any task list is populated "
                "— provide a valid session identifier"
            )
            raise ValueError(msg)
        return self

    def to_markdown(self) -> str:
        """Serialize the handoff document to markdown.

        Returns:
            Markdown string representation.
        """
        lines: list[str] = []
        lines.append("# Handoff")
        lines.append("")
        lines.append(f"**Session:** {self.session_id}")
        lines.append(f"**Timestamp:** {self.timestamp}")
        lines.append("")

        lines.append("## Completed")
        lines.append("")
        for item in self.completed:
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## In Progress")
        lines.append("")
        for item in self.in_progress:
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## Blocked")
        lines.append("")
        for item in self.blocked:
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## Next Actions")
        lines.append("")
        for item in self.next_actions:
            lines.append(f"- {item}")
        lines.append("")

        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, markdown: str) -> HandoffDocument:
        """Deserialize a handoff document from markdown.

        Args:
            markdown: Markdown string to parse.

        Returns:
            HandoffDocument parsed from the markdown.
        """
        session_id = ""
        timestamp = ""
        sections: dict[str, list[str]] = {
            "completed": [],
            "in_progress": [],
            "blocked": [],
            "next_actions": [],
        }

        session_match = re.search(
            r"\*\*Session:\*\*\s*(.+)", markdown
        )
        if session_match:
            session_id = session_match.group(1).strip()

        timestamp_match = re.search(
            r"\*\*Timestamp:\*\*\s*(.+)", markdown
        )
        if timestamp_match:
            timestamp = timestamp_match.group(1).strip()

        section_map = {
            "## Completed": "completed",
            "## In Progress": "in_progress",
            "## Blocked": "blocked",
            "## Next Actions": "next_actions",
        }

        current_section: str | None = None
        for line in markdown.splitlines():
            stripped = line.strip()
            if stripped in section_map:
                current_section = section_map[stripped]
            elif current_section and stripped.startswith("- "):
                sections[current_section].append(stripped[2:])

        return cls(
            completed=sections["completed"],
            in_progress=sections["in_progress"],
            blocked=sections["blocked"],
            next_actions=sections["next_actions"],
            session_id=session_id,
            timestamp=timestamp,
        )
