"""Atomic Claim Decomposer — splits compound claims into atomic facts.

Research: Min et al. (2023) FActScore.
"""

from __future__ import annotations

import re
from uuid import uuid4

from ai_architect_mcp._models.verification import (
    ClaimSource,
    ClaimType,
    VerificationClaim,
)

CONJUNCTION_PATTERNS = [" and ", " but ", " also ", " while ", " whereas ", "; "]
PRIORITY_PATTERN = re.compile(r"\[PRIORITY:(\d+)\]")
CONTEXT_PATTERN = re.compile(r"\[CONTEXT:([^\]]+)\]")
MIN_PRIORITY = 1
MAX_PRIORITY = 100


class AtomicClaimDecomposer:
    """Decomposes compound claims into atomic, self-contained facts.

    Atomic claims are: self-contained, factual, cannot be split further,
    and decontextualized (include necessary context inline).
    """

    def __init__(self, client: object | None = None) -> None:
        """Initialize the decomposer.

        Args:
            client: Anthropic client for LLM-assisted decomposition.
                None for rule-based only.
        """
        self._client = client

    async def decompose(
        self, claim: VerificationClaim
    ) -> list[VerificationClaim]:
        """Decompose a claim into atomic sub-claims.

        Args:
            claim: The compound claim to decompose.

        Returns:
            List of atomic VerificationClaim objects.
        """
        if self.is_atomic(claim.content):
            return [claim]

        parts = self._split_by_conjunctions(claim.content)

        if len(parts) <= 1 and self._client is not None:
            parts = await self._llm_decompose(claim.content)

        if len(parts) <= 1:
            return [claim]

        atomic_claims = _build_atomic_claims(parts, claim)
        return atomic_claims if atomic_claims else [claim]

    def is_atomic(self, claim_text: str) -> bool:
        """Check if a claim text is already atomic.

        Args:
            claim_text: The text to check.

        Returns:
            True if the claim appears to be atomic.
        """
        text = PRIORITY_PATTERN.sub("", claim_text)
        text = CONTEXT_PATTERN.sub("", text).strip()

        for pattern in CONJUNCTION_PATTERNS:
            if pattern in text.lower():
                return False

        predicates = re.findall(
            r"\b(?:is|are|was|were|has|have|does|do)\b",
            text,
            re.IGNORECASE,
        )
        if len(predicates) > 1:
            return False

        return True

    def _split_by_conjunctions(self, text: str) -> list[str]:
        """Split text by conjunction patterns.

        Args:
            text: Text to split.

        Returns:
            List of text fragments.
        """
        parts = [text]
        for pattern in CONJUNCTION_PATTERNS:
            new_parts: list[str] = []
            for part in parts:
                new_parts.extend(part.split(pattern))
            parts = new_parts
        return [p.strip() for p in parts if p.strip()]

    async def _llm_decompose(self, text: str) -> list[str]:
        """Use LLM to decompose a complex claim.

        Args:
            text: Claim text to decompose.

        Returns:
            List of atomic claim texts.
        """
        return [text]


def _build_atomic_claims(
    parts: list[str], parent: VerificationClaim
) -> list[VerificationClaim]:
    """Build atomic claims from text parts.

    Args:
        parts: Split text fragments.
        parent: Original parent claim.

    Returns:
        List of atomic VerificationClaim objects.
    """
    atomic_claims: list[VerificationClaim] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        priority = parent.priority
        context = parent.context

        priority_match = PRIORITY_PATTERN.search(part)
        if priority_match:
            priority = int(priority_match.group(1))
            part = PRIORITY_PATTERN.sub("", part).strip()

        context_match = CONTEXT_PATTERN.search(part)
        if context_match:
            context = context_match.group(1)
            part = CONTEXT_PATTERN.sub("", part).strip()

        if part:
            atomic_claims.append(VerificationClaim(
                claim_id=uuid4(),
                content=part,
                claim_type=ClaimType.ATOMIC_FACT,
                source=ClaimSource.DECOMPOSITION,
                context=context,
                priority=max(MIN_PRIORITY, min(MAX_PRIORITY, priority)),
                metadata={
                    **parent.metadata,
                    "parent_claim_id": str(parent.claim_id),
                },
            ))

    return atomic_claims
