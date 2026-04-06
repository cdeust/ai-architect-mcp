"""Backend: dead code detection — Grove et al. 1997 + Tip et al. 1999."""

from __future__ import annotations

from typing import Any

from ...core.analysis.dead_code import detect_dead_code
from ...core.storage.repo_store import get_index


async def dead_code_tool(
    backend: Any,
    repo: dict[str, Any],
    params: dict[str, Any],
) -> Any:
    """Detect unreachable code candidates.

    Args:
        backend: LocalBackend instance.
        repo: Resolved repo dict.
        params: Tool params with optional min_confidence.

    Returns:
        Dead code candidates with confidence levels.
    """
    await backend.ensure_initialized(repo["id"])
    index = get_index(repo["id"])

    min_confidence = params.get("min_confidence", 0.6)
    include_low = params.get("include_low_confidence", False)

    return detect_dead_code(
        index,
        min_confidence=min_confidence,
        include_low_confidence=include_low,
    )
