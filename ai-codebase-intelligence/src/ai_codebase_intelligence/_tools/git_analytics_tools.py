"""Git analytics MCP tools — ownership, bus factor, churn, co-change, dead code.

Every tool traces to a peer-reviewed paper. No invented algorithms.
"""

from __future__ import annotations

import json

from .._app import mcp
from ..mcp.local.local_backend import LocalBackend

_backend: LocalBackend | None = None


def _get_backend() -> LocalBackend:
    global _backend
    if _backend is None:
        _backend = LocalBackend()
    return _backend


@mcp.tool(
    name="ai_architect_codebase_ownership",
    description=(
        "Analyze code ownership per Bird et al. 2011 (ESEC/FSE). "
        "Shows ownership ratio, minor contributors, and top contributor "
        "per file. Low ownership correlates with higher defect density."
    ),
)
async def tool_ownership(
    target: str = "all",
    repo: str = "",
) -> str:
    """Query code ownership metrics.

    Args:
        target: File path to analyze, or 'all' for entire repo.
        repo: Repository name. Omit if only one indexed.
    """
    backend = _get_backend()
    result = await backend.call_tool("ownership", {
        "target": target, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Use bus_factor() to assess knowledge concentration risk."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_bus_factor",
    description=(
        "Calculate bus factor per Avelino et al. 2016 (ICPC). "
        "Iteratively removes top contributor until >50%% of files are "
        "orphaned. Bus factor of 1 = CRITICAL risk."
    ),
)
async def tool_bus_factor(
    repo: str = "",
    threshold: float = 0.5,
) -> str:
    """Calculate repository bus factor.

    Args:
        repo: Repository name. Omit if only one indexed.
        threshold: Orphan threshold (default 0.5 per Avelino et al.).
    """
    backend = _get_backend()
    result = await backend.call_tool("bus_factor", {
        "threshold": threshold, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Use ownership() on high-risk files to identify knowledge silos."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_churn",
    description=(
        "Compute code churn metrics per Nagappan & Ball 2005 (ICSE). "
        "Reports commit count, lines added/deleted, and relative churn "
        "per file. High relative churn predicts higher defect density."
    ),
)
async def tool_churn(
    target: str = "all",
    repo: str = "",
    max_commits: int = 500,
) -> str:
    """Compute churn metrics for files.

    Args:
        target: File path or 'all' for entire repo.
        repo: Repository name. Omit if only one indexed.
        max_commits: Maximum commits to analyze per file.
    """
    backend = _get_backend()
    result = await backend.call_tool("churn", {
        "target": target, "max_commits": max_commits, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Cross-reference with cochange() to find hidden coupling."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_cochange",
    description=(
        "Detect co-change pairs per Gall et al. 1998 (ICSM) and "
        "Zimmermann et al. 2005 (IEEE TSE). Files that change together "
        "without import links indicate hidden structural coupling."
    ),
)
async def tool_cochange(
    target: str = "",
    repo: str = "",
) -> str:
    """Query co-change partners for a file or all pairs.

    Args:
        target: File path for specific file, or empty for all pairs.
        repo: Repository name. Omit if only one indexed.
    """
    backend = _get_backend()
    result = await backend.call_tool("cochange", {
        "target": target, "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Use impact() on coupled files to assess blast radius."
    return json.dumps(result, indent=2) + hint


@mcp.tool(
    name="ai_architect_codebase_dead_code",
    description=(
        "Detect unreachable code via conservative CHA-based reachability "
        "per Grove et al. 1997 (OOPSLA) and Tip et al. 1999 (OOPSLA). "
        "BFS from entry points; unreachable nodes are dead code candidates "
        "with confidence levels (HIGH/MEDIUM/LOW)."
    ),
)
async def tool_dead_code(
    repo: str = "",
    min_confidence: float = 0.6,
    include_low_confidence: bool = False,
) -> str:
    """Detect dead code candidates.

    Args:
        repo: Repository name. Omit if only one indexed.
        min_confidence: Minimum confidence threshold (default 0.6).
        include_low_confidence: Include LOW confidence candidates.
    """
    backend = _get_backend()
    result = await backend.call_tool("dead_code", {
        "min_confidence": min_confidence,
        "include_low_confidence": include_low_confidence,
        "repo": repo or None,
    })
    hint = "\n\n---\n**Next:** Use context() on candidates to verify they're truly unused."
    return json.dumps(result, indent=2) + hint
