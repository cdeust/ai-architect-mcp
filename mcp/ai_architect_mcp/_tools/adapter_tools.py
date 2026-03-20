"""Adapter tools — git, GitHub, filesystem operations via ports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect_mcp._app import mcp
from ai_architect_mcp._observability.instrumentation import observe_tool_call
from ai_architect_mcp._tools._composition import get_root


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
@observe_tool_call
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
    git = get_root().create_git()
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
@observe_tool_call
async def ai_architect_git_commit(
    message: str,
    files: list[str],
    worktree_path: str = "",
) -> dict[str, str]:
    """Create a git commit.

    Args:
        message: Commit message.
        files: Files to stage and commit.
        worktree_path: If set, commit inside this worktree instead of the main repo.

    Returns:
        Dict with commit SHA.
    """
    if worktree_path:
        from ai_architect_mcp._adapters.git_adapter import GitAdapter
        git = GitAdapter(repo_path=worktree_path)
    else:
        git = get_root().create_git()
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
@observe_tool_call
async def ai_architect_git_push(
    branch: str,
    force: bool = False,
    worktree_path: str = "",
) -> dict[str, str]:
    """Push a branch to remote.

    Args:
        branch: Branch to push.
        force: Force push flag.
        worktree_path: If set, push from this worktree instead of the main repo.

    Returns:
        Confirmation dict.
    """
    if worktree_path:
        from ai_architect_mcp._adapters.git_adapter import GitAdapter
        git = GitAdapter(repo_path=worktree_path)
    else:
        git = get_root().create_git()
    await git.push(branch, force=force)
    return {"status": "pushed", "branch": branch}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_git_worktree_add(
    branch_name: str,
    base: str = "main",
) -> dict[str, str]:
    """Create an isolated git worktree with a new branch.

    Each finding gets its own worktree so 1000 concurrent pipeline
    runs never collide.  Returns the worktree path — pass it to
    git_commit, git_push, and fs_write via their worktree_path param.

    Args:
        branch_name: Branch to create in the worktree.
        base: Base branch to fork from.

    Returns:
        Dict with worktree_path and branch.
    """
    git = get_root().create_git()
    path = await git.create_worktree(branch_name, base)
    return {"worktree_path": path, "branch": f"refs/heads/{branch_name}"}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_git_worktree_remove(
    worktree_path: str,
) -> dict[str, str]:
    """Remove a previously created worktree.

    Call after push + PR to clean up the temporary directory.

    Args:
        worktree_path: Path returned by ai_architect_git_worktree_add.

    Returns:
        Confirmation dict.
    """
    git = get_root().create_git()
    await git.remove_worktree(worktree_path)
    return {"status": "removed", "worktree_path": worktree_path}


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
@observe_tool_call
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
    git = get_root().create_git()
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
@observe_tool_call
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
    github = get_root().create_github()
    return await github.create_pull_request(title, body, head, base)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
@observe_tool_call
async def ai_architect_fs_read(
    path: str,
) -> dict[str, str]:
    """Read a file's contents.

    Args:
        path: Relative path to the file.

    Returns:
        Dict with file content.
    """
    fs = get_root().create_filesystem()
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
@observe_tool_call
async def ai_architect_fs_write(
    path: str,
    content: str,
    worktree_path: str = "",
) -> dict[str, str]:
    """Write content to a file.

    Args:
        path: Relative path to write.
        content: File content.
        worktree_path: If set, write inside this worktree instead of the main repo.

    Returns:
        Confirmation dict.
    """
    if worktree_path:
        from ai_architect_mcp._adapters.filesystem_adapter import FileSystemAdapter
        fs = FileSystemAdapter(project_root=Path(worktree_path))
    else:
        fs = get_root().create_filesystem()
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
@observe_tool_call
async def ai_architect_fs_list(
    path: str = ".",
    pattern: str = "*",
) -> dict[str, Any]:
    """List files in a directory.

    Args:
        path: Directory path.
        pattern: Glob pattern.
    """
    fs = get_root().create_filesystem()
    files = await fs.list_directory(Path(path), pattern)
    return {"path": path, "pattern": pattern, "files": [str(f) for f in files]}
