"""Pipeline tools — initialization and session management."""

from __future__ import annotations

from pathlib import Path

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp._app import mcp
from ai_architect_mcp._observability.instrumentation import observe_tool_call
from ai_architect_mcp._tools._composition import reset_context, reset_root


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_init_pipeline(
    target_repo_path: str,
    data_dir: str = ".pipeline",
    github_repo: str = "",
) -> dict[str, str]:
    """Initialize pipeline for a target repository.

    Call once at pipeline start to set the target repo and data directory.
    Re-initializes the shared composition root and stage context.

    Args:
        target_repo_path: Absolute path to the target git repository.
        data_dir: Pipeline data directory relative to target repo.
        github_repo: GitHub repository in owner/repo format.

    Returns:
        Confirmation with resolved paths.
    """
    repo = Path(target_repo_path).resolve()
    git_dir = repo / ".git"
    if not git_dir.exists():
        msg = (
            f"No .git directory found at {repo} — "
            f"target_repo_path must be a git repository"
        )
        return {"status": "error", "message": msg}

    data_path = repo / data_dir
    new_root = CompositionRoot(
        project_root=repo,
        repo_path=str(repo),
        github_repo=github_repo or None,
        data_dir=data_path,
    )
    reset_root(new_root)
    reset_context(persist_dir=data_path / "artifacts")

    return {
        "status": "initialized",
        "target_repo": str(repo),
        "data_dir": str(data_path),
        "github_repo": github_repo,
    }
