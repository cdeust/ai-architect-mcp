"""Prompting tools — enhancement, strategy selection, confidence fusion."""

from __future__ import annotations

from typing import Any

from ai_architect_mcp._models.prompting import ConfidenceEstimate, EnhancementSource
from ai_architect_mcp._prompting.algorithms.adaptive_expansion import AdaptiveExpansion
from ai_architect_mcp._prompting.algorithms.trm_refinement import TRMRefinement
from ai_architect_mcp._prompting.confidence_fusion import ConfidenceFusionEngine
from ai_architect_mcp._prompting.strategies.registry import StrategyRegistry
from ai_architect_mcp.server import mcp


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
async def ai_architect_enhance_prompt(
    prompt: str,
    context: str = "",
    max_iterations: int = 5,
) -> dict[str, Any]:
    """Enhance a prompt using TRM recursive refinement.

    Args:
        prompt: The prompt to enhance.
        context: Supporting context.
        max_iterations: Maximum refinement iterations.

    Returns:
        EnhancedPrompt as a dictionary.
    """
    trm = TRMRefinement()
    result = await trm.refine(prompt, context, max_iterations=max_iterations)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_select_strategy(
    project_type: str,
    complexity: str,
    characteristics: list[str],
) -> dict[str, Any]:
    """Select the best thinking strategy for a problem.

    Args:
        project_type: Type of project (api, mobile, data, etc).
        complexity: Complexity level (low, medium, high).
        characteristics: Problem characteristics to match.

    Returns:
        StrategySelection as a dictionary.
    """
    registry = StrategyRegistry()
    result = registry.select(project_type, complexity, characteristics)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
async def ai_architect_fuse_confidence(
    estimates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fuse multiple confidence estimates into a single result.

    Args:
        estimates: List of ConfidenceEstimate dictionaries.

    Returns:
        FusedConfidence as a dictionary.
    """
    parsed = [ConfidenceEstimate.model_validate(e) for e in estimates]
    engine = ConfidenceFusionEngine()
    result = engine.fuse(parsed)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
async def ai_architect_expand_thought(
    prompt: str,
    context: str = "",
    max_depth: int = 5,
) -> dict[str, Any]:
    """Expand a prompt using adaptive Tree/Graph of Thoughts.

    Args:
        prompt: The prompt to expand.
        context: Supporting context.
        max_depth: Maximum exploration depth.

    Returns:
        EnhancedPrompt as a dictionary.
    """
    expander = AdaptiveExpansion()
    result = await expander.expand(prompt, context, max_depth=max_depth)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
async def ai_architect_refine_prompt(
    prompt: str,
    context: str = "",
    max_iterations: int = 5,
) -> dict[str, Any]:
    """Refine a prompt using TRM recursive refinement.

    Args:
        prompt: The prompt to refine.
        context: Supporting context.
        max_iterations: Maximum iterations.

    Returns:
        EnhancedPrompt as a dictionary.
    """
    trm = TRMRefinement()
    result = await trm.refine(prompt, context, max_iterations=max_iterations)
    return result.model_dump(mode="json")
