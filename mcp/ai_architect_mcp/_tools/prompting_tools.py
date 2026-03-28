"""Prompting tools — enhancement, strategy selection, confidence fusion."""

from __future__ import annotations

from typing import Any

from fastmcp import Context

from ai_architect_mcp._adapters.sampling_client import SamplingClient
from ai_architect_mcp._models.prompting import ConfidenceEstimate, EnhancementSource
from ai_architect_mcp._prompting.algorithms.adaptive_expansion import AdaptiveExpansion
from ai_architect_mcp._prompting.algorithms.collaborative_inference import CollaborativeInference
from ai_architect_mcp._prompting.algorithms.metacognitive import MetacognitiveMonitor
from ai_architect_mcp._prompting.algorithms.thought_buffer import SignalAwareThoughtBuffer
from ai_architect_mcp._prompting.algorithms.trm_refinement import TRMRefinement
from ai_architect_mcp._prompting.confidence_fusion import ConfidenceFusionEngine
from ai_architect_mcp._prompting.strategies.registry import StrategyRegistry
from ai_architect_mcp._app import mcp
from ai_architect_mcp._config.loader import load_config
from ai_architect_mcp._observability.instrumentation import observe_tool_call


def _llm_model() -> str:
    """Get the configured LLM model ID."""
    return load_config().prompting.llm_model


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
@observe_tool_call
async def ai_architect_enhance_prompt(
    prompt: str,
    ctx: Context,
    context: str = "",
    max_iterations: int = 5,
) -> dict[str, Any]:
    """Enhance a prompt using TRM recursive refinement.

    Args:
        prompt: The prompt to enhance.
        ctx: FastMCP context (injected) — used for LLM sampling.
        context: Supporting context.
        max_iterations: Maximum refinement iterations.

    Returns:
        EnhancedPrompt as a dictionary.
    """
    trm = TRMRefinement(client=SamplingClient(ctx), model=_llm_model())
    result = await trm.refine(prompt, context, max_iterations=max_iterations)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
)
@observe_tool_call
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
@observe_tool_call
async def ai_architect_fuse_confidence(
    estimates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fuse multiple confidence estimates into a single result.

    Applies source-specific bias corrections, weighted averaging with
    disagreement penalty, and consensus bonus (agreement >0.8, fused >0.7).

    Args:
        estimates: List of ConfidenceEstimate dictionaries. Each requires:
            - source (str): Algorithm that produced this estimate — one of
              "thought_buffer", "adaptive_expansion", "collaborative_inference",
              "metacognitive", "trm_refinement".
            - value (float): Confidence value (0.0-1.0).
            - uncertainty (float): Uncertainty in the estimate (>= 0.0).
            - reasoning (str): Explanation of the confidence calculation.

    Returns:
        FusedConfidence as a dictionary with fields:
            point, lower, upper (all 0.0-1.0), contributing_estimates,
            fusion_method.
    """
    parsed = [ConfidenceEstimate.model_validate(e) for e in estimates]
    engine = ConfidenceFusionEngine()
    result = engine.fuse(parsed)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
@observe_tool_call
async def ai_architect_expand_thought(
    prompt: str,
    ctx: Context,
    context: str = "",
    max_depth: int = 5,
) -> dict[str, Any]:
    """Expand a prompt using adaptive Tree/Graph of Thoughts.

    Args:
        prompt: The prompt to expand.
        ctx: FastMCP context (injected) — used for LLM sampling.
        context: Supporting context.
        max_depth: Maximum exploration depth.

    Returns:
        EnhancedPrompt as a dictionary.
    """
    expander = AdaptiveExpansion(client=SamplingClient(ctx), model=_llm_model())
    result = await expander.expand(prompt, context, max_depth=max_depth)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
@observe_tool_call
async def ai_architect_metacognitive_monitor(
    prompt: str,
    response: str,
    ctx: Context,
    context: str = "",
    max_iterations: int = 5,
) -> dict[str, Any]:
    """Monitor and enhance reasoning with metacognitive interventions.

    Evaluates response quality iteratively, triggering reflection when
    stalled or strategy switching when quality degrades.

    Args:
        prompt: The original prompt/task.
        response: Initial response to monitor and improve.
        ctx: FastMCP context (injected) — used for LLM sampling.
        context: Supporting context.
        max_iterations: Maximum monitoring iterations.

    Returns:
        EnhancedPrompt as a dictionary with intervention history.
    """
    monitor = MetacognitiveMonitor(client=SamplingClient(ctx), model=_llm_model())
    result = await monitor.monitor(prompt, response, context, max_iterations=max_iterations)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
@observe_tool_call
async def ai_architect_thought_buffer(
    prompt: str,
    ctx: Context,
    context: str = "",
) -> dict[str, Any]:
    """Process a prompt using signal-aware thought buffer templates.

    Retrieves relevant thought templates by category matching,
    builds enhanced context, and learns new templates from
    high-confidence executions (>0.8 threshold).

    Args:
        prompt: The prompt to process.
        ctx: FastMCP context (injected) — used for LLM sampling.
        context: Supporting context.

    Returns:
        EnhancedPrompt as a dictionary with template metadata.
    """
    buffer = SignalAwareThoughtBuffer(client=SamplingClient(ctx), model=_llm_model())
    result = await buffer.process(prompt, context)
    return result.model_dump(mode="json")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
@observe_tool_call
async def ai_architect_collaborative_infer(
    prompt: str,
    ctx: Context,
    context: str = "",
    path_count: int = 3,
    max_steps: int = 5,
) -> dict[str, Any]:
    """Run collaborative inference across multiple reasoning paths.

    Spawns N independent reasoning paths with varied temperatures,
    advances each iteratively, and terminates when paths reach
    consensus (variance <0.02, mean confidence >0.7).

    Args:
        prompt: The prompt to reason about.
        ctx: FastMCP context (injected) — used for LLM sampling.
        context: Supporting context.
        path_count: Number of independent reasoning paths (default 3).
        max_steps: Maximum reasoning steps per path (default 5).

    Returns:
        EnhancedPrompt as a dictionary with consensus metadata.
    """
    ci = CollaborativeInference(client=SamplingClient(ctx), model=_llm_model())
    result = await ci.infer(prompt, context, path_count=path_count, max_steps=max_steps)
    return result.model_dump(mode="json")
