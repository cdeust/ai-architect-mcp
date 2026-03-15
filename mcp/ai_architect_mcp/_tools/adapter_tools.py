"""Adapter tools — git, GitHub, filesystem operations via ports.

Xcode tools are in xcode_tools.py (split for the 300-line limit).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect_mcp._adapters.composition_root import CompositionRoot
from ai_architect_mcp._app import mcp

_root: CompositionRoot | None = None


def _get_root() -> CompositionRoot:
    """Get or create the composition root."""
    global _root
    if _root is None:
        _root = CompositionRoot()
    return _root


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_git_branch(
    branch_name: str,
    base: str = "main",
) -> dict[str, str]:
    """Create a new git branch.

    Args:
        branch_name: Name for the new branch.
        base: Base branch.

    Returns:
        Dict with branch reference.
    """
    git = _get_root().create_git()
    ref = await git.create_branch(branch_name, base)
    return {"branch": ref}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_git_commit(
    message: str,
    files: list[str],
) -> dict[str, str]:
    """Create a git commit.

    Args:
        message: Commit message.
        files: Files to stage and commit.

    Returns:
        Dict with commit SHA.
    """
    git = _get_root().create_git()
    sha = await git.commit(message, files)
    return {"sha": sha}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def ai_architect_git_push(
    branch: str,
    force: bool = False,
) -> dict[str, str]:
    """Push a branch to remote.

    Args:
        branch: Branch to push.
        force: Force push flag.

    Returns:
        Confirmation dict.
    """
    git = _get_root().create_git()
    await git.push(branch, force=force)
    return {"status": "pushed", "branch": branch}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_git_diff(
    base: str,
    head: str,
) -> dict[str, str]:
    """Get diff between two refs.

    Args:
        base: Base ref.
        head: Head ref.

    Returns:
        Dict with diff content.
    """
    git = _get_root().create_git()
    diff = await git.diff(base, head)
    return {"diff": diff}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def ai_architect_github_create_pr(
    title: str,
    body: str,
    head: str,
    base: str = "main",
) -> dict[str, Any]:
    """Create a GitHub pull request.

    Args:
        title: PR title.
        body: PR description.
        head: Source branch.
        base: Target branch.

    Returns:
        PR metadata dict.
    """
    github = _get_root().create_github()
    return await github.create_pull_request(title, body, head, base)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_fs_read(
    path: str,
) -> dict[str, str]:
    """Read a file's contents.

    Args:
        path: Relative path to the file.

    Returns:
        Dict with file content.
    """
    fs = _get_root().create_filesystem()
    content = await fs.read(Path(path))
    return {"path": path, "content": content}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def ai_architect_fs_write(
    path: str,
    content: str,
) -> dict[str, str]:
    """Write content to a file.

    Args:
        path: Relative path to write.
        content: File content.

    Returns:
        Confirmation dict.
    """
    fs = _get_root().create_filesystem()
    await fs.write(Path(path), content)
    return {"status": "written", "path": path}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def ai_architect_fs_list(
    path: str = ".",
    pattern: str = "*",
) -> dict[str, Any]:
    """List files in a directory.

    Args:
        path: Directory path.
        pattern: Glob pattern.

    Returns:
        Dict with file list.
    """
    fs = _get_root().create_filesystem()
    files = await fs.list_directory(Path(path), pattern)
    return {"path": path, "pattern": pattern, "files": [str(f) for f in files]}
