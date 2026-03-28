"""Sampling-based LLM client adapter.

Wraps FastMCP's ``ctx.sample()`` into the ``client.messages.create()``
interface that all verification and prompting algorithms expect.

When the MCP server is hosted inside Claude Code, sampling requests
flow over stdio to the client which fulfils them using its own
subscription OAuth — no API keys required on the server side.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from fastmcp import Context

logger = logging.getLogger(__name__)


# ── Response shims matching the Anthropic SDK shape ──────────────────────────


@dataclass(slots=True)
class _TextBlock:
    """Mimics ``anthropic.types.TextBlock``."""

    text: str
    type: str = "text"


@dataclass(slots=True)
class _SamplingResponse:
    """Mimics ``anthropic.types.Message`` — only the fields algorithms read."""

    content: list[_TextBlock] = field(default_factory=list)


# ── Messages adapter ────────────────────────────────────────────────────────


class _SamplingMessages:
    """Implements ``client.messages.create()`` via ``ctx.sample()``."""

    def __init__(self, ctx: Context) -> None:
        self._ctx = ctx

    async def create(
        self,
        *,
        model: str = "sonnet",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str = "",
        messages: list[dict] | None = None,
    ) -> _SamplingResponse:
        """Forward an LLM request to the MCP client via sampling.

        Args:
            model: Model hint (mapped to ``model_preferences``).
            max_tokens: Maximum tokens for the response.
            temperature: Sampling temperature.
            system: System prompt.
            messages: Conversation messages in Anthropic SDK format.

        Returns:
            Response object with ``content[0].text`` as algorithms expect.
        """
        from mcp.types import SamplingMessage, TextContent

        # Build SamplingMessage list from Anthropic-style messages
        sampling_messages: list[SamplingMessage] = []
        if messages:
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                sampling_messages.append(
                    SamplingMessage(
                        role=role,
                        content=TextContent(type="text", text=content),
                    )
                )

        if not sampling_messages:
            return _SamplingResponse(content=[_TextBlock(text="")])

        # Map model string to preference hints
        model_hints: list[str] = []
        if "opus" in model:
            model_hints = ["claude-opus-4-6", "claude-opus"]
        elif "haiku" in model:
            model_hints = ["claude-haiku-4-5", "claude-haiku"]
        else:
            model_hints = ["claude-sonnet-4-6", "claude-sonnet"]

        try:
            result = await self._ctx.sample(
                messages=sampling_messages,
                system_prompt=system or None,
                temperature=temperature,
                max_tokens=max_tokens,
                model_preferences=model_hints,
            )
        except (ValueError, RuntimeError, Exception) as exc:
            error_msg = str(exc).lower()
            if "does not support sampling" in error_msg:
                logger.warning(
                    "MCP client does not support sampling — returning empty response. "
                    "LLM-dependent algorithms will degrade to fallback behavior."
                )
                return _SamplingResponse(content=[_TextBlock(text="")])
            raise

        text = result.text or ""
        logger.debug(
            "Sampling response (%d chars, model hints=%s)",
            len(text),
            model_hints,
        )
        return _SamplingResponse(content=[_TextBlock(text=text)])


# ── Public client ────────────────────────────────────────────────────────────


class SamplingClient:
    """LLM client backed by MCP sampling — drop-in for ``AsyncAnthropic``.

    Algorithms call ``client.messages.create(...)`` which is routed
    through ``ctx.sample()`` to the MCP host (Claude Code).

    Args:
        ctx: The FastMCP tool execution Context.
    """

    def __init__(self, ctx: Context) -> None:
        self.messages = _SamplingMessages(ctx)
