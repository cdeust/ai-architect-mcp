"""Composition root — factory wiring all adapters to port interfaces.

The ONE place where concrete adapter types are instantiated.
All other code depends only on port interfaces, never on concrete adapters.

Environment variables:
- AI_ARCHITECT_MCPBRIDGE_PATH: xcrun path for mcpbridge (default: xcrun)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from ai_architect_mcp._adapters.filesystem_adapter import FileSystemAdapter
from ai_architect_mcp._adapters.git_adapter import GitAdapter
from ai_architect_mcp._adapters.github_adapter import GitHubAdapter
from ai_architect_mcp._adapters.local_audit import LocalAudit
from ai_architect_mcp._adapters.local_experience import LocalExperience
from ai_architect_mcp._adapters.local_pipeline_state import LocalPipelineState
from ai_architect_mcp._adapters.memory_ports import (
    AuditPort,
    ExperiencePort,
    PipelineStatePort,
)
from ai_architect_mcp._adapters.ports import (
    FileSystemPort,
    GitHubOperationsPort,
    GitOperationsPort,
    StageContextPort,
    XcodeOperationsPort,
)
from ai_architect_mcp._adapters.xcode_adapter import XcodeAdapter
from ai_architect_mcp._context.stage_context import StageContext
from ai_architect_mcp._observability.composite_adapter import (
    CompositeObservabilityAdapter,
)
from ai_architect_mcp._observability.file_adapter import FileObservabilityAdapter
from ai_architect_mcp._observability.observability_port import ObservabilityPort
from ai_architect_mcp._observability.sse_adapter import SSEObservabilityAdapter

logger = logging.getLogger(__name__)

ENV_MCPBRIDGE_PATH: str = "AI_ARCHITECT_MCPBRIDGE_PATH"
ENV_ANTHROPIC_API_KEY: str = "ANTHROPIC_API_KEY"
ENV_SESSION_TOKEN: str = "CLAUDE_CODE_SESSION_ACCESS_TOKEN"


# ── Claude CLI Client ────────────────────────────────────────────────────────

class _ContentBlock:
    """Mimics anthropic SDK ContentBlock."""

    __slots__ = ("text", "type")

    def __init__(self, text: str) -> None:
        self.text = text
        self.type = "text"


class _CLIResponse:
    """Mimics anthropic SDK Message response."""

    __slots__ = ("content",)

    def __init__(self, text: str) -> None:
        self.content = [_ContentBlock(text)]


class _CLIMessages:
    """Mimics client.messages with a create() that calls claude CLI."""

    def __init__(self, claude_path: str) -> None:
        self._claude = claude_path

    async def create(
        self,
        *,
        model: str = "sonnet",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str = "",
        messages: list[dict] | None = None,
    ) -> _CLIResponse:
        """Call claude CLI in print mode and return the response."""
        import asyncio

        user_content = ""
        if messages:
            for msg in messages:
                if msg.get("role") == "user":
                    user_content = msg.get("content", "")
                    break

        if not user_content:
            return _CLIResponse("")

        # Map full model IDs to CLI aliases
        model_alias = model
        if "sonnet" in model:
            model_alias = "sonnet"
        elif "opus" in model:
            model_alias = "opus"
        elif "haiku" in model:
            model_alias = "haiku"

        args = [
            self._claude,
            "-p", user_content,
            "--output-format", "json",
            "--model", model_alias,
            "--max-turns", "1",
            "--no-session-persistence",
        ]
        if system:
            args.extend(["--system-prompt", system])

        # Clean env: remove Claude Code session markers so CLI runs standalone
        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in (
                "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT",
                "CLAUDE_CODE_SESSION_ACCESS_TOKEN",
            )
        }

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=clean_env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=180,
        )

        text = stdout.decode("utf-8", errors="replace").strip()

        # --output-format json returns {"type":"result","result":"..."}
        if text:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    text = data.get("result", "") or data.get("content", "") or text
            except (json.JSONDecodeError, ValueError):
                pass

        return _CLIResponse(text)


class ClaudeCLIClient:
    """LLM client backed by the claude CLI — uses subscription auth via Keychain."""

    def __init__(self, claude_path: str) -> None:
        self.messages = _CLIMessages(claude_path)


def _find_claude_cli() -> str | None:
    """Locate the claude CLI binary."""
    candidates = [
        shutil.which("claude"),
        os.path.expanduser("~/.local/bin/claude"),
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


class CompositionRoot:
    """Factory for creating adapter instances.

    Wires concrete adapters to their port interfaces. This is the
    only module that imports concrete adapter classes.

    Mcpbridge is used for Xcode operations when available;
    otherwise falls back to xcodebuild CLI.

    Args:
        project_root: Root directory for the project.
        repo_path: Path to the git repository.
        github_repo: GitHub repository in owner/repo format.
        data_dir: Pipeline data directory for state and artifacts.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        repo_path: str = ".",
        github_repo: str | None = None,
        data_dir: Path | None = None,
    ) -> None:
        """Initialize the composition root.

        Args:
            project_root: Root directory for filesystem operations.
            repo_path: Path to the git repository.
            github_repo: GitHub repository identifier.
            data_dir: Pipeline data directory. Defaults to project_root/.pipeline.
        """
        self._project_root = project_root or Path.cwd()
        self._repo_path = repo_path
        self._github_repo = github_repo
        self._data_dir = data_dir or (self._project_root / ".pipeline")
        self._mcpbridge_path = os.environ.get(ENV_MCPBRIDGE_PATH, "xcrun")
        self._llm_client: object | None = None

    def _mcpbridge_available(self) -> bool:
        """Check if xcrun mcpbridge is available on this system.

        Returns:
            True if xcrun is found and assumed to support mcpbridge.
        """
        return shutil.which(self._mcpbridge_path) is not None

    def create_git(self) -> GitOperationsPort:
        """Create a git operations adapter.

        Returns:
            GitOperationsPort implementation.
        """
        return GitAdapter(repo_path=self._repo_path)

    def create_github(self) -> GitHubOperationsPort:
        """Create a GitHub operations adapter.

        Returns:
            GitHubOperationsPort implementation.
        """
        return GitHubAdapter(repo=self._github_repo)

    def create_xcode(self) -> XcodeOperationsPort:
        """Create an Xcode operations adapter.

        Uses mcpbridge when available, falls back to xcodebuild CLI.

        Returns:
            XcodeOperationsPort implementation.
        """
        if self._mcpbridge_available():
            from ai_architect_mcp._adapters.xcode_mcpbridge_adapter import (
                XcodeMCPBridgeAdapter,
            )
            logger.info("Using XcodeMCPBridgeAdapter (mcpbridge)")
            return XcodeMCPBridgeAdapter(xcrun_path=self._mcpbridge_path)

        logger.info(
            "mcpbridge not available, falling back to XcodeAdapter (xcodebuild CLI)"
        )
        return XcodeAdapter(project_path=self._repo_path)

    def create_filesystem(self) -> FileSystemPort:
        """Create a filesystem adapter.

        Returns:
            FileSystemPort implementation.
        """
        return FileSystemAdapter(project_root=self._project_root)

    def create_pipeline_state(self) -> PipelineStatePort:
        """Create a pipeline state persistence adapter.

        Returns:
            PipelineStatePort implementation.
        """
        return LocalPipelineState(data_dir=self._data_dir)

    def create_experience(self) -> ExperiencePort:
        """Create an experience pattern storage adapter.

        Returns:
            ExperiencePort implementation.
        """
        return LocalExperience(data_dir=self._data_dir)

    def create_audit(self) -> AuditPort:
        """Create an audit event logging adapter.

        Returns:
            AuditPort implementation.
        """
        return LocalAudit(data_dir=self._data_dir)

    @staticmethod
    def _read_claude_oauth_token() -> str | None:
        """Read OAuth access token from Claude Code credentials.

        Looks for ~/.claude/.credentials.json → claudeAiOauth.accessToken.

        Returns:
            OAuth access token string or None.
        """
        creds_path = Path.home() / ".claude" / ".credentials.json"
        if not creds_path.exists():
            return None
        try:
            data = json.loads(creds_path.read_text())
            token = data.get("claudeAiOauth", {}).get("accessToken")
            if token:
                logger.debug("Found Claude OAuth token in credentials file")
            return token
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed to read Claude credentials: %s", exc)
            return None

    def create_llm_client(self) -> object | None:
        """Create or return cached LLM client.

        Used for non-MCP contexts (GitHub Actions, CLI scripts).
        MCP tools use ``SamplingClient(ctx)`` instead — see
        ``_adapters/sampling_client.py``.

        Auth priority:
        1. ANTHROPIC_API_KEY env var → AsyncAnthropic SDK.
        2. Claude CLI (standalone, not inside Claude Code).

        Returns:
            AsyncAnthropic instance, ClaudeCLIClient, or None.
        """
        if self._llm_client is not None:
            return self._llm_client

        # 1. Direct SDK with API key
        api_key = os.environ.get(ENV_ANTHROPIC_API_KEY)
        if api_key:
            try:
                from anthropic import AsyncAnthropic
                self._llm_client = AsyncAnthropic(api_key=api_key)
                logger.info("LLM client created (AsyncAnthropic via API key)")
                return self._llm_client
            except ImportError:
                pass

        # 2. Claude CLI — for standalone usage outside Claude Code
        claude_path = _find_claude_cli()
        if claude_path:
            self._llm_client = ClaudeCLIClient(claude_path)
            logger.info("LLM client created (Claude CLI at %s)", claude_path)
            return self._llm_client

        raise RuntimeError(
            "No LLM client available. "
            "Set ANTHROPIC_API_KEY or install the Claude CLI. "
            "Note: MCP tools should use SamplingClient(ctx) instead."
        )

    def create_context(self) -> StageContextPort:
        """Create a stage context adapter.

        Returns:
            StageContextPort implementation.
        """
        return StageContext()

    def create_observability(
        self, enable_sse: bool = True
    ) -> ObservabilityPort:
        """Create a composite observability adapter.

        Combines file-based JSONL persistence with optional SSE streaming.
        The SSE adapter must be started separately via its start() method.

        Args:
            enable_sse: Whether to include the SSE adapter.

        Returns:
            ObservabilityPort implementation multiplexing all backends.
        """
        trace_dir = self._data_dir
        file_adapter = FileObservabilityAdapter(data_dir=trace_dir)

        adapters: list[ObservabilityPort] = [file_adapter]
        if enable_sse:
            sse_adapter = SSEObservabilityAdapter()
            adapters.append(sse_adapter)
            logger.info("Observability: file + SSE adapters created")
        else:
            logger.info("Observability: file adapter only")

        return CompositeObservabilityAdapter(adapters=adapters)
