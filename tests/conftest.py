"""Shared test fixtures for the AI Architect test suite.

Provides mock clients, sample data objects, and in-memory stores
used across multiple test modules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from ai_architect_mcp._context.artifact_store import ArtifactStore
from ai_architect_mcp._context.stage_context import StageContext
from ai_architect_mcp._models.finding import Finding, Severity, SourceCategory
from ai_architect_mcp._models.verification import (
    ClaimSource,
    ClaimType,
    VerificationClaim,
)


# ── Stub LLM Client ─────────────────────────────────────────────────────────

class _StubContentBlock:
    """Mimics anthropic SDK ContentBlock for tests."""

    __slots__ = ("text", "type")

    def __init__(self, text: str) -> None:
        self.text = text
        self.type = "text"


class _StubResponse:
    """Mimics anthropic SDK Message response for tests."""

    __slots__ = ("content",)

    def __init__(self, text: str) -> None:
        self.content = [_StubContentBlock(text)]


class _StubMessages:
    """Test double for client.messages that returns deterministic responses."""

    async def create(
        self,
        *,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str = "",
        messages: list[dict] | None = None,
    ) -> _StubResponse:
        """Return a deterministic response based on the system prompt."""
        system_lower = system.lower()

        # Confidence/rating evaluation → return a score
        if any(kw in system_lower for kw in ("rate", "scale of 0.0 to 1.0", "score")):
            return _StubResponse("0.78")

        # NLI classification
        if "classification" in system_lower and "entailment" in system_lower:
            return _StubResponse("ENTAILMENT")

        # Verification questions
        if "verification questions" in system_lower:
            return _StubResponse(
                "1. Does the context support the claim?\n"
                "2. Is there contradicting evidence?\n"
                "3. Is the claim internally consistent?\n"
                "4. Does the claim align with known facts?\n"
                "5. Are there edge cases that invalidate it?"
            )

        # Default: echo the user content with expansion
        user_text = ""
        if messages:
            for msg in messages:
                if msg.get("role") == "user":
                    user_text = msg.get("content", "")
                    break

        return _StubResponse(
            f"Enhanced analysis: {user_text[:200]}"
        )


class StubLLMClient:
    """Deterministic LLM client for tests — no network calls."""

    def __init__(self) -> None:
        self.messages = _StubMessages()


@pytest.fixture
def stub_llm_client() -> StubLLMClient:
    """Create a stub LLM client for algorithm tests."""
    return StubLLMClient()


@pytest.fixture
def sample_finding() -> Finding:
    """Create a sample finding for testing."""
    return Finding(
        finding_id="FIND-TEST-001",
        title="Test Finding for Unit Tests",
        description="A finding created for testing pipeline flow",
        source_category=SourceCategory.INTERNAL,
        relevance_score=0.85,
        severity=Severity.HIGH,
        created_at=datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        metadata={"test": "true"},
    )


@pytest.fixture
def sample_claim() -> VerificationClaim:
    """Create a sample verification claim for testing."""
    return VerificationClaim(
        claim_id=uuid4(),
        content="The system implements secure authentication",
        claim_type=ClaimType.ATOMIC_FACT,
        source=ClaimSource.GENERATION,
        priority=75,
    )


@pytest.fixture
def sample_prd_artifact() -> dict[str, object]:
    """Create a sample PRD artifact for HOR rule testing."""
    return {
        "title": "Authentication System PRD",
        "content": (
            "## Overview\n"
            "Authentication system using OAuth 2.0.\n\n"
            "## Requirements\n"
            "FR-001: User login\n"
            "FR-002: Token refresh\n\n"
            "## User Stories\n"
            "STORY-001: As a user, I want to log in.\n\n"
            "## Technical\n"
            "Uses port/adapter pattern with protocol interfaces.\n\n"
            "## Acceptance\n"
            "AC-001: Login returns JWT\n"
            "AC-002: Token expires in 1 hour\n\n"
            "## Roadmap\n"
            "Sprint 1: Basic auth\n\n"
            "## Testing\n"
            "Integration tests with coverage threshold of 80%.\n"
            "Edge cases: empty credentials, expired tokens.\n"
            "Test isolation with fixtures and setup/teardown.\n"
        ),
        "sections": [
            {"name": "Overview"},
            {"name": "Requirements"},
            {"name": "User Stories"},
            {"name": "Technical"},
            {"name": "Acceptance"},
            {"name": "Roadmap"},
            {"name": "Testing"},
        ],
        "requirements": [
            {"id": "FR-001", "source": "User Request"},
            {"id": "FR-002", "source": "Clarification"},
        ],
    }


@pytest.fixture
def in_memory_store() -> ArtifactStore:
    """Create an in-memory artifact store."""
    return ArtifactStore()


@pytest.fixture
def stage_context(in_memory_store: ArtifactStore) -> StageContext:
    """Create a stage context with in-memory backing."""
    return StageContext(store=in_memory_store)
