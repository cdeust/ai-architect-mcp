"""Tests for HandoffDocument — markdown round-trip, validation."""

from __future__ import annotations

import pytest

from ai_architect_mcp._context.handoff import HandoffDocument


class TestHandoffValidation:
    """Test HandoffDocument validation."""

    def test_empty_document_valid(self) -> None:
        doc = HandoffDocument()
        assert doc.session_id == ""
        assert doc.completed == []

    def test_populated_without_session_id_rejected(self) -> None:
        with pytest.raises(ValueError, match="session_id is required"):
            HandoffDocument(
                completed=["Task 1"],
                session_id="",
            )

    def test_populated_with_session_id_valid(self) -> None:
        doc = HandoffDocument(
            completed=["Task 1"],
            session_id="session-001",
            timestamp="2025-03-01T12:00:00Z",
        )
        assert doc.session_id == "session-001"


class TestMarkdownRoundTrip:
    """Test markdown serialization and deserialization."""

    def test_round_trip(self) -> None:
        original = HandoffDocument(
            completed=["Implemented models", "Created tests"],
            in_progress=["Building context engine"],
            blocked=["Waiting for API key"],
            next_actions=["Complete scoring engine"],
            session_id="session-001",
            timestamp="2025-03-01T12:00:00Z",
        )
        markdown = original.to_markdown()
        restored = HandoffDocument.from_markdown(markdown)

        assert restored.completed == original.completed
        assert restored.in_progress == original.in_progress
        assert restored.blocked == original.blocked
        assert restored.next_actions == original.next_actions
        assert restored.session_id == original.session_id
        assert restored.timestamp == original.timestamp

    def test_empty_sections_round_trip(self) -> None:
        original = HandoffDocument(
            completed=["Done"],
            session_id="s1",
            timestamp="2025-01-01T00:00:00Z",
        )
        markdown = original.to_markdown()
        restored = HandoffDocument.from_markdown(markdown)
        assert restored.completed == ["Done"]
        assert restored.in_progress == []
        assert restored.blocked == []

    def test_to_markdown_format(self) -> None:
        doc = HandoffDocument(
            completed=["Task A"],
            session_id="s1",
            timestamp="2025-01-01",
        )
        md = doc.to_markdown()
        assert "# Handoff" in md
        assert "## Completed" in md
        assert "- Task A" in md
        assert "## In Progress" in md
