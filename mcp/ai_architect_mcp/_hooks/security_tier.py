"""Security tier hook — 10-tier command classification.

Runs at PRE_TOOL phase. Classifies commands into 10 security
tiers from T1 (safe reads) to T10 (destructive operations).
T1-T5 are allowed, T6-T7 require confirmation, T8-T10 are blocked.
"""

from __future__ import annotations

import logging
import re
from enum import IntEnum

from ai_architect_mcp._hooks.base import (
    Hook,
    HookContext,
    HookPhase,
    HookResult,
    HookStatus,
)

logger = logging.getLogger(__name__)


class SecurityTier(IntEnum):
    """10-tier security classification for commands."""

    T1_READ = 1
    T2_ENV_QUERY = 2
    T3_PACKAGE = 3
    T4_WRITE = 4
    T5_PUBLISH = 5
    T6_CONTAINER = 6
    T7_PERMISSION = 7
    T8_KILL = 8
    T9_SYSTEM_FILE = 9
    T10_DESTRUCTIVE = 10


class TierAction(str):
    """Action to take for a security tier."""

    ALLOW = "allow"
    ASK = "ask"
    BLOCK = "block"


TIER_ACTIONS: dict[SecurityTier, str] = {
    SecurityTier.T1_READ: TierAction.ALLOW,
    SecurityTier.T2_ENV_QUERY: TierAction.ALLOW,
    SecurityTier.T3_PACKAGE: TierAction.ALLOW,
    SecurityTier.T4_WRITE: TierAction.ALLOW,
    SecurityTier.T5_PUBLISH: TierAction.ALLOW,
    SecurityTier.T6_CONTAINER: TierAction.ASK,
    SecurityTier.T7_PERMISSION: TierAction.ASK,
    SecurityTier.T8_KILL: TierAction.BLOCK,
    SecurityTier.T9_SYSTEM_FILE: TierAction.BLOCK,
    SecurityTier.T10_DESTRUCTIVE: TierAction.BLOCK,
}

T10_PATTERNS = [
    re.compile(r"rm\s+-rf\s+/\s*$"),
    re.compile(r"rm\s+-rf\s+/\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bformat\s+[a-zA-Z]:", re.IGNORECASE),
    re.compile(r"dd\s+.*of=/dev/"),
]

T9_PATTERNS = [
    re.compile(r"(?:>|tee)\s+/etc/"),
    re.compile(r"(?:>|tee)\s+/usr/"),
    re.compile(r"(?:>|tee)\s+/sys/"),
    re.compile(r"mv\s+.*\s+/etc/"),
]

T8_PATTERNS = [
    re.compile(r"\bkill\b"),
    re.compile(r"\bpkill\b"),
    re.compile(r"\bkillall\b"),
]

T7_PATTERNS = [
    re.compile(r"\bchmod\b"),
    re.compile(r"\bchown\b"),
    re.compile(r"\bchgrp\b"),
]

T6_PATTERNS = [
    re.compile(r"\bdocker\s+(?:run|build|exec)\b"),
    re.compile(r"\bpodman\s+(?:run|build|exec)\b"),
]

T5_PATTERNS = [
    re.compile(r"\bgit\s+(?:commit|push|tag)\b"),
    re.compile(r"\bnpm\s+publish\b"),
    re.compile(r"\btwine\s+upload\b"),
]

T4_PATTERNS = [
    re.compile(r"\becho\s.*>"),
    re.compile(r"\btouch\b"),
    re.compile(r"\bmkdir\b"),
    re.compile(r"\bcp\b"),
]

T3_PATTERNS = [
    re.compile(r"\bpip\s+(?:list|show|freeze)\b"),
    re.compile(r"\bnpm\s+(?:ls|list)\b"),
]

T2_PATTERNS = [
    re.compile(r"\buname\b"),
    re.compile(r"\bwhich\b"),
    re.compile(r"\benv\b"),
    re.compile(r"\bprintenv\b"),
]

T1_PATTERNS = [
    re.compile(r"\bls\b"),
    re.compile(r"\bcat\b"),
    re.compile(r"\bhead\b"),
    re.compile(r"\btail\b"),
    re.compile(r"\bfind\b"),
    re.compile(r"\bgrep\b"),
    re.compile(r"\bwc\b"),
]

TIER_PATTERNS: list[tuple[SecurityTier, list[re.Pattern[str]]]] = [
    (SecurityTier.T10_DESTRUCTIVE, T10_PATTERNS),
    (SecurityTier.T9_SYSTEM_FILE, T9_PATTERNS),
    (SecurityTier.T8_KILL, T8_PATTERNS),
    (SecurityTier.T7_PERMISSION, T7_PATTERNS),
    (SecurityTier.T6_CONTAINER, T6_PATTERNS),
    (SecurityTier.T5_PUBLISH, T5_PATTERNS),
    (SecurityTier.T4_WRITE, T4_PATTERNS),
    (SecurityTier.T3_PACKAGE, T3_PATTERNS),
    (SecurityTier.T2_ENV_QUERY, T2_PATTERNS),
    (SecurityTier.T1_READ, T1_PATTERNS),
]


def classify_command(command: str) -> SecurityTier:
    """Classify a command into a security tier.

    Checks from highest tier (most dangerous) to lowest.

    Args:
        command: The shell command to classify.

    Returns:
        The highest matching SecurityTier.
    """
    for tier, patterns in TIER_PATTERNS:
        for pattern in patterns:
            if pattern.search(command):
                return tier
    return SecurityTier.T1_READ


class SecurityTierHook(Hook):
    """Pre-tool hook that classifies and gates commands by security tier.

    T1-T5: ALLOW (safe operations)
    T6-T7: ASK (require user confirmation — returned as metadata)
    T8-T10: BLOCK (dangerous operations)
    """

    @property
    def name(self) -> str:
        """Hook name."""
        return "security_tier"

    @property
    def phase(self) -> HookPhase:
        """Runs before each tool call."""
        return HookPhase.PRE_TOOL

    async def execute(self, context: HookContext) -> HookResult:
        """Classify command and enforce security tier.

        Args:
            context: Hook context with command to classify.

        Returns:
            PASS for T1-T5, PASS with ask metadata for T6-T7,
            BLOCK for T8-T10.
        """
        if not context.command:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message="No command to classify",
            )

        tier = classify_command(context.command)
        action = TIER_ACTIONS[tier]

        if action == TierAction.BLOCK:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.BLOCK,
                message=(
                    f"Command blocked (T{tier.value}): {context.command} — "
                    f"this operation is classified as dangerous"
                ),
                metadata={"tier": tier.value, "action": action},
            )

        if action == TierAction.ASK:
            return HookResult(
                hook_name=self.name,
                status=HookStatus.PASS,
                message=(
                    f"Command requires confirmation (T{tier.value}): "
                    f"{context.command}"
                ),
                metadata={
                    "tier": tier.value,
                    "action": action,
                    "requires_confirmation": True,
                },
            )

        return HookResult(
            hook_name=self.name,
            status=HookStatus.PASS,
            message=f"Command allowed (T{tier.value})",
            metadata={"tier": tier.value, "action": action},
        )
